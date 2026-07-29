"""
Prompt template and LLM chain for the healthcare chatbot.

This file builds the chain the assignment asked for:
    chain = prompt | model | StrOutputParser()
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import ALLOWED_TOPICS, ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS

# Turning the topic list from config.py into plain bullet points so the
# prompt text and the actual allowed scope never fall out of sync.
_TOPIC_LIST = "\n".join(f"- {topic}" for topic in ALLOWED_TOPICS)

# This is the system prompt that sets the rules for the chatbot and provides the retrieved context.
SYSTEM_PROMPT = f"""You are a helpful healthcare information assistant.

You may answer general questions about:
{_TOPIC_LIST}

Rules you must always follow:
1. Never give a medical diagnosis. Share general information only, and
   tell the user to see a qualified healthcare professional for anything
   specific to their own situation.
2. Never prescribe medication names or dosages.
3. If the question is not about health, say so politely and steer back
   to what you can help with.
4. Keep the language simple, explain any medical term you use.
5. When you use the knowledge base context below, mention which topic it
   came from so the answer is grounded.
6. End any answer about a symptom or condition with a short reminder
   that this is general information, not a diagnosis.
7. Write in a calm, measured, and factual tone, avoid dramatic or
   alarming language.

Knowledge base context for this question:
{{context}}

If the context above has nothing relevant, answer using general health
knowledge and say so, do not pretend it came from the knowledge base.
"""

# The actual prompt template that turns the system prompt and 
# the conversation messages into a list of messages for the model to read.
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

model = ChatAnthropic(
    model=CLAUDE_MODEL,
    api_key=ANTHROPIC_API_KEY,
    max_tokens=MAX_TOKENS,
)

# The chain itself.
# Order matters here: prompt runs first and turns our variables into
# formatted messages, then the model reads those messages and replies,
# then the parser pulls the plain text string out of that reply.
chain = prompt | model | StrOutputParser()