# Healthcare Assistant Chatbot

A chatbot that answers general health questions using Claude, with a knowledge base, safety checks, and a review step before any answer reaches the user. Built as part of an AI Engineer assignment.

## What this chatbot does

It answers general questions about:

- Common symptoms
- General diseases
- Healthy lifestyle
- Nutrition and diet
- Preventive healthcare
- First aid guidance

It does **not** give a medical diagnosis, does **not** recommend medicines or dosages, and always reminds the user to see a real doctor for anything specific to their own situation. A disclaimer is shown at the top of the page at all times.

## Tech stack

- **FastAPI** for the backend
- **Claude Sonnet 5** (Anthropic API) as the model
- **LangChain** for the prompt and the chain
- **LangGraph** for the workflow, guardrails, retrieval, generation, and the human review step
- **FAISS** with **sentence transformers** for the knowledge base search
- **SQLite** for saving conversations, so chat history survives a restart
- **LangSmith** for tracing every step of a conversation
- Plain **HTML, CSS, and JavaScript** for the interface, no frontend framework

## Project structure

```
healthcare_chatbot/
├── app.py               main FastAPI app and all routes
├── config.py             settings, loads from .env
├── prompts.py            the system prompt and the chain
├── guardrails.py         emergency, off topic, and casual message checks
├── knowledge_base.py     builds the FAISS search index
├── chat_store.py         saves chat titles for the sidebar
├── export_utils.py       builds the PDF and Word downloads
├── requirements.txt
├── .env                  your own keys go here, not shared
├── data/
│   └── medical_kb.json   the knowledge base entries
├── graph/
│   ├── state.py          the shared state that flows through the graph
│   ├── nodes.py           each step in the workflow
│   └── workflow.py        connects the steps together
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## Features

- Answers grounded in a small medical knowledge base, with sources shown under each answer
- Emergency messages are caught and redirected straight to emergency guidance, no model call needed
- Casual messages like greetings or thank you get a quick reply with no review step, so the person is not slowed down for things that do not need checking
- Real health answers pause for a human review step before they are shown, with an option to approve or ask for a new answer
- Full chat history, multiple conversations in a sidebar, all saved to disk
- Upload a PDF or text file and ask a question about it
- Speak your question using the microphone instead of typing
- Download a finished conversation as a PDF or Word file

## Setup and running it with uv

1. Open a terminal inside the `healthcare_chatbot` folder.

2. Create the virtual environment:
```
uv venv
```

3. Install everything the project needs:
```
uv pip install -r requirements.txt
```

4. Open the `.env` file and fill in your own keys:
```
ANTHROPIC_API_KEY=your_real_key_here
LANGSMITH_TRACING_V2=true
LANGSMITH_API_KEY=your_real_key_here
LANGSMITH_PROJECT=healthcare_chatbot
```

5. Run the app:
```
uv run uvicorn app:app --reload
```

6. Open a browser and go to:
```
http://localhost:8000
```

The first time it runs, it downloads a small embedding model in the background, so that first run needs a working internet connection and takes a little longer. After that it is cached and starts fast.

## Challenges faced and solutions

**Claude Sonnet 5 stopped accepting a temperature setting**
Setting a custom temperature caused the model to reject the request. The fix was to remove it completely and instead ask for a calm, steady tone directly inside the prompt text.

**The .env file was not loading when the app was started from a different folder**
By default, the settings file is only found if you run the app from the exact folder it lives in. This was fixed by making the app always look for .env right next to config.py itself, no matter which folder the command is run from.

**The sidebar chat menu looked broken**
The three dot menu on each chat was sitting inside a box that scrolls, so the browser was cutting off part of the menu. It was fixed by moving the menu outside that scrolling box and positioning it directly with JavaScript.

**Downloading a chat as a PDF was crashing**
The PDF library was not moving back to the left edge of the page after writing a line of text, so the next line sometimes had no room left and the app crashed. The fix was to reset the position back to the left edge after every line.

**A confusing torchvision warning appeared on startup**
This came from an unrelated part of Streamlit checking every loaded library on startup, not from anything in this project. It went away completely once the interface was rebuilt in FastAPI instead of Streamlit.

**Moving from Streamlit to FastAPI**
Streamlit was quick to get a first version running, but a sidebar, file uploads, and voice input needed more control over the page than Streamlit easily allows. The interface was rebuilt using FastAPI with plain HTML, CSS, and JavaScript so every part of the page could be shaped exactly as needed.

## Notes

This chatbot is for general health information only. It is not a replacement for a doctor, and it should never be used for real medical emergencies. If you are testing this project, please do not rely on it for actual health decisions.

---
Built by Shabareesh Nair
