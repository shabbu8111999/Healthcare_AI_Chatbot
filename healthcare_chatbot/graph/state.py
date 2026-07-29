"""
Shared state definition for the LangGraph workflow.

This is the single object that flows through every node in the graph.
It carries the conversation, kept by the add_messages reducer, which is
what gives the chatbot memory of past turns, the RAG results, the
guardrail flags, and the fields the two extra techniques need on top of a
plain chain.

Human in the loop (HITL):
    needs_human_review and human_decision are read and written by the
    review node together with interrupt() and Command(resume=...), so a
    person can approve, edit, or reject an answer before it reaches the
    user.

Loop engineering:
    loop_count and max_loops let a node send the graph back to an earlier
    node to regenerate an answer, for example when a guardrail rejects a
    response, while max_loops stops that cycle from running forever.
"""

from dataclasses import dataclass, field
from typing import Annotated, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


@dataclass
class GraphState:
    messages: Annotated[list[BaseMessage], add_messages] = field(default_factory=list)
    retrieved_context: list = field(default_factory=list)
    attached_document: Optional[str] = None
    is_emergency: bool = False
    is_off_topic: bool = False
    is_casual: bool = False
    # set once the conversation has had a genuine, reviewed answer,
    # used by the frontend to decide whether the download buttons
    # should show, greetings and thanks alone should not trigger them
    has_real_question: bool = False
    needs_human_review: bool = False
    human_decision: Optional[str] = None
    loop_count: int = 0
    max_loops: int = 3
    final_answer: Optional[str] = None