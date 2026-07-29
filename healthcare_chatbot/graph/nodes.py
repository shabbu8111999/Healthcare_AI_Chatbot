"""
Node functions for the LangGraph workflow.

Each node takes the current GraphState and returns only the fields it
wants to change, LangGraph merges these into the full state on its own.
The edges that connect these nodes into an actual flow come in
workflow.py next.
"""

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

import guardrails
import knowledge_base
from config import TOP_K_RESULTS
from graph.state import GraphState

# the vector store is expensive to build, so it gets built once and
# reused, instead of rebuilding it on every single node call
_vector_store = None


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = knowledge_base.build_vector_store()
    return _vector_store


def guardrail_node(state: GraphState):
    # look at what the user just typed
    last_message = state.messages[-1].content

    return {
        "is_emergency": guardrails.contains_emergency_signal(last_message),
        "is_off_topic": guardrails.contains_off_topic_signal(last_message),
        "is_casual": guardrails.is_casual_message(last_message),
    }


def emergency_node(state: GraphState):
    # short circuits here, no model call, straight to the safety message
    message = guardrails.EMERGENCY_MESSAGE
    return {
        "final_answer": message,
        "messages": [AIMessage(content=message)],
    }


def off_topic_node(state: GraphState):
    # same idea as emergency_node, just for unrelated questions
    message = guardrails.OFF_TOPIC_MESSAGE
    return {
        "final_answer": message,
        "messages": [AIMessage(content=message)],
    }


def casual_node(state: GraphState):
    # greetings, thanks, and quick questions about the bot itself.
    # these still get a real reply from Claude, just with no knowledge
    # base lookup and no review pause, there is nothing here that
    # needs checking before it reaches the user
    from prompts import chain

    context_text = "No relevant entries were found in the knowledge base."
    answer = chain.invoke({"context": context_text, "messages": state.messages})

    return {
        "final_answer": answer,
        "messages": [AIMessage(content=answer)],
    }


def retrieve_node(state: GraphState):
    # search the knowledge base for entries close to the user question
    last_message = state.messages[-1].content
    vector_store = _get_vector_store()
    results = vector_store.similarity_search_with_score(last_message, k=TOP_K_RESULTS)

    # turn LangChain's (Document, score) pairs into plain dicts, this is
    # the shape both the prompt and the Streamlit UI expect
    context = []
    for doc, score in results:
        context.append(
            {
                "content": doc.page_content,
                "topic": doc.metadata["topic"],
                "source": doc.metadata["source"],
                "score": float(score),  # lower score means more similar
            }
        )

    return {"retrieved_context": context}


def generate_node(state: GraphState):
    # imported here, not at the top, so this file still imports cleanly
    # even before prompts.py has a real API key set
    from prompts import chain

    # turn the retrieved chunks into the text block the system prompt
    # expects in place of {context}, and fold in an attached document
    # from the user, if one was uploaded with this question
    context_parts = []

    if state.attached_document:
        context_parts.append(
            "Document the user attached to this question:\n" + state.attached_document
        )

    if state.retrieved_context:
        context_parts.append(
            "\n\n".join(
                f"[{c['topic']} | source: {c['source']}]\n{c['content']}"
                for c in state.retrieved_context
            )
        )

    if context_parts:
        context_text = "\n\n".join(context_parts)
    else:
        context_text = "No relevant entries were found in the knowledge base."

    answer = chain.invoke({"context": context_text, "messages": state.messages})

    # note: the draft answer is NOT added to messages here on purpose.
    # only an approved answer should become part of the permanent chat
    # history, otherwise a rejected draft would sit in the transcript
    # right next to the regenerated one
    return {
        "final_answer": answer,
        "needs_human_review": True,
        "has_real_question": True,
        "loop_count": state.loop_count + 1,
    }


def human_review_node(state: GraphState):
    # this is the human in the loop step, it pauses the graph right
    # here, whoever resumes it sends back approve or reject
    decision = interrupt(
        {
            "question": "Approve this answer before it reaches the user?",
            "answer": state.final_answer,
        }
    )

    updates = {
        "human_decision": decision,
        "needs_human_review": False,
    }

    # only now, once approved, does the answer get added to the real
    # conversation history
    if decision == "approve":
        updates["messages"] = [AIMessage(content=state.final_answer)]

    return updates