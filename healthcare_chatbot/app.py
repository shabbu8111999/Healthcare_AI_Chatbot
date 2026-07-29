"""
FastAPI backend and minimal built in web page for the healthcare
chatbot. Replaces the previous Streamlit app. The same LangGraph
workflow powers this, guardrails, retrieval, generation, and the human
in the loop review step all work exactly the same, just exposed as
HTTP endpoints instead of a Streamlit script.
"""

import io
import os
import uuid
from contextlib import asynccontextmanager

import pypdf
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from pydantic import BaseModel

import chat_store
import export_utils
from graph import nodes as graph_nodes
from graph.state import GraphState
from graph.workflow import build_graph
from guardrails import DISCLAIMER

# anchored to this file's own folder, same reasoning as config.py, so
# static and templates resolve correctly no matter where the app is
# launched from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# holds the compiled graph once the server has started, shared by
# every request instead of being rebuilt each time
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # this runs once when the server starts, the current recommended
    # place for startup work, replaces the older on_event("startup")
    global graph
    graph = build_graph()
    # warm up the vector store here too, so the very first real chat
    # request is not the one paying for the embedding model load
    graph_nodes._get_vector_store()
    yield
    # nothing needs cleanup on shutdown for this project


app = FastAPI(title="Healthcare Assistant Chatbot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


def make_thread_config(thread_id: str) -> dict:
    # same shape every call to the graph uses, so every run shows up
    # consistently in the LangSmith dashboard
    return {
        "configurable": {"thread_id": thread_id},
        "run_name": "healthcare_chatbot_turn",
        "tags": ["healthcare_chatbot", "fastapi", "langgraph"],
        "metadata": {
            "Author": "Shabareesh Nair",
            "Model": "Claude Sonnet 5",
            "App": "Healthcare Chatbot",
        },
    }


class ChatRequest(BaseModel):
    thread_id: str | None = None
    message: str
    attachment_text: str | None = None


class ReviewRequest(BaseModel):
    thread_id: str
    decision: str


class RenameRequest(BaseModel):
    title: str


def serialize_message(message) -> dict:
    role = "user" if message.type == "human" else "assistant"
    return {"role": role, "content": message.content}


def get_state_payload(thread_id: str) -> dict:
    # one function builds the same response shape for /chat, /review,
    # and /history, so the page always gets a consistent picture
    thread_config = make_thread_config(thread_id)
    snapshot = graph.get_state(thread_config)
    history = snapshot.values.get("messages", []) if snapshot.values else []
    pending = snapshot.interrupts[0] if snapshot.interrupts else None

    payload = {
        "thread_id": thread_id,
        "history": [serialize_message(m) for m in history],
        "pending_review": None,
        "has_real_question": snapshot.values.get("has_real_question", False) if snapshot.values else False,
    }

    if pending:
        payload["pending_review"] = {
            "answer": pending.value["answer"],
            "sources": snapshot.values.get("retrieved_context", []),
        }

    return payload


@app.post("/chat")
def chat(request: ChatRequest):
    # new conversation gets a fresh thread id, existing one reuses it
    is_new_chat = request.thread_id is None
    thread_id = request.thread_id or str(uuid.uuid4())
    thread_config = make_thread_config(thread_id)

    state = GraphState(
        messages=[HumanMessage(content=request.message)],
        attached_document=request.attachment_text,
    )
    graph.invoke(state, config=thread_config)

    # record this chat in the sidebar list, either as a brand new
    # entry with a title from the first message, or just bump its
    # position since it was just used
    if is_new_chat:
        chat_store.create_session(thread_id, request.message)
    else:
        chat_store.touch_session(thread_id)

    return get_state_payload(thread_id)


@app.post("/review")
def review(request: ReviewRequest):
    # decision is "approve" or "reject", this resumes the graph right
    # where human_review_node paused it
    thread_config = make_thread_config(request.thread_id)
    graph.invoke(Command(resume=request.decision), config=thread_config)
    return get_state_payload(request.thread_id)


@app.get("/history/{thread_id}")
def history(thread_id: str):
    return get_state_payload(thread_id)


@app.get("/chats")
def list_chats():
    # everything the sidebar needs to render the chat list
    return chat_store.list_sessions()


@app.post("/chats/{thread_id}/rename")
def rename_chat(thread_id: str, request: RenameRequest):
    chat_store.rename_session(thread_id, request.title)
    return {"ok": True}


@app.delete("/chats/{thread_id}")
def delete_chat(thread_id: str):
    # this removes the chat from the sidebar list, the underlying
    # LangGraph checkpoint data for that thread is left as is
    chat_store.delete_session(thread_id)
    return {"ok": True}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # pulls text out of an uploaded file so it can be attached to the
    # next question as extra context, a PDF diet plan for example
    content = await file.read()
    filename = file.filename or "upload"

    if filename.lower().endswith(".pdf"):
        reader = pypdf.PdfReader(io.BytesIO(content))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        text = content.decode("utf-8", errors="ignore")

    # keeps one attachment from overwhelming the prompt
    text = text[:6000]

    return {"filename": filename, "text": text}


@app.get("/export/{thread_id}/{file_format}")
def export_chat(thread_id: str, file_format: str):
    payload = get_state_payload(thread_id)
    history = payload["history"]

    if file_format == "pdf":
        content = export_utils.build_pdf_bytes(history)
        media_type = "application/pdf"
        filename = "healthcare_chat.pdf"
    elif file_format == "docx":
        content = export_utils.build_docx_bytes(history)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = "healthcare_chat.docx"
    else:
        return {"error": "unsupported format, use pdf or docx"}

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), "r", encoding="utf-8") as f:
        page_html = f.read()
    return page_html.replace("__DISCLAIMER__", DISCLAIMER)