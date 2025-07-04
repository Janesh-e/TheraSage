from langgraph.graph import StateGraph, END
from emotion_utils import detect_emotion
from llm_utils import generate_response
from typing import TypedDict
from cbt_utils import run_cbt_analysis

class ChatState(TypedDict):
    user_id: str
    text: str
    emotion: str
    confidence: float
    distortion: str
    cbt_tool: str
    response: str

# Define state keys
def get_emotion_node(state: ChatState):
    user_input = state["text"]
    emotion_result = detect_emotion(user_input)
    return {"emotion": emotion_result["emotion"], "confidence": emotion_result["confidence"]}

def get_llm_response_node(state: ChatState):
    user_id = state["user_id"]
    user_input = state["text"]
    emotion = state["emotion"]
    reply = generate_response(user_id, user_input, emotion)
    return {"response": reply}

def cbt_tool_node(state: ChatState) -> dict:
    result = run_cbt_analysis(state["text"])
    return {
        "distortion": result["distortion"],
        "cbt_tool": result["cbt_tool"]
    }

# Define the state structure
builder = StateGraph(ChatState)

# Input: text -> emotion -> response -> END
builder.add_node("emotion_detector", get_emotion_node)
builder.add_node("response_generator", get_llm_response_node)
builder.add_node("cbt_tools", cbt_tool_node)

builder.set_entry_point("emotion_detector")
builder.add_edge("emotion_detector", "cbt_tools")
builder.add_edge("cbt_tools", "response_generator")
builder.add_edge("response_generator", END)

flow = builder.compile()
