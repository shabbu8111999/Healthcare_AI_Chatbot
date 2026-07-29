"""
Wires the node functions from nodes.py into an actual LangGraph flow.

This is where the two extra techniques become real edges:

Human in the loop: after generate_node, the flow always stops at
human_review_node before an answer can leave the graph.

Loop engineering: if the reviewer rejects an answer, the conditional
edge below sends the flow back to generate_node instead of ending,
capped by max_loops so it cannot loop forever.
"""

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from config import CHECKPOINT_DB_PATH
from graph.nodes import (
    casual_node,
    emergency_node,
    generate_node,
    guardrail_node,
    human_review_node,
    off_topic_node,
    retrieve_node,
)
from graph.state import GraphState


def route_after_guardrail(state: GraphState) -> str:
    # decide which path to take right after the safety checks
    if state.is_emergency:
        return "emergency"
    if state.is_off_topic:
        return "off_topic"
    if state.is_casual:
        return "casual"
    return "retrieve"


def route_after_review(state: GraphState) -> str:
    # this is the loop engineering decision point, only regenerate on a
    # reject, and only while there is still room under max_loops
    if state.human_decision == "reject" and state.loop_count < state.max_loops:
        return "regenerate"
    return "end"


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("guardrail", guardrail_node)
    builder.add_node("emergency", emergency_node)
    builder.add_node("off_topic", off_topic_node)
    builder.add_node("casual", casual_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_node("human_review", human_review_node)

    builder.add_edge(START, "guardrail")

    # branch right after the safety checks
    builder.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {
            "emergency": "emergency",
            "off_topic": "off_topic",
            "casual": "casual",
            "retrieve": "retrieve",
        },
    )

    builder.add_edge("emergency", END)
    builder.add_edge("off_topic", END)
    builder.add_edge("casual", END)
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "human_review")

    # branch after the human in the loop step, this edge is the loop
    # engineering part, it can send the flow back to generate
    builder.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "regenerate": "generate",
            "end": END,
        },
    )

    # check_same_thread is off since Streamlit can touch this connection
    # from more than one thread across reruns
    conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    return builder.compile(checkpointer=checkpointer)