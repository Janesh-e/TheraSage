from langgraph.graph import StateGraph, END
from emotion_utils import detect_emotion
from llm_utils import generate_response
from typing import TypedDict
from cbt_utils import run_cbt_analysis
from session_manager import SessionManager
from journal_utils import save_journal
from langchain_core.runnables import RunnableLambda
from datetime import datetime

class ChatState(TypedDict):
    user_id: str
    text: str
    emotion: str
    confidence: float
    distortion: str
    cbt_tool: str
    response: str
    journal_entry: str
    session_messages: list[str]
    should_reflect: bool
    should_provide_cbt: bool
    context_depth: int
    conversation_phase: str

# Define state keys
def get_emotion_node(state: ChatState):
    user_input = state["text"]
    emotion_result = detect_emotion(user_input)
    return {"emotion": emotion_result["emotion"], 
            "confidence": emotion_result["confidence"]}

def generate_response_node(state: ChatState):
    """Generates appropriate response based on conversation phase"""
    user_id = state["user_id"]
    user_input = state["text"]
    emotion = state["emotion"]
    phase = state["conversation_phase"]
    should_provide_cbt = state.get("should_provide_cbt", False)
    
    # Pass CBT info if available
    cbt_info = None
    if should_provide_cbt:
        cbt_info = {
            "distortion": state.get("distortion"),
            "cbt_tool": state.get("cbt_tool")
        }
    
    reply = generate_response(
        user_id=user_id,
        user_input=user_input,
        emotion=emotion,
        conversation_phase=phase,
        cbt_info=cbt_info
    )
    
    return {"response": reply}

def assess_context_depth_node(state: ChatState) -> dict:
    """Determines if we have enough context to provide CBT suggestions"""
    user_id = state["user_id"]
    current_input = state["text"]
    
    session = SessionManager(user_id)
    analysis = session.analyze_conversation_depth()
    session.close()
    
    # Determine conversation phase based on context depth
    if analysis["context_depth"] < 2:
        phase = "exploring"
    elif analysis["context_depth"] < 4:
        phase = "building_context"
    else:
        phase = "ready_for_cbt"
    
    # Check if we should provide CBT tools
    should_provide_cbt = (
        analysis["context_depth"] >= 3 and
        analysis["emotional_intensity"] > 0.6 and
        analysis["has_specific_situation"]
    )
    
    return {
        "context_depth": analysis["context_depth"],
        "conversation_phase": phase,
        "should_provide_cbt": should_provide_cbt,
        "session_messages": analysis["recent_messages"]
    }

def cbt_analysis_node(state: ChatState) -> dict:
    """Runs CBT analysis when we have enough context"""
    user_input = state["text"]
    session_messages = state.get("session_messages", [])
    
    # Analyze current input plus recent context
    full_context = "\n".join(session_messages[-3:] + [user_input])
    result = run_cbt_analysis(full_context)
    
    return {
        "distortion": result["distortion"],
        "cbt_tool": result["cbt_tool"]
    }

def check_reflection_node(state: dict) -> dict:
    """Node function - returns dict to update state"""
    user_id = state["user_id"]
    
    session = SessionManager(user_id)
    analysis = session.analyze_session()
    session.close()
    
    updates = {"should_reflect": analysis["should_reflect"]}
    
    if analysis["should_reflect"]:
        # Add context for future nodes
        updates.update({
            "session_messages": analysis["messages"],
            "emotion": analysis["emotion"],
            "confidence": analysis["confidence"]
        })
    
    return updates

def check_reflection_condition(state: dict) -> str:
    """Condition function - returns string for routing"""
    return "reflect" if state.get("should_reflect", False) else "continue"
    
def journal_writing_node(state: ChatState) -> dict:
    """Journals significant interactions and CBT progress"""
    user_id = state["user_id"]
    should_provide_cbt = state.get("should_provide_cbt", False)
    
    if should_provide_cbt:
        # Journal CBT interaction
        journal_entry = f"""📝 CBT Session Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
Emotion detected: {state.get('emotion', 'N/A')} (confidence: {state.get('confidence', 0):.2f})
Cognitive distortion: {state.get('distortion', 'None identified')}
CBT Tool suggested: {state.get('cbt_tool', 'None')}

User's situation:
{state.get('text', '')}

Context depth: {state.get('context_depth', 0)}
"""
        save_journal(user_id, journal_entry, entry_type="cbt_session")
    else:
        # Journal emotional check-in
        journal_entry = f"""💭 Emotional Check-in - {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
Emotion: {state.get('emotion', 'N/A')} (confidence: {state.get('confidence', 0):.2f})
Phase: {state.get('conversation_phase', 'exploring')}

User shared: {state.get('text', '')[:200]}...
"""
        save_journal(user_id, journal_entry, entry_type="emotional_checkin")
    
    return {"journal_entry": journal_entry}

def should_analyze_cbt(state: ChatState) -> str:
    """Determines if we should run CBT analysis"""
    return "analyze_cbt" if state.get("should_provide_cbt", False) else "skip_cbt"

def should_journal(state: ChatState) -> str:
    """Determines if we should journal this interaction"""
    # Journal CBT sessions and significant emotional interactions
    if (state.get("should_provide_cbt", False) or 
        state.get("confidence", 0) > 0.7 or
        state.get("context_depth", 0) >= 2):
        return "journal"
    return "skip_journal"


# Define the state structure
builder = StateGraph(ChatState)

# Add nodes
builder.add_node("emotion_detection", get_emotion_node)
builder.add_node("assess_context", assess_context_depth_node)
builder.add_node("cbt_analysis", cbt_analysis_node)
builder.add_node("generate_response", generate_response_node)
builder.add_node("journal_writing", journal_writing_node)

# Set entry point
builder.set_entry_point("emotion_detection")

# Define the flow
builder.add_edge("emotion_detection", "assess_context")

# Conditional CBT analysis based on context depth
builder.add_conditional_edges(
    "assess_context",
    should_analyze_cbt,
    {
        "analyze_cbt": "cbt_analysis",
        "skip_cbt": "generate_response"
    }
)

# From CBT analysis to response generation
builder.add_edge("cbt_analysis", "generate_response")

# Conditional journaling
builder.add_conditional_edges(
    "generate_response",
    should_journal,
    {
        "journal": "journal_writing",
        "skip_journal": END
    }
)

# End after journaling
builder.add_edge("journal_writing", END)

flow = builder.compile()
