# Healthcare Assistant Chatbot

A chatbot that answers general health questions using Claude, with a knowledge base, safety checks, and a human review step before any answer reaches the user. Built as part of an AI Engineer assignment.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-teal?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-enabled-green?logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-workflow-purple)
![Claude](https://img.shields.io/badge/Claude-Sonnet%205-orange?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Screenshots](#screenshots)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup with uv](#setup-with-uv)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [API Endpoints](#api-endpoints)
- [Challenges Faced and Solutions](#challenges-faced-and-solutions)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Contact](#contact)

## About

This chatbot answers general questions about:

- Common symptoms
- General diseases
- Healthy lifestyle
- Nutrition and diet
- Preventive healthcare
- First aid guidance

It does **not** give a medical diagnosis, does **not** recommend medicines or dosages, and always points the user to a real doctor for anything specific to their own situation. A disclaimer is shown on the page at all times.

## Features

- Answers grounded in a small medical knowledge base, with sources shown under each answer
- Emergency messages are caught and redirected straight to emergency guidance, no model call needed
- Casual messages like greetings or thank you get a quick reply with no review step, so the person is not slowed down for things that do not need checking
- Real health answers pause for a human review step before they are shown, with an option to approve the answer or ask for a new one
- Full chat history, multiple conversations in a sidebar, all saved to disk and still there after a restart
- Upload a PDF or text file and ask a question about it
- Speak your question using the microphone instead of typing
- Download a finished conversation as a PDF or Word file
- Every step of a conversation is traced in LangSmith

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI |
| Model | Claude Sonnet 5 (Anthropic API) |
| Orchestration | LangChain and LangGraph |
| Vector search | FAISS with sentence transformers |
| Storage | SQLite, for chat history and saved sessions |
| Tracing | LangSmith |
| Frontend | Plain HTML, CSS, and JavaScript, no framework |
| Package manager | uv |


## Project Structure

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

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) installed
- An Anthropic API key
- A LangSmith API key, for tracing

## Setup with uv

1. Open a terminal inside the `healthcare_chatbot` folder.

2. Create the virtual environment:
```
uv init .
```

3. Install everything the project needs:
```
uv add -r requirements.txt
```

## Environment Variables

Open the `.env` file inside `healthcare_chatbot` and fill in your own keys:

```
ANTHROPIC_API_KEY=your_real_key_here
LANGSMITH_TRACING_V2=true
LANGSMITH_API_KEY=your_real_key_here
LANGSMITH_PROJECT=healthcare_chatbot
```
`Just a heads up, you can avoid LangSmith, because the setup of LangSmith is different, if you know then please continue the testing.`

`.env` file is not there, so I have used Anthropic if you want to try you have to add your own API Key.

## Running the App

From inside the `healthcare_chatbot` folder:

```
uv run uvicorn app:app --reload
```

Then open a browser and go to:

```
http://localhost:8000
```

The first run downloads a small embedding model in the background, so it needs a working internet connection and takes a little longer. After that it is cached and starts fast.

## API Endpoints

| Method | Endpoint | What it does |
|---|---|---|
| GET | `/` | Loads the chat page |
| POST | `/chat` | Sends a new message |
| POST | `/review` | Approves an answer, or asks for a new one |
| GET | `/history/{thread_id}` | Loads a past conversation |
| GET | `/chats` | Lists all saved chats |
| POST | `/chats/{thread_id}/rename` | Renames a chat |
| DELETE | `/chats/{thread_id}` | Deletes a chat from the list |
| POST | `/upload` | Extracts text from an uploaded file |
| GET | `/export/{thread_id}/{format}` | Downloads the chat as PDF or Word, format is pdf or docx |

## Challenges Faced and Solutions

**Claude Sonnet 5 stopped accepting a temperature setting**
Setting a custom temperature caused the model to reject the request. The fix was to remove it completely and instead ask for a calm, steady tone directly inside the prompt text.

**The .env file was not loading when the app was started from a different folder**
By default, the settings file is only found if you run the app from the exact folder it lives in. This was fixed by making the app always look for `.env` right next to `config.py` itself, no matter which folder the command is run from.

**The sidebar chat menu looked broken**
The three dot menu on each chat was sitting inside a box that scrolls, so the browser was cutting off part of the menu. It was fixed by moving the menu outside that scrolling box and positioning it directly with JavaScript.

**Downloading a chat as a PDF was crashing**
The PDF library was not moving back to the left edge of the page after writing a line of text, so the next line sometimes had no room left and the app crashed. The fix was to reset the position back to the left edge after every line.

**A confusing torchvision warning appeared on startup**
This came from an unrelated part of Streamlit checking every loaded library on startup, not from anything in this project. It went away completely once the interface was rebuilt in FastAPI instead of Streamlit.

**Moving from Streamlit to FastAPI**
Streamlit was quick to get a first version running, but a sidebar, file uploads, and voice input needed more control over the page than Streamlit easily allows. The interface was rebuilt using FastAPI with plain HTML, CSS, and JavaScript so every part of the page could be shaped exactly as needed.

## Disclaimer

This chatbot is for general health information only. It is not a replacement for a doctor, and it should never be used for real medical emergencies. If you are testing this project, please do not rely on it for actual health decisions.

## License

This project was built for an AI Engineer job assignment and as a personal portfolio piece. Released under the MIT License, feel free to reference it with credit.

## Contact

**Shabareesh Nair**

[![GitHub](https://img.shields.io/badge/GitHub-shabbu8111999-black?logo=github&logoColor=white)](https://github.com/shabbu8111999)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Shabareesh%20Nair-blue?logo=linkedin&logoColor=white)](https://linkedin.com/in/shabareesh-nair)
