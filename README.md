## TheraSage – Intelligent Mental Wellness Companion

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
