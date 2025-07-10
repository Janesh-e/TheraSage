# TheraSage – Intelligent Mental Wellness Companion

**TheraSage** is an AI-powered emotional support companion that understands the user's feelings, provides empathetic responses, and gently introduces **CBT (Cognitive Behavioral Therapy)** tools for mental well-being. Users can interact via **text or voice**, and the system utilizes **LangGraph-based agent flows**, **emotion/sentiment analysis**, **depth-aware response logic**, and **journaling**, all while maintaining an emotionally intelligent and human-like tone.

TheraSage is designed to feel like a warm, trustworthy companion, not a cold chatbot, making mental health support more accessible, personalized, and non-intrusive.

---

## 📁 Project Folder Structure

```bash
project-root/
│
├── public/                  # Public assets for frontend (images, static files)
│
├── src/                     # React frontend source code
│   ├── components/          # React components (chat UI, buttons, recorder, etc.)
│   ├── pages/               # Frontend routes/pages
│   ├── utils/               # Frontend utilities (API handlers, audio helpers, etc.)
│   └── App.js               # Root React component
│
├── backend/                 # Backend server logic (FastAPI + LangGraph + SQLite)
│   ├── cbt_utils.py         # CBT tool suggestion logic and distortion detection
│   ├── db.py                # Database setup and ORM session management
│   ├── depth_analyzer.py    # Determines conversation depth to trigger CBT
│   ├── emotion_utils.py     # Emotion/sentiment detection for user input
│   ├── journal_utils.py     # Journal saving and retrieval logic
│   ├── langgraph_chain.py   # LangGraph chain definition and flow setup
│   ├── llm_utils.py         # LLM-based response generation with context memory
│   ├── main.py              # FastAPI routes and server entry point
│   ├── models.py            # SQLAlchemy models for users, messages, journals
│   ├── pattern_utils.py     # Heuristic patterns for detecting thought types
│   ├── run_db.py            # Utility to initialize or manage the database
│   ├── schemas.py           # Pydantic schemas for request and response validation
│   ├── session_manager.py   # Maintains and analyzes ongoing user conversation sessions
│   ├── stt_utils.py         # Handles speech-to-text logic using Whisper
│   ├── vad_utils.py         # Voice activity detection (to filter silence/empty clips)
│   └── chat_memory.db       # SQLite DB file storing user data, chats, and journals
│
├── README.md                # You’re reading it now
├── requirements.txt         # Backend dependencies
└── .env                     # Environment variables (if any)
```

---

## Features

* **Emotionally Intelligent Chatbot**
  Responds with empathy and understanding by detecting the user's emotional tone through their messages or voice inputs.

* **Multi-Modal Input (Text & Voice)**
  Users can either type messages or speak to the bot. Voice messages are transcribed using speech-to-text and handled seamlessly.

* **Context-Aware LangGraph Agent Flow**
  Uses LangGraph to structure conversation flow, assess conversation depth, and decide when to provide deeper insights or CBT tools.

* **Depth-Aware Interaction**
  Analyzes the entire conversation to determine when the user has reached a point of emotional openness, then gently guides toward helpful solutions.

* **🛠Implicit CBT Tool Suggestions**
  CBT (Cognitive Behavioral Therapy) techniques are introduced **indirectly**, without overwhelming or explicitly labeling them—ensuring a more human and natural experience.

* **Smart Journaling System**
  Automatically summarizes and saves key reflections, cognitive distortions, and insights from the conversation, enabling long-term tracking and continuity.

* **Persistent Conversation Memory**
  Previous conversations and journals are stored in a database, allowing the bot to remember and build upon the user's emotional history over multiple sessions.

* **Secure User Management**
  Signup/login system with password hashing and user-specific data separation, ensuring safe and personalized interactions.

* **Voice Playback of Bot Responses (TTS)**
  When enabled, the bot's replies can be read aloud, offering a hands-free experience for users needing extra accessibility or comfort.

---

