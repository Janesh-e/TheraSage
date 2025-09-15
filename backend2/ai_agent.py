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
from datetime import datetime
import time
from dotenv import load_dotenv

from crisis_alert_manager import CrisisAlertManager

load_dotenv()

from models import (
    User, ChatSession, ChatMessage, CrisisAlert,
    MessageRole, RiskLevel, CrisisType
)

class ConversationAnalysis(BaseModel):
    """Structure for conversation analysis results"""
    emotional_state: str
    risk_level: int # 0-10 scale
    context_depth: str # 'shallow', 'moderate', 'deep'
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

    async def ainvoke(self, messages: List, temperature: float = 0.7, max_tokens: int = 200):
        """Async invoke method with increased token limit for better responses"""
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

class SessionContextManager:
    """Manages session summaries and context optimization"""
    
    def __init__(self, llm_client: OpenRouterClient, db: Session):
        self.llm = llm_client
        self.db = db
    
    async def generate_session_summary(self, session_id: str, messages: List[ChatMessage]) -> str:
        """Generate an optimized summary of the session for context"""
        
        # Get recent messages from this session
        conversation_text = ""
        for msg in messages[-10:]:  # Last 10 messages for summary
            role = "Student" if msg.role == MessageRole.USER else "AI"
            conversation_text += f"{role}: {msg.content}\n"
        
        summary_prompt = f"""
Create a concise context summary for this counseling session. Focus on:

Conversation:
{conversation_text}

Extract and summarize ONLY:
1. Student's main concerns/issues (2-3 key points)
2. Emotional state and patterns
3. AI's key suggestions/interventions given
4. Any progress or recurring themes
5. Important context for future conversations

Keep it under 200 words. Be specific and actionable.
Format as bullet points for easy parsing.
"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=summary_prompt)], max_tokens=300)
            return response.content
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Session summary generation failed"
    
    async def update_session_summary(self, session_id: str):
        """Update the session summary in database"""
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return
        
        # Get all messages in this session
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.message_order).all()
        
        if len(messages) >= 4:  # Update summary after at least 4 messages
            summary = await self.generate_session_summary(session_id, messages)
            session.conversation_summary = summary
            self.db.commit()
    
    async def get_session_context(self, user_id: str, current_session_id: str) -> str:
        """Get optimized context from current and previous sessions"""
        
        # Get current session summary
        current_session = self.db.query(ChatSession).filter(
            ChatSession.id == current_session_id
        ).first()
        
        # Get recent messages from current session (last 6 for immediate context)
        recent_messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == current_session_id
        ).order_by(ChatMessage.message_order.desc()).limit(6).all()
        
        # Get summaries from previous sessions (last 3 sessions)
        previous_sessions = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.id != current_session_id,
            ChatSession.conversation_summary.isnot(None)
        ).order_by(ChatSession.last_message_at.desc()).limit(3).all()
        
        # Build context
        context = ""
        
        # Add previous session summaries
        if previous_sessions:
            context += "Previous sessions context:\n"
            for i, session in enumerate(previous_sessions, 1):
                context += f"Session {i}: {session.conversation_summary}\n"
        
        # Add current session summary if exists
        if current_session and current_session.conversation_summary:
            context += f"\nCurrent session summary: {current_session.conversation_summary}\n"
        
        # Add recent conversation
        if recent_messages:
            context += "\nRecent conversation:\n"
            for msg in reversed(recent_messages):
                role = "Student" if msg.role == MessageRole.USER else "AI"
                context += f"{role}: {msg.content}\n"
        
        return context

class EmotionalSupportAgent:
    """Enhanced AI agent for natural emotional support conversations"""

    def __init__(self, db: Session):
        self.db = db

        # Initialize crisis alert manager
        self.crisis_manager = CrisisAlertManager(db)
        
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
        
        # Context manager
        self.context_manager = SessionContextManager(self.llm, db)

        # Initialize memory for conversation state
        self.memory = MemorySaver()
        self.workflow = self._create_conversation_workflow()

    def _create_conversation_workflow(self) -> StateGraph:
        """Create simplified LangGraph workflow for conversation handling"""
        workflow = StateGraph(MessagesState)

        # Simplified workflow: analysis -> context -> routing -> response
        workflow.add_node("comprehensive_analysis", self._comprehensive_analysis)
        workflow.add_node("check_context_depth", self._check_context_depth)
        workflow.add_node("detect_patterns", self._detect_repetitive_patterns)
        workflow.add_node("generate_contextual_response", self._generate_contextual_response)
        workflow.add_node("provide_cbt_intervention", self._provide_cbt_intervention)
        workflow.add_node("handle_crisis_escalation", self._handle_crisis_escalation)

        # Define workflow edges
        workflow.add_edge(START, "comprehensive_analysis")
        workflow.add_edge("comprehensive_analysis", "check_context_depth")
        workflow.add_edge("check_context_depth", "detect_patterns")

        # Smart routing based on analysis
        workflow.add_conditional_edges(
            "detect_patterns",
            self._intelligent_routing,
            {
                "crisis": "handle_crisis_escalation",
                "cbt": "provide_cbt_intervention", 
                "respond": "generate_contextual_response"
            }
        )

        workflow.add_edge("handle_crisis_escalation", END)
        workflow.add_edge("provide_cbt_intervention", END)
        workflow.add_edge("generate_contextual_response", END)

        return workflow.compile(checkpointer=self.memory)

    async def _comprehensive_analysis(self, state: MessagesState) -> MessagesState:
        """Enhanced analysis that includes crisis assessment and cognitive patterns"""
        user_message = state["messages"][-1].content
        user_id = state.get("user_id")
        session_id = state.get("session_id")

        # Get optimized session context
        session_context = await self.context_manager.get_session_context(user_id, session_id)

        analysis_prompt = f"""
You are an expert mental health AI analyzing a student's message for comprehensive emotional support.

Student's message: "{user_message}"
Session context: {session_context[:500]}

Provide EXACTLY this JSON structure (no additional text):
{{
    "emotional_state": "(1-2 words: anxious/stressed/sad/overwhelmed/frustrated/hopeful/neutral/etc)",
    "urgency_level": (1-10 integer),
    "main_concerns": ["concern1", "concern2"],
    "cognitive_distortions": ["list any: all-or-nothing, catastrophizing, mind-reading, fortune-telling, emotional-reasoning, etc"],
    "risk_score": (0-10 integer),
    "risk_factors": ["list any detected risk keywords"],
    "immediate_action_needed": (true/false),
    "conversation_needs": "(question/support/advice/validation/cbt/crisis)",
    "response_tone": "(encouraging/validating/practical/gentle/urgent)"
}}

Focus on detecting:
- All-or-nothing thinking (words like "never", "always", "completely", "totally")
- Catastrophizing (worst-case scenario thinking)
- Risk factors (hopelessness, self-harm, suicide ideation etc)
- Specific emotional needs
"""
        analysis_response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)], temperature=0.3, max_tokens=300)
        try:
            state["analysis_raw"] = analysis_response
            analysis_data = json.loads(analysis_response.content)
            state["analysis"] = analysis_data
            state["analysis_path"] = "try"
        except Exception as e:
            print(f"Analysis error: {e}")
            state["analysis_path"] = "except"
            # Fallback analysis
            state["analysis"] = {
                "emotional_state": "stressed",
                "urgency_level": 3,
                "main_concerns": ["general stress"],
                "cognitive_distortions": [],
                "risk_score": 0,
                "risk_factors": [],
                "immediate_action_needed": False,
                "conversation_needs": "support",
                "response_tone": "encouraging"
            }

        return state

    async def _check_context_depth(self, state: MessagesState) -> MessagesState:
        """Evaluate conversation context and flow"""
        session_id = state.get("session_id")
        
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
        state["message_count"] = message_count

        return state

    async def _detect_repetitive_patterns(self, state: MessagesState) -> MessagesState:
        """Identify patterns but keep it simple"""
        user_id = state.get("user_id")
        
        # Get patterns from previous sessions
        recent_sessions = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.conversation_summary.isnot(None)
        ).limit(3).all()

        patterns_found = []
        if len(recent_sessions) >= 2:
            summaries = [session.conversation_summary for session in recent_sessions]
            combined_summary = " ".join(summaries)
            
            # Basic keyword-based pattern detection
            keywords = ["exam anxiety", "perfectionism", "study stress", "fear of failure", "overwhelmed"]
            for keyword in keywords:
                if keyword in combined_summary.lower():
                    patterns_found.append(keyword)
            
            patterns_found = patterns_found[:2]  # Limit to 2 patterns

        state["repetitive_patterns"] = patterns_found
        return state

    def _intelligent_routing(self, state: MessagesState) -> str:
        """Smart routing based on comprehensive analysis"""
        analysis = state.get("analysis", {})
        
        risk_score = analysis.get("risk_score", 0)
        risk_factors = analysis.get("risk_factors", [])
        cognitive_distortions = analysis.get("cognitive_distortions", [])
        immediate_action = analysis.get("immediate_action_needed", False)
        
        # Crisis path: high risk score OR immediate action needed OR risk factors present
        if risk_score >= 7 or immediate_action or risk_factors:
            return "crisis"
        
        # CBT path: cognitive distortions detected
        elif cognitive_distortions and len(cognitive_distortions) > 0:
            return "cbt"
        
        # Regular supportive response
        else:
            return "respond"

    async def _generate_contextual_response(self, state: MessagesState) -> MessagesState:
        """Generate contextual, varied responses using analysis data"""
        user_message = state["messages"][-1].content
        analysis = state.get("analysis", {})
        context_depth = state.get("context_depth", "shallow")
        message_count = state.get("message_count", 0)
        patterns = state.get("repetitive_patterns", [])
        
        # Get session context
        session_context = await self.context_manager.get_session_context(
            state.get("user_id"), 
            state.get("session_id")
        )

        # Extract key analysis parameters
        emotional_state = analysis.get("emotional_state", "neutral")
        main_concerns = analysis.get("main_concerns", [])
        conversation_needs = analysis.get("conversation_needs", "support")
        response_tone = analysis.get("response_tone", "encouraging")
        urgency_level = analysis.get("urgency_level", 3)

        # Create dynamic, contextual response prompt
        response_prompt = f"""
You're an empathetic AI counselor responding to a college student. Use ALL the provided context.

Student's message: "{user_message}"
Emotional state: {emotional_state}
Main concerns: {main_concerns}
Conversation needs: {conversation_needs}
Response tone needed: {response_tone}
Urgency level: {urgency_level}/10
Recurring patterns: {patterns}
Session context: {session_context[:300]}

Response Guidelines based on context:

IF emotional_state is "anxious/stressed/overwhelmed":
- Acknowledge the specific stress they're feeling
- Offer perspective or practical insights
- Avoid generic "it's normal" phrases

IF main_concerns include "exam/study/grades":
- Address study-related anxieties specifically
- Offer practical study perspectives
- Validate their academic concerns

IF conversation_needs is "validation":
- Focus on validating their experience
- Reflect their emotions back
- Show understanding of their specific situation

IF conversation_needs is "advice":
- Provide specific, actionable suggestions
- Be practical and concrete
- Offer strategies they can implement

IF conversation_needs is "support":
- Be encouraging and hopeful
- Share perspective that helps them feel less alone
- Build on their strengths

Response Structure (2-4 sentences max):
1. Specific acknowledgment (not generic)
2. Insight/perspective/validation relevant to their concern
3. Optional: gentle question OR encouragement OR practical tip

AVOID these phrases: "It's completely normal", "I understand", "Thank you for sharing"

Examples based on context:
- If stressed about exams: "Exam anxiety can make everything feel impossible, even when you're prepared. That fear of not being perfect is exhausting."
- If feeling inadequate: "Those thoughts telling you you're not good enough are really loud right now. But they're not facts about who you are."
- If seeking advice: "One thing that might help is breaking down what 'being prepared' actually looks like for you."

Keep it natural, specific, and contextual. Maximum 60 words.
"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=response_prompt)], max_tokens=180)
            response_content = self._post_process_response(response.content)
        except Exception as e:
            print(f"Error generating response: {e}")
            # Contextual fallback based on emotional state
            fallbacks = {
                "anxious": "That anxiety about your exams is really weighing on you.",
                "stressed": "You're carrying a lot of pressure right now.",
                "overwhelmed": "Everything feels like too much at once.",
                "frustrated": "This situation is really getting to you.",
                "sad": "You're going through a tough time.",
            }
            response_content = fallbacks.get(emotional_state, "Tell me more about what's going through your mind.")

        state["messages"].append(AIMessage(content=response_content))
        state["intervention_type"] = "contextual_response"
        return state

    async def _provide_cbt_intervention(self, state: MessagesState) -> MessagesState:
        """Provide specific CBT intervention based on detected cognitive distortions"""
        user_message = state["messages"][-1].content
        analysis = state.get("analysis", {})
        
        emotional_state = analysis.get("emotional_state", "neutral")
        cognitive_distortions = analysis.get("cognitive_distortions", [])
        main_concerns = analysis.get("main_concerns", [])

        cbt_prompt = f"""
You're a CBT-trained counselor addressing specific cognitive distortions.

Student's message: "{user_message}"
Emotional state: {emotional_state}
Detected cognitive distortions: {cognitive_distortions}
Main concerns: {main_concerns}

For each distortion, provide a targeted CBT intervention:

IF "all-or-nothing" detected:
- Address the black/white thinking specifically
- Offer middle-ground perspective
- Example: "I hear you saying you 'never' do well - but what about the gray areas? What would 'good enough' look like?"

IF "catastrophizing" detected:
- Challenge worst-case scenario thinking
- Bring them back to realistic outcomes
- Example: "Your mind is jumping to the worst possible outcome. What's more likely to actually happen?"

IF "fortune-telling" detected:
- Question their ability to predict the future
- Focus on present moment control
- Example: "You're predicting failure before it happens. What can you control right now?"

Structure your response (2-3 sentences):
1. Validate their feeling briefly
2. Gently challenge the specific distortion
3. Offer a reframe or coping strategy

Specific to their concern. Be conversational but therapeutic. Maximum 70 words.
"""

        try:
            cbt_response = await self.cbt_llm.ainvoke([HumanMessage(content=cbt_prompt)], max_tokens=200)
            response_content = cbt_response.content
        except:
            # Fallback CBT response based on common distortions
            if "all-or-nothing" in cognitive_distortions:
                response_content = "I hear you saying 'never' - but what about the times you did okay? Perfect isn't the only option here."
            elif "catastrophizing" in cognitive_distortions:
                response_content = "Your mind is jumping to worst-case scenarios. What's actually most likely to happen?"
            else:
                response_content = "Those thoughts feel very real, but they might not be telling you the whole truth about yourself."

        state["messages"].append(AIMessage(content=response_content))
        state["intervention_type"] = "cbt_intervention"
        return state

    async def _handle_crisis_escalation(self, state: MessagesState) -> MessagesState:
        """Enhanced crisis handling with automatic therapist assignment"""
        
        analysis = state.get("analysis", {})
        risk_factors = analysis.get("risk_factors", [])
        user_id = state.get("user_id")
        session_id = state.get("session_id")
        
        try:
            # Create crisis alert with automatic therapist assignment
            crisis_result = await self.crisis_manager.create_crisis_alert_with_assignment(
                user_id, session_id, analysis
            )
            
            # Enhanced crisis response based on assignment result
            if crisis_result["assigned_therapist_id"]:
                if crisis_result["therapist_session_id"]:
                    # Emergency session created
                    crisis_resources = f"""I'm genuinely concerned about you right now and I've immediately connected you with professional help.

🚨 **Immediate Support Activated:**
• A crisis counselor has been automatically assigned to you
• An emergency session has been scheduled within the next 30-60 minutes
• You'll receive session details shortly via email

**Right Now - Immediate Crisis Support:**
• Crisis Hotline: 988 (24/7)
• Crisis Text Line: Text HOME to 741741
• Emergency: 911

**Campus Resources:**
• Campus Counseling Center (immediate appointment)
• Campus Safety

Your crisis counselor will reach out to you very soon. You don't have to face this alone - help is on the way.

Can you stay safe until your counselor contacts you? Let me know if you need immediate emergency assistance."""

                else:
                    # Therapist assigned but no emergency session
                    crisis_resources = f"""I'm concerned about what you're going through and I've connected you with professional support.

🏥 **Professional Support Assigned:**
• A qualified counselor has been assigned to your case
• They will review your situation and contact you within 2-4 hours
• You'll receive contact information shortly

**Immediate Crisis Support (Available Now):**
• Crisis Hotline: 988 (24/7)
• Crisis Text Line: Text HOME to 741741
• Emergency: 911

**Campus Resources:**
• Campus Counseling Center
• Campus Safety

Help is available right now if you need it. Can you tell me how you're feeling at this moment?"""
            
            else:
                # No therapist available - emergency protocol
                crisis_resources = f"""I'm very concerned about you right now. While our counselors are currently unavailable, immediate help is still accessible.

🚨 **Immediate Crisis Support (Available 24/7):**
• Crisis Hotline: 988
• Crisis Text Line: Text HOME to 741741
• Emergency: 911

**Campus Emergency Resources:**
• Campus Counseling Center Emergency Line
• Campus Safety
• Local Emergency Room

I've flagged your situation as high priority and you'll be contacted as soon as a counselor becomes available.

Please don't hesitate to use the crisis hotline or call 911 if you need immediate help. Can you stay safe right now?"""
            
            # Store crisis result in state for logging
            state["crisis_result"] = crisis_result
            
        except Exception as e:
            print(f"Crisis alert creation failed: {e}")
            # Fallback crisis response
            crisis_resources = f"""I'm genuinely concerned about you right now. Please reach out for immediate support:

🚨 **Immediate Crisis Support:**
• Crisis Hotline: 988 (24/7)  
• Crisis Text Line: Text HOME to 741741
• Emergency: 911

🏥 **Campus Resources:**
• Campus Counseling Center (immediate appointment)
• Campus Safety

You don't have to face this alone. These feelings can change, and help is available right now.

Can you tell me what you're experiencing at this moment?"""
            
            state["crisis_result"] = {"error": str(e)}
        
        state["messages"].append(AIMessage(content=crisis_resources))
        state["intervention_type"] = "crisis_escalation"
        
        return state

    def _post_process_response(self, response: str) -> str:
        """Clean up and improve AI response"""
        # Remove common repetitive phrases
        repetitive_starts = [
            "It's completely normal",
            "It's totally normal", 
            "I understand that",
            "Thank you for sharing",
            "I hear what you're saying"
        ]
        
        cleaned = response.strip()
        
        # Remove repetitive beginnings
        for phrase in repetitive_starts:
            if cleaned.startswith(phrase):
                # Find the first period and remove everything before it
                period_index = cleaned.find('.')
                if period_index != -1 and period_index < 50:  # Only if period is within first 50 chars
                    cleaned = cleaned[period_index + 1:].strip()
                break
        
        # Ensure response isn't too generic
        if len(cleaned) < 10:
            cleaned = "Tell me more about that."
        
        return cleaned

    async def _create_crisis_alert(self, user_id: str, session_id: str, analysis: Dict):
        """Create crisis alert record in database"""
        risk_factors = analysis.get("risk_factors", [])
        risk_score = analysis.get("risk_score", 0)
        
        crisis_type = CrisisType.SEVERE_DEPRESSION  # Default

        if any(factor in str(risk_factors).lower() for factor in ["suicide", "kill", "death"]):
            crisis_type = CrisisType.SUICIDE_IDEATION
        elif any(factor in str(risk_factors).lower() for factor in ["hurt", "cut", "harm"]):
            crisis_type = CrisisType.SELF_HARM

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
        start_time = time.time()
        
        # 1. UPDATE USER LAST ACTIVITY
        self._update_user_activity(user_id)
        
        # Load Session
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Compute next message_order
        next_order = (session.total_messages or 0) + 1

        # 2. SAVE USER MESSAGE WITH ENHANCED FIELDS
        user_db_message = ChatMessage(
            session_id=session_id,
            content=message,
            role=MessageRole.USER,
            message_order=next_order,
            created_at=datetime.utcnow()
        )

        self.db.add(user_db_message)

        # Update session counters
        session.total_messages = next_order
        session.last_message_at = datetime.utcnow()
        self.db.commit()

        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_id": session_id
        }

        # Run through LangGraph workflow
        config = {"configurable": {"thread_id": f"{user_id}_{session_id}"}}
        try:
            result = await self.workflow.ainvoke(initial_state, config=config)
        except Exception as workflow_error:
            print(f"LangGraph workflow error: {workflow_error}")
            # Create a simple fallback response
            from langchain_core.messages import AIMessage
            result = {
                "messages": [AIMessage(content="I'm here to listen and support you. Thank you for sharing with me. How are you feeling right now? 💜")],
                "analysis": {
                    "emotional_state": "neutral",
                    "urgency_level": 3,
                    "main_concerns": [],
                    "cognitive_distortions": [],
                    "risk_factors": []
                },
                "crisis_result": {},
                "repetitive_patterns": []
            }

        # Extract AI response and analysis
        ai_message = result["messages"][-1]
        analysis = result.get("analysis", {})
        crisis_result = result.get("crisis_result", {})
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # 3. SAVE AI MESSAGE WITH FULL METADATA
        next_order += 1
        ai_db_message = ChatMessage(
            session_id=session_id,
            content=ai_message.content,
            role=MessageRole.ASSISTANT,
            message_order=next_order,
            created_at=datetime.utcnow(),
            
            # AI Response Metadata
            ai_model_used="deepseek/deepseek-chat-v3.1:free",
            response_time_ms=response_time_ms,
            confidence_score=analysis.get("urgency_level", 5) / 10.0,  # Convert to 0-1 scale
        )

        self.db.add(ai_db_message)

        # 4. UPDATE USER MESSAGE WITH RISK ANALYSIS (retroactively)
        if analysis:
            user_db_message.risk_indicators = {
                "cognitive_distortions": analysis.get("cognitive_distortions", []),
                "risk_factors": analysis.get("risk_factors", []),
                "detected_patterns": result.get("repetitive_patterns", [])
            }
            user_db_message.sentiment_score = self._calculate_sentiment_score(analysis)
            user_db_message.emotion_analysis = {
                "emotional_state": analysis.get("emotional_state", "neutral"),
                "urgency_level": analysis.get("urgency_level", 3),
                "main_concerns": analysis.get("main_concerns", [])
            }

        # 5. UPDATE SESSION WITH RISK ASSESSMENT
        self._update_session_risk_assessment(session, analysis)

        # Final commit
        session.total_messages = next_order
        self.db.commit()

        # 6. UPDATE SESSION SUMMARY
        if next_order % 6 == 0:  # Update summary every 6 messages
            await self.context_manager.update_session_summary(session_id)

        return {
            "response": ai_message.content,
            "intervention_type": result.get("intervention_type", "contextual_response"),
            "crisis_detected": analysis.get("risk_score", 0) >= 7,
            "analysis": analysis,
            "patterns": result.get("repetitive_patterns", []),
            "response_time_ms": response_time_ms,
            "crisis_alert_id": crisis_result.get("crisis_alert_id"),
            "assigned_therapist_id": crisis_result.get("assigned_therapist_id"), 
            "therapist_session_id": crisis_result.get("therapist_session_id"),
            "auto_escalated": crisis_result.get("auto_escalated", False)
        }
    
    def _update_user_activity(self, user_id: str):
        """Update user's last activity timestamp"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_activity = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            print(f"Error updating user activity: {e}")

    def _calculate_sentiment_score(self, analysis: Dict) -> float:
        """Calculate sentiment score based on analysis (-1.0 to 1.0)"""
        emotional_state = analysis.get("emotional_state", "neutral").lower()
        urgency_level = analysis.get("urgency_level", 5)
        
        # Sentiment mapping
        positive_emotions = ["hopeful", "calm", "peaceful", "happy", "confident"]
        negative_emotions = ["anxious", "stressed", "sad", "overwhelmed", "frustrated", "depressed"]
        
        if any(emotion in emotional_state for emotion in positive_emotions):
            base_sentiment = 0.3
        elif any(emotion in emotional_state for emotion in negative_emotions):
            base_sentiment = -0.3
        else:
            base_sentiment = 0.0
        
        # Adjust based on urgency (higher urgency = more negative)
        urgency_adjustment = (urgency_level - 5) * -0.1
        
        # Clamp to -1.0 to 1.0 range
        final_sentiment = max(-1.0, min(1.0, base_sentiment + urgency_adjustment))
        
        return final_sentiment

    def _update_session_risk_assessment(self, session: ChatSession, analysis: Dict):
        """Update session with risk assessment data"""
        if not analysis:
            return
            
        risk_score = analysis.get("risk_score", 0)
        cognitive_distortions = analysis.get("cognitive_distortions", [])
        risk_factors = analysis.get("risk_factors", [])
        
        # Update risk score
        session.risk_score = float(risk_score)
        session.last_risk_assessment = datetime.utcnow()
        
        # Update risk level based on analysis
        if risk_score >= 8 or risk_factors:
            if risk_score >= 9:
                session.current_risk_level = RiskLevel.CRITICAL
            elif risk_score >= 7:
                session.current_risk_level = RiskLevel.HIGH
            else:
                session.current_risk_level = RiskLevel.MEDIUM
        elif cognitive_distortions or risk_score >= 4:
            session.current_risk_level = RiskLevel.MEDIUM
        else:
            session.current_risk_level = RiskLevel.LOW

# Integration function for chat routes
async def process_ai_conversation(
    db: Session,
    user_id: str,
    session_id: str,
    message: str
) -> Dict[str, Any]:
    """Main function to process AI conversation - improved version"""
    agent = EmotionalSupportAgent(db)
    
    # Process through enhanced AI agent
    result = await agent.process_user_message(user_id, session_id, message)
    
    return result