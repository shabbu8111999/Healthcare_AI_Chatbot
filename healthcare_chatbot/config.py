"""
Central configuration for the healthcare chatbot.
Every other module reads its settings from here so there is one place
to change the model, the embedding model, or how conversations are stored.
"""

import os

from dotenv import load_dotenv

# anchor to this file's own folder, not the OS working directory, so
# this works the same whether the app is launched from inside this
# folder or from one level above it
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

# Anthropic Claude settings, used by langchain_anthropic.ChatAnthropic
ANTHROPIC_API_KEY = os.environ.get("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-sonnet-5"  # check Anthropic's docs for the current model name before running
MAX_TOKENS = 1024

# Embedding model used to build the FAISS index over the knowledge base
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K_RESULTS = 3

# The six topic areas the assignment allows the chatbot to answer on
ALLOWED_TOPICS = [
    "common symptoms",
    "general diseases",
    "healthy lifestyle suggestions",
    "nutrition and diet",
    "preventive healthcare",
    "first aid guidance",
]

# Human in the loop switch, when true the graph pauses for a review step
# before sending back any answer the guardrails flag as sensitive
ENABLE_HUMAN_REVIEW = True

# Conversation memory settings.
# SqliteSaver stores the full LangGraph state, including message history, in a local file.
CHECKPOINT_DB_PATH = os.environ.get("CHECKPOINT_DB_PATH", os.path.join(BASE_DIR, "checkpoints.db"))