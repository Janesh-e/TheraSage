import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
import asyncio
import requests

from dotenv import load_dotenv
load_dotenv()

from models import (
    User, ChatSession, ChatMessage, CrisisAlert, 
    MessageRole, RiskLevel, CrisisType
)

# Alternative Suggestion: Consider using Anthropic Claude-3 or locally hosted LLaMA 3.2-8B fine-tuned on mental health data for better therapeutic responses and privacy

class ConversationAnalysis(BaseModel):
    """Structure for conversation analysis results"""
    emotional_state: str
    risk_level: int  # 0-10 scale
    context_depth: str  # 'shallow', 'moderate', 'deep'
    repetitive_patterns: List[str]
    suggested_interventions: List[str]
    cbt_recommendation: bool
    requires_human_escalation: bool

class OpenRouterClient:
    """Custom OpenRouter client for DeepSeek API calls"""
    
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-chat-v3.1:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def ainvoke(self, messages: List, temperature: float = 0.7, max_tokens: int = 1500):
        """Async invoke method compatible with LangChain interface"""
        
        # Convert LangChain message format to OpenRouter format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            else:
                # Handle raw message content
                if hasattr(msg, 'content'):
                    formatted_messages.append({"role": "system", "content": msg.content})
                else:
                    formatted_messages.append({"role": "system", "content": str(msg)})
        
        # Make API call
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Return object with content attribute for compatibility
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        return MockResponse(content)

class EmotionalSupportAgent:
    """Core AI agent for emotional support conversations"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Get API key from environment
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        # Initialize OpenRouter clients for different purposes
        self.llm = OpenRouterClient(
            api_key=self.api_key,
            model="deepseek/deepseek-chat-v3.1:free"
        )
        
        # CBT-focused client for therapeutic interventions
        self.cbt_llm = OpenRouterClient(
            api_key=self.api_key,
            model="deepseek/deepseek-chat-v3.1:free"
        )
        
        # Crisis detection client
        self.crisis_llm = OpenRouterClient(
            api_key=self.api_key,
            model="deepseek/deepseek-chat-v3.1:free"
        )
        
        # Initialize memory for conversation state
        self.memory = MemorySaver()
        self.workflow = self._create_conversation_workflow()
    
    def _create_conversation_workflow(self) -> StateGraph:
        """Create LangGraph workflow for conversation handling"""
        
        workflow = StateGraph(MessagesState)
        
        # Define workflow nodes
        workflow.add_node("analyze_input", self._analyze_user_input)
        workflow.add_node("check_context_depth", self._check_context_depth)
        workflow.add_node("detect_patterns", self._detect_repetitive_patterns)
        workflow.add_node("crisis_assessment", self._assess_crisis_risk)
        workflow.add_node("generate_response", self._generate_empathetic_response)
        workflow.add_node("cbt_intervention", self._provide_cbt_intervention)
        workflow.add_node("escalate_crisis", self._handle_crisis_escalation)
        
        # Define workflow edges and conditions
        workflow.add_edge(START, "analyze_input")
        workflow.add_edge("analyze_input", "check_context_depth")
        workflow.add_edge("check_context_depth", "detect_patterns")
        workflow.add_edge("detect_patterns", "crisis_assessment")
        
        # Conditional routing based on crisis assessment
        workflow.add_conditional_edges(
            "crisis_assessment",
            self._should_escalate_crisis,
            {
                "escalate": "escalate_crisis",
                "cbt": "cbt_intervention", 
                "respond": "generate_response"
            }
        )
        
        workflow.add_edge("escalate_crisis", END)
        workflow.add_edge("cbt_intervention", END)
        workflow.add_edge("generate_response", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _analyze_user_input(self, state: MessagesState) -> MessagesState:
        """Analyze user's emotional state and message content"""
        
        state["analyze_user_input_path"] = None
        user_message = state["messages"][-1].content
        user_id = state.get("user_id")
        
        # Get user's conversation history for context
        user_history = await self._get_user_conversation_history(user_id)
        
        analysis_prompt = f"""
        You are an expert mental health AI analyzing a student's message for emotional support.
        
        User's current message: "{user_message}"
        
        Previous conversation context: {user_history[-5:] if user_history else "None"}
        
        Provide EXACTLY the following JSON object (no additional text):
        {{
        "emotional_state": "<one word>",
        "urgency_level": <integer 1–10>,
        "concerns": [<strings>],
        "cognitive_distortions": [<strings>],
        "intervention_ready": <true|false>
        }}
        """
        
        analysis_response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)], temperature=0.3, max_tokens=1500)
        state["analysis_raw"] = analysis_response.content
        
        try:
            analysis_data = json.loads(analysis_response.content)
            state["analyze_user_input_path"] = "try"
            state["analysis"] = analysis_data
        except:
            state["analyze_user_input_path"] = "except"
            # Fallback if JSON parsing fails
            state["analysis"] = {
                "emotional_state": "neutral",
                "urgency_level": 3,
                "concerns": ["general conversation"],
                "cognitive_distortions": [],
                "intervention_ready": False
            }
        
        return state
    
    async def _check_context_depth(self, state: MessagesState) -> MessagesState:
        """Evaluate if the conversation has sufficient context depth"""

        user_id = state.get("user_id")
        session_id = state.get("session_id")
        
        # Get current session message count
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        message_count = session.total_messages if session else 0
        
        # Determine context depth
        if message_count < 3:
            context_depth = "shallow"
        elif message_count < 8:
            context_depth = "moderate"  
        else:
            context_depth = "deep"
        
        state["context_depth"] = context_depth
        
        # If shallow context, ask follow-up questions
        # disable forcing follow-ups on initial messages:
        # if context_depth == "shallow":
            # state["needs_context_building"] = True
        
        return state
    
    async def _detect_repetitive_patterns(self, state: MessagesState) -> MessagesState:
        """Identify repetitive emotional or behavioral patterns"""
        
        user_id = state.get("user_id")
        
        # Get user's recent conversations across multiple sessions
        recent_sessions = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.created_at >= datetime.utcnow() - timedelta(days=30)
        ).order_by(ChatSession.created_at.desc()).limit(10).all()
        
        patterns_found = []
        
        if len(recent_sessions) >= 3:
            # Analyze for recurring themes
            session_summaries = [session.conversation_summary for session in recent_sessions if session.conversation_summary]
            
            if session_summaries:
                pattern_prompt = f"""
                Analyze these conversation summaries from the past 30 days for repetitive patterns:
                {session_summaries}
                
                Identify:
                1. Recurring emotional states
                2. Repeated concerns or stressors
                3. Cyclical thought patterns
                4. Consistent triggers
                
                List the top 3 most significant patterns found.
                """
                
                pattern_response = await self.llm.ainvoke([HumanMessage(content=pattern_prompt)])
                patterns_found = pattern_response.content.split('\n')[:3]
        
        state["repetitive_patterns"] = patterns_found
        return state
    
    async def _assess_crisis_risk(self, state: MessagesState) -> MessagesState:
        """Assess suicide/crisis risk and determine intervention needs"""
        
        state["assess_crisis_path"] = None
        user_message = state["messages"][-1].content
        analysis = state.get("analysis", {})
        patterns = state.get("repetitive_patterns", [])
        
        crisis_prompt = f"""
        You are a crisis assessment AI trained in suicide risk evaluation.
        
        User message: "{user_message}"
        Emotional analysis: {analysis}
        Recent patterns: {patterns}
        
        Assess crisis risk level (0-10):
        - 0-2: No risk
        - 3-4: Mild distress
        - 5-6: Moderate concern
        - 7-8: High risk - immediate intervention needed
        - 9-10: Critical - emergency response required
        
        Look for:
        - Suicidal ideation keywords
        - Hopelessness expressions
        - Self-harm mentions
        - Substance abuse indicators
        - Social isolation signs
        - Sudden mood changes
        
        Respond with JSON: {{"risk_score": X, "risk_factors": [], "immediate_action_needed": boolean}}
        """
        
        crisis_response = await self.crisis_llm.ainvoke([HumanMessage(content=crisis_prompt)])
        state["crisis_raw"] = crisis_response.content
        
        try:
            crisis_data = json.loads(crisis_response.content)
            state["assess_crisis_path"] = "try"
            state["crisis_assessment"] = crisis_data
            
            # Log crisis alert if high risk
            if crisis_data["risk_score"] >= 7:
                await self._create_crisis_alert(
                    state.get("user_id"),
                    state.get("session_id"), 
                    crisis_data
                )
        except:
            state["assess_crisis_path"] = "except"
            state["crisis_assessment"] = {"risk_score": 0, "risk_factors": [], "immediate_action_needed": False}
        
        return state
    
    def _should_escalate_crisis(self, state: MessagesState) -> str:
        """Determine next workflow step based on crisis assessment"""
        
        crisis_data = state.get("crisis_assessment", {})
        risk_score = crisis_data.get("risk_score", 0)
        analysis = state.get("analysis", {})
        context_depth = state.get("context_depth", "shallow")
        
        if risk_score >= 7:
            return "escalate"
        elif (risk_score >= 4 and context_depth != "shallow" and 
              analysis.get("intervention_ready", False)):
            return "cbt"
        else:
            return "respond"
    
    async def _handle_crisis_escalation(self, state: MessagesState) -> MessagesState:
        """Handle high-risk crisis situations"""
        
        crisis_resources = """
        I'm genuinely concerned about you and want to help. Please consider reaching out to:
        
        🚨 **Immediate Crisis Support:**
        • National Crisis Hotline: 988 (24/7)
        • Crisis Text Line: Text HOME to 741741
        • Emergency Services: 911
        
        🏥 **Campus Resources:**
        • Campus Counseling Center: [Available 24/7]
        • Campus Safety: [Emergency contact]
        
        💬 **Right Now:**
        • You're not alone in this
        • These feelings can change
        • Help is available and effective
        
        I've also scheduled an urgent consultation with a licensed counselor. 
        Would you like to talk about what you're feeling right now?
        """
        
        state["messages"].append(AIMessage(content=crisis_resources))
        state["intervention_type"] = "crisis_escalation"
        
        return state
    
    async def _provide_cbt_intervention(self, state: MessagesState) -> MessagesState:
        """Provide CBT-based therapeutic intervention"""
        
        user_message = state["messages"][-1].content
        analysis = state.get("analysis", {})
        patterns = state.get("repetitive_patterns", [])
        
        cbt_prompt = f"""
        You are a CBT-trained AI therapist providing evidence-based interventions.
        
        User's message: "{user_message}"
        Emotional state: {analysis.get('emotional_state', 'unknown')}
        Identified patterns: {patterns}
        Cognitive distortions detected: {analysis.get('cognitive_distortions', [])}
        
        Provide a CBT intervention that includes:
        1. Validation of their feelings
        2. Identification of thought patterns
        3. Gentle challenging of distorted thinking
        4. Practical coping strategy
        5. Homework/practice suggestion
        
        Keep it conversational, empathetic, and age-appropriate for college students.
        Focus on building self-awareness and coping skills.
        """
        
        cbt_response = await self.cbt_llm.ainvoke([HumanMessage(content=cbt_prompt)])
        
        # Add CBT resource links
        cbt_content = cbt_response.content + """
        
        💡 **Additional CBT Resources:**
        • Thought Record Worksheet
        • Mindfulness Exercise (5-minute guided)
        • Behavioral Activation Schedule
        
        Would you like to try one of these exercises together?
        """
        
        state["messages"].append(AIMessage(content=cbt_content))
        state["intervention_type"] = "cbt_therapy"
        
        return state
    
    async def _generate_empathetic_response(self, state: MessagesState) -> MessagesState:
        """Generate supportive, empathetic response for general conversations"""
        
        user_message = state["messages"][-1].content
        analysis = state.get("analysis", {})
        context_depth = state.get("context_depth", "shallow")
        needs_context = state.get("needs_context_building", False)
        
        # Build context-aware prompt
        if needs_context:
            response_prompt = f"""
            You are a compassionate AI counselor for college students. The conversation just started.
            
            User said: "{user_message}"
            Their emotional state appears to be: {analysis.get('emotional_state', 'neutral')}
            
            Respond with:
            1. Warm acknowledgment of their sharing
            2. Gentle follow-up questions to understand their situation better
            3. Validation of their feelings
            4. Invitation to share more when ready
            
            Keep it natural, non-clinical, and supportive. Ask about their college experience, current stressors, or what brought them here today.
            """
        else:
            response_prompt = f"""
            You are an experienced, empathetic AI counselor specialized in supporting college students.
            
            User's message: "{user_message}"
            Current emotional state: {analysis.get('emotional_state', 'neutral')}
            Conversation depth: {context_depth}
            Recurring patterns: {state.get('repetitive_patterns', [])}
            
            Provide a thoughtful response that:
            1. Shows genuine understanding and empathy
            2. Reflects back their emotions appropriately
            3. Offers gentle insights or reframes if helpful
            4. Suggests practical next steps or coping strategies
            5. Maintains hope and encouragement
            
            Be authentic, warm, and professional. Avoid being too clinical or robotic.
            """
        
        response = await self.llm.ainvoke([HumanMessage(content=response_prompt)])
        
        state["messages"].append(AIMessage(content=response.content))
        state["intervention_type"] = "supportive_conversation"
        
        return state
    
    async def _get_user_conversation_history(self, user_id: str) -> List[str]:
        """Retrieve user's recent conversation history for context"""
        
        recent_messages = self.db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatMessage.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()
        
        history = []
        for msg in reversed(recent_messages):
            role = "User" if msg.role == MessageRole.USER else "AI"
            history.append(f"{role}: {msg.content[:200]}")  # Truncate for context
        
        return history
    
    async def _create_crisis_alert(self, user_id: str, session_id: str, crisis_data: Dict):
        """Create crisis alert record in database"""
        
        # Determine crisis type based on risk factors
        risk_factors = crisis_data.get("risk_factors", [])
        crisis_type = CrisisType.SEVERE_DEPRESSION  # Default
        
        if any(factor in str(risk_factors).lower() for factor in ["suicide", "kill", "death"]):
            crisis_type = CrisisType.SUICIDE_IDEATION
        elif any(factor in str(risk_factors).lower() for factor in ["hurt", "cut", "harm"]):
            crisis_type = CrisisType.SELF_HARM
        
        # Map risk score to risk level
        risk_score = crisis_data["risk_score"]
        if risk_score >= 9:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 7:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 5:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        crisis_alert = CrisisAlert(
            user_id=user_id,
            session_id=session_id,
            crisis_type=crisis_type,
            risk_level=risk_level,
            confidence_score=risk_score,
            detected_indicators=risk_factors,
            status="pending"
        )
        
        self.db.add(crisis_alert)
        self.db.commit()
    
    async def process_user_message(self, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
        """Main method to process user message through the AI workflow"""
        # Load Session
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        # Compute next message_order
        next_order = (session.total_messages or 0) + 1

        # Save user message
        db_message = ChatMessage(
            session_id=session_id,
            content=message,
            role=MessageRole.USER,
            message_order=next_order
        )
        self.db.add(db_message)
        # Update session counters
        session.total_messages = next_order
        session.last_message_at = datetime.utcnow()
        self.db.commit()

        # 5. Initialize LangGraph state from DB messages
        messages = await self._get_user_conversation_history(user_id)
        # convert to HumanMessage list if needed, or just pass state["messages"] below
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_id": session_id
        }
        
        # Run through LangGraph workflow
        config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}
        result = await self.workflow.ainvoke(initial_state, config=config)
        
        # Extract AI response
        ai_message = result["messages"][-1]

        # Persist AI response as well
        next_order += 1
        db_ai = ChatMessage(
            session_id=session_id,
            content=ai_message.content,
            role=MessageRole.ASSISTANT,
            message_order=next_order
        )
        self.db.add(db_ai)
        session.total_messages = next_order
        self.db.commit()
        
        return {
            "response": ai_message.content,
            "intervention_type": result.get("intervention_type", "general"),
            "crisis_detected": result.get("crisis_assessment", {}).get("risk_score", 0) >= 7,
            "analysis": result.get("analysis", {}),
            "patterns": result.get("repetitive_patterns", [])
        }

# RAG Implementation for College-Specific Data
class CollegeKnowledgeRAG:
    """RAG system for college-specific information"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.llm = OpenRouterClient(
            api_key=self.api_key,
            model="deepseek/deepseek-chat-v3.1:free"
        )
        # Note: In production, implement vector database (Pinecone, Chroma, etc.)
        self.college_knowledge = {}
    
    async def query_college_data(self, query: str, college_id: str) -> Optional[str]:
        """Query college-specific information relevant to student's concern"""
        
        # Placeholder for RAG implementation
        # In production: 
        # 1. Embed the query
        # 2. Search vector database for relevant college documents
        # 3. Retrieve relevant chunks
        # 4. Generate response with context
        
        college_context_prompt = f"""
        Based on the college knowledge base for {college_id}, provide relevant information for:
        Query: "{query}"
        
        Focus on:
        - Academic policies and deadlines
        - Campus resources and support services  
        - Mental health services available
        - Academic accommodations
        - Exam schedules and stress periods
        
        If no relevant information is found, return "No relevant college information found."
        """
        
        response = await self.llm.ainvoke([SystemMessage(content=college_context_prompt)])
        
        if "no relevant" in response.content.lower():
            return None
            
        return response.content

# Integration function for chat routes
async def process_ai_conversation(
    db: Session,
    user_id: str, 
    session_id: str,
    message: str
) -> Dict[str, Any]:
    """Main function to process AI conversation - call this from your chat routes"""
    
    agent = EmotionalSupportAgent(db)
    rag = CollegeKnowledgeRAG()
    
    # Get user's college for RAG context
    user = db.query(User).filter(User.id == user_id).first()
    college_id = user.college_id if user else None
    
    # Check if college-specific information might be relevant
    college_info = None
    if college_id and any(keyword in message.lower() for keyword in 
                         ['exam', 'deadline', 'grade', 'professor', 'course', 'assignment']):
        college_info = await rag.query_college_data(message, college_id)
    
    # Process through AI agent
    result = await agent.process_user_message(user_id, session_id, message)
    
    # Add college context if relevant
    if college_info:
        result["response"] += f"\n\n**Relevant Campus Information:**\n{college_info}"
        result["college_context_provided"] = True
    
    return result
