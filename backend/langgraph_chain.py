from langgraph.graph import StateGraph, END
from emotion_utils import detect_emotion
from llm_utils import generate_response
from typing import TypedDict
from cbt_utils import run_cbt_analysis
from session_manager import SessionManager
from journal_utils import save_journal

from langgraph.graph import StateGraph, END
from emotion_utils import detect_emotion
from llm_utils import generate_response
from typing import TypedDict
from cbt_utils import run_cbt_analysis
from session_manager import SessionManager
from journal_utils import save_journal
from pattern_utils import PatternRecognizer
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
    patterns_detected: dict
    should_surface_patterns: bool
    pattern_summary: str
    pattern_recommendations: list[str]

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

    # Check if we should include pattern insights
    pattern_summary = state.get("pattern_summary")
    patterns_detected = state.get("patterns_detected", {})
    
    # Pass CBT info if available
    cbt_info = None
    if should_provide_cbt:
        cbt_info = {
            "distortion": state.get("distortion"),
            "cbt_tool": state.get("cbt_tool")
        }
    
    # Pass pattern info if available
    pattern_info = None
    if pattern_summary and patterns_detected:
        pattern_info = {
            "summary": pattern_summary,
            "recommendations": patterns_detected.get("recommendations", [])
        }

    reply = generate_response(
        user_id=user_id,
        user_input=user_input,
        emotion=emotion,
        conversation_phase=phase,
        cbt_info=cbt_info,
        pattern_info=pattern_info
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

def pattern_recognition_node(state: ChatState) -> dict:
    """Node to analyze patterns and determine if they should be surfaced"""
    user_id = state["user_id"]
    
    recognizer = PatternRecognizer()
    patterns = recognizer.analyze_emotional_patterns(user_id, days_back=14)
    
    should_surface = recognizer.should_surface_pattern(patterns)
    pattern_summary = recognizer.get_pattern_summary(patterns) if should_surface else None
    
    return {
        "patterns_detected": patterns,
        "should_surface_patterns": should_surface,
        "pattern_summary": pattern_summary
    }

def should_surface_patterns(state: ChatState) -> str:
    """Condition function to determine if patterns should be surfaced"""
    return "surface_patterns" if state.get("should_surface_patterns", False) else "continue"

def cbt_analysis_node(state: ChatState) -> dict:
    """Runs CBT analysis when we have enough context"""
    should_provide_cbt = state.get("should_provide_cbt", False)
    
    if not should_provide_cbt:
        return {
            "distortion": None,
            "cbt_tool": None
        }
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
    patterns_detected = state.get("patterns_detected", {})
    
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
    elif patterns_detected and state.get("should_surface_patterns", False):
        # Journal pattern recognition
        journal_entry = f"""🔍 Pattern Recognition Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
Current emotion: {state.get('emotion', 'N/A')} (confidence: {state.get('confidence', 0):.2f})

Patterns detected:
- Recurring emotions: {list(patterns_detected.get('recurring_emotions', {}).keys())}
- Emotional cycles: {len(patterns_detected.get('emotional_cycles', []))} cycles found
- Trigger correlations: {len(patterns_detected.get('trigger_emotion_correlations', {}))} correlations

Pattern summary: {state.get('pattern_summary', 'None')}

Analysis period: {patterns_detected.get('analysis_period', 'N/A')}
Total emotional events: {patterns_detected.get('total_emotional_events', 0)}
"""
        save_journal(user_id, journal_entry, entry_type="pattern_recognition")
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

def should_check_patterns(state: ChatState) -> str:
    """Determines if we should check for patterns"""
    # Check patterns every 3rd conversation or when context depth is high
    context_depth = state.get("context_depth", 0)
    conversation_phase = state.get("conversation_phase", "exploring")
    
    # Check patterns when we have enough context or periodically
    if context_depth >= 1 or conversation_phase in ["exploring","building_context", "ready_for_cbt"]:
        return "check_patterns"
    return "skip_patterns"

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
builder.add_node("pattern_recognition", pattern_recognition_node)
builder.add_node("cbt_analysis", cbt_analysis_node)
builder.add_node("generate_response", generate_response_node)
builder.add_node("journal_writing", journal_writing_node)

# Set entry point
builder.set_entry_point("emotion_detection")

# Define the flow
builder.add_edge("emotion_detection", "assess_context")

# Conditional pattern checking
builder.add_conditional_edges(
    "assess_context",
    should_check_patterns,
    {
        "check_patterns": "pattern_recognition",
        "skip_patterns": "generate_response"  # Skip both patterns and CBT
    }
)

# From pattern recognition, check if we should surface patterns
builder.add_conditional_edges(
    "pattern_recognition",
    should_surface_patterns,
    {
        "surface_patterns": "generate_response",  # Skip CBT if surfacing patterns
        "continue": "cbt_analysis"  # Continue to CBT Analysis
    }
)

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
