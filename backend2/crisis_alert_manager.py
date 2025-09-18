import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from models import (
    CrisisAlert, User, ChatSession, ChatMessage, Therapist, TherapistSession,
    RiskLevel, CrisisType, SessionStatus, TherapistStatus, TherapistRole
)

class CrisisAlertManager:
    """Enhanced crisis alert manager with automatic therapist assignment"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_crisis_alert_with_assignment(
        self, 
        user_id: str, 
        session_id: str, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create crisis alert and automatically assign best available therapist
        """
        
        # 1. Create the crisis alert
        crisis_alert = await self._create_enhanced_crisis_alert(
            user_id, session_id, analysis
        )
        
        # 2. Find and assign best available therapist
        assigned_therapist = await self._assign_best_available_therapist(
            crisis_alert, analysis
        )
        
        # 3. Create therapist session if high/critical risk
        '''therapist_session = None
        if crisis_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            therapist_session = await self._create_emergency_session(
                crisis_alert, assigned_therapist
            )'''
        
        # 4. Send notifications
        await self._send_crisis_notifications(
            crisis_alert, assigned_therapist, None
        )
        
        return {
            "crisis_alert_id": str(crisis_alert.id),
            "assigned_therapist_id": assigned_therapist["id"] if assigned_therapist else None,
            "therapist_session_id": None,
            "risk_level": crisis_alert.risk_level.value,
            "auto_escalated": crisis_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        }
    
    async def _create_enhanced_crisis_alert(
        self, 
        user_id: str, 
        session_id: str, 
        analysis: Dict[str, Any]
    ) -> CrisisAlert:
        """Create detailed crisis alert with context"""
        
        # Get user and session info
        user = self.db.query(User).filter(User.id == user_id).first()
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        
        # Extract analysis data
        risk_factors = analysis.get("risk_factors", [])
        risk_score = analysis.get("risk_score", 0)
        main_concerns = analysis.get("main_concerns", [])
        
        # Determine crisis type from risk factors and concerns
        crisis_type = self._determine_crisis_type(risk_factors, main_concerns)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(risk_score, risk_factors, analysis)
        
        # Get trigger message context
        trigger_message = None
        context_messages = []
        
        if session:
            # Get the most recent user message as trigger
            recent_messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.message_order.desc()).limit(5).all()
            
            if recent_messages:
                trigger_message = recent_messages[0].content  # Most recent message
                context_messages = [msg.content for msg in reversed(recent_messages[1:])]
        
        # Create crisis alert
        crisis_alert = CrisisAlert(
            user_id=user_id,
            session_id=session_id,
            crisis_type=crisis_type,
            risk_level=risk_level,
            confidence_score=min(risk_score, 10.0),
            trigger_message=trigger_message,
            context_messages="\n".join(context_messages),
            detected_indicators={
                "risk_factors": risk_factors,
                "main_concerns": main_concerns,
                "cognitive_distortions": analysis.get("cognitive_distortions", []),
                "emotional_state": analysis.get("emotional_state", "unknown"),
                "urgency_level": analysis.get("urgency_level", 5)
            },
            status="pending",
            escalated_to_human=risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            auto_resources_sent=False,
            response_actions={
                "ai_detected_at": datetime.utcnow().isoformat(),
                "analysis_version": "v2.0",
                "auto_escalation": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            }
        )
        
        self.db.add(crisis_alert)
        self.db.commit()
        self.db.refresh(crisis_alert)
        
        return crisis_alert
    
    def _determine_crisis_type(self, risk_factors: List[str], main_concerns: List[str]) -> CrisisType:
        """Determine crisis type from detected factors"""
        
        # Convert to lowercase for matching
        factors_text = " ".join(risk_factors + main_concerns).lower()
        
        # Priority order for crisis type determination
        if any(word in factors_text for word in ["suicide", "kill", "death", "die", "end it all"]):
            return CrisisType.SUICIDE_IDEATION
        elif any(word in factors_text for word in ["cut", "hurt myself", "self-harm", "harm myself"]):
            return CrisisType.SELF_HARM
        elif any(word in factors_text for word in ["panic", "anxiety attack", "can't breathe"]):
            return CrisisType.ANXIETY_PANIC
        elif any(word in factors_text for word in ["drugs", "alcohol", "substance", "drinking"]):
            return CrisisType.SUBSTANCE_ABUSE
        elif any(word in factors_text for word in ["eating", "food", "weight", "starving"]):
            return CrisisType.EATING_DISORDER
        else:
            return CrisisType.SEVERE_DEPRESSION
    
    def _calculate_risk_level(self, risk_score: int, risk_factors: List[str], analysis: Dict) -> RiskLevel:
        """Calculate comprehensive risk level"""
        
        # Base risk from score
        if risk_score >= 9:
            base_risk = RiskLevel.CRITICAL
        elif risk_score >= 7:
            base_risk = RiskLevel.HIGH
        elif risk_score >= 4:
            base_risk = RiskLevel.MEDIUM
        else:
            base_risk = RiskLevel.LOW
        
        # Escalate if immediate action needed
        if analysis.get("immediate_action_needed", False):
            if base_risk == RiskLevel.MEDIUM:
                base_risk = RiskLevel.HIGH
            elif base_risk == RiskLevel.LOW:
                base_risk = RiskLevel.MEDIUM
        
        # Escalate if specific risk factors present
        high_risk_indicators = ["suicide", "kill", "death", "hurt myself", "end it all"]
        if any(indicator in " ".join(risk_factors).lower() for indicator in high_risk_indicators):
            if base_risk in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                base_risk = RiskLevel.HIGH
        
        return base_risk
    
    async def _assign_best_available_therapist(
        self, 
        crisis_alert: CrisisAlert, 
        analysis: Dict
    ) -> Optional[Dict[str, Any]]:
        """Find and assign the best available therapist"""
        
        # Get user's college for college-specific assignment
        user = self.db.query(User).filter(User.id == crisis_alert.user_id).first()
        if not user:
            return None
        
        college_id = user.college_id
        
        # Find available therapists for this college
        available_therapists = self.db.query(Therapist).filter(
            and_(
                Therapist.college_id == college_id,
                Therapist.is_active == True,
                Therapist.status.in_([TherapistStatus.ACTIVE, TherapistStatus.BUSY])
            )
        ).all()
        
        if not available_therapists:
            # No therapists available - log this for admin attention
            crisis_alert.response_actions.update({
                "no_therapists_available": datetime.utcnow().isoformat(),
                "college_id": college_id
            })
            self.db.commit()
            return None
        
        # Calculate workload for each therapist
        therapist_workloads = []
        for therapist in available_therapists:
            
            # Count active crisis alerts assigned to this therapist
            active_crisis_count = self.db.query(CrisisAlert).filter(
                and_(
                    CrisisAlert.assigned_therapist_id == therapist.id,
                    CrisisAlert.status.in_(["pending", "acknowledged", "escalated"])
                )
            ).count()
            
            # Count active therapist sessions
            active_session_count = self.db.query(TherapistSession).filter(
                and_(
                    TherapistSession.external_therapist_id == str(therapist.id),
                    TherapistSession.status.in_([SessionStatus.SCHEDULED, SessionStatus.IN_PROGRESS])
                )
            ).count()
            
            # Calculate specialization match score
            specialization_score = self._calculate_specialization_match(
                therapist, crisis_alert.crisis_type, analysis
            )
            
            # Preference for crisis specialists for high-risk cases
            role_priority = 1
            if crisis_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                if therapist.role == TherapistRole.CRISIS_SPECIALIST:
                    role_priority = 3
                elif therapist.role in [TherapistRole.PSYCHOLOGIST, TherapistRole.PSYCHIATRIST]:
                    role_priority = 2
            
            # Calculate total score (lower is better for assignment)
            total_workload = active_crisis_count * 2 + active_session_count
            assignment_score = total_workload - (specialization_score * role_priority)
            
            therapist_workloads.append({
                "therapist": therapist,
                "workload": total_workload,
                "specialization_score": specialization_score,
                "role_priority": role_priority,
                "assignment_score": assignment_score
            })
        
        # Sort by assignment score (lower is better)
        therapist_workloads.sort(key=lambda x: x["assignment_score"])
        
        # Assign to the best available therapist
        best_therapist_data = therapist_workloads[0]
        best_therapist = best_therapist_data["therapist"]
        
        # Update crisis alert with assignment
        crisis_alert.assigned_therapist_id = best_therapist.id
        crisis_alert.human_reviewer_id = str(best_therapist.id)
        crisis_alert.status = "acknowledged" if crisis_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "pending"
        
        # Update response actions
        crisis_alert.response_actions.update({
            "auto_assigned_at": datetime.utcnow().isoformat(),
            "assigned_therapist_id": str(best_therapist.id),
            "therapist_name": best_therapist.name,
            "therapist_role": best_therapist.role.value,
            "assignment_reason": f"Lowest workload ({best_therapist_data['workload']}) with specialization match ({best_therapist_data['specialization_score']})"
        })
        
        if crisis_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            crisis_alert.acknowledged_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "id": str(best_therapist.id),
            "name": best_therapist.name,
            "role": best_therapist.role.value,
            "email": best_therapist.email,
            "workload": best_therapist_data["workload"],
            "specialization_score": best_therapist_data["specialization_score"]
        }
    
    def _calculate_specialization_match(self, therapist: Therapist, crisis_type: CrisisType, analysis: Dict) -> float:
        """Calculate how well a therapist's specialization matches the crisis"""
        
        # Get therapist specializations (assuming JSON string)
        specializations = []
        if therapist.specializations:
            try:
                import json
                specializations = json.loads(therapist.specializations)
            except:
                specializations = therapist.specializations.split(",") if therapist.specializations else []
        
        specializations_text = " ".join(specializations).lower()
        
        # Crisis type matching
        crisis_matches = {
            CrisisType.SUICIDE_IDEATION: ["suicide", "crisis", "emergency", "ideation"],
            CrisisType.SELF_HARM: ["self-harm", "cutting", "trauma", "crisis"],
            CrisisType.SEVERE_DEPRESSION: ["depression", "mood", "cognitive", "therapy"],
            CrisisType.ANXIETY_PANIC: ["anxiety", "panic", "phobia", "stress"],
            CrisisType.SUBSTANCE_ABUSE: ["substance", "addiction", "recovery", "abuse"],
            CrisisType.EATING_DISORDER: ["eating", "body", "nutrition", "disorder"]
        }
        
        score = 0.0
        crisis_keywords = crisis_matches.get(crisis_type, [])
        
        for keyword in crisis_keywords:
            if keyword in specializations_text:
                score += 1.0
        
        # Bonus for general crisis experience
        if any(word in specializations_text for word in ["crisis", "emergency", "trauma"]):
            score += 0.5
        
        # Bonus for CBT if cognitive distortions detected
        if analysis.get("cognitive_distortions") and "cbt" in specializations_text:
            score += 0.3
        
        return score
    
    async def _create_emergency_session(
        self, 
        crisis_alert: CrisisAlert, 
        therapist_data: Optional[Dict]
    ) -> Optional[TherapistSession]:
        """Create emergency therapist session for high-risk cases"""
        
        if not therapist_data or crisis_alert.risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return None
        
        # Calculate urgency-based scheduling
        if crisis_alert.risk_level == RiskLevel.CRITICAL:
            # Schedule within 30 minutes for critical cases
            scheduled_for = datetime.utcnow() + timedelta(minutes=30)
            duration = 60  # 60 minutes for critical
        else:
            # Schedule within 2 hours for high risk
            scheduled_for = datetime.utcnow() + timedelta(hours=2)
            duration = 50  # Standard 50 minutes
        
        therapist_session = TherapistSession(
            user_id=crisis_alert.user_id,
            crisis_alert_id=crisis_alert.id,
            session_type="crisis",
            urgency_level=crisis_alert.risk_level,
            requested_at=datetime.utcnow(),
            scheduled_for=scheduled_for,
            duration_minutes=duration,
            status=SessionStatus.SCHEDULED,
            external_therapist_id=therapist_data["id"],
            meeting_link=f"https://meet.therasage.com/emergency/{str(crisis_alert.id)[:8]}",
            follow_up_needed=False
        )
        
        self.db.add(therapist_session)
        
        # Update crisis alert
        crisis_alert.status = "escalated"
        crisis_alert.escalated_to_human = True
        crisis_alert.response_actions.update({
            "emergency_session_created": datetime.utcnow().isoformat(),
            "session_scheduled_for": scheduled_for.isoformat(),
            "therapist_id": therapist_data["id"]
        })
        
        self.db.commit()
        self.db.refresh(therapist_session)
        
        return therapist_session
    
    async def _send_crisis_notifications(
        self, 
        crisis_alert: CrisisAlert, 
        therapist_data: Optional[Dict],
        therapist_session: Optional[TherapistSession]
    ):
        """Send notifications to relevant parties"""
        
        # This is a placeholder for notification system
        # In a real implementation, you would integrate with:
        # - Email service
        # - SMS service  
        # - Push notifications
        # - Slack/Teams integration
        
        notifications_sent = []
        
        if therapist_data:
            # Notify assigned therapist
            notifications_sent.append({
                "type": "therapist_assignment",
                "recipient": therapist_data["email"],
                "urgency": crisis_alert.risk_level.value,
                "message": f"New crisis alert assigned - {crisis_alert.crisis_type.value}"
            })
        
        '''if therapist_session:
            # Notify about emergency session
            notifications_sent.append({
                "type": "emergency_session",
                "recipient": therapist_data["email"],
                "session_time": therapist_session.scheduled_for,
                "meeting_link": therapist_session.meeting_link
            })'''
        
        # Notify admin for critical cases
        if crisis_alert.risk_level == RiskLevel.CRITICAL:
            notifications_sent.append({
                "type": "admin_alert",
                "urgency": "critical",
                "crisis_id": str(crisis_alert.id)
            })
        
        # Update crisis alert with notification info
        crisis_alert.response_actions.update({
            "notifications_sent": notifications_sent,
            "notification_timestamp": datetime.utcnow().isoformat()
        })
        
        self.db.commit()
        
        print(f"🚨 Crisis notifications sent: {len(notifications_sent)}")
        for notification in notifications_sent:
            print(f"   • {notification['type']}: {notification.get('recipient', 'admin')}")

    def get_therapist_availability_stats(self, college_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current therapist availability statistics"""
        
        query = self.db.query(Therapist).filter(Therapist.is_active == True)
        if college_id:
            query = query.filter(Therapist.college_id == college_id)
        
        therapists = query.all()
        
        availability_stats = {
            "total_therapists": len(therapists),
            "active_therapists": 0,
            "busy_therapists": 0,
            "offline_therapists": 0,
            "crisis_specialists": 0,
            "average_workload": 0.0,
            "therapist_details": []
        }
        
        total_workload = 0
        
        for therapist in therapists:
            # Count current assignments
            active_crisis = self.db.query(CrisisAlert).filter(
                and_(
                    CrisisAlert.assigned_therapist_id == therapist.id,
                    CrisisAlert.status.in_(["pending", "acknowledged", "escalated"])
                )
            ).count()
            
            active_sessions = self.db.query(TherapistSession).filter(
                and_(
                    TherapistSession.external_therapist_id == str(therapist.id),
                    TherapistSession.status.in_([SessionStatus.SCHEDULED, SessionStatus.IN_PROGRESS])
                )
            ).count()
            
            workload = active_crisis + active_sessions
            total_workload += workload
            
            # Update availability stats
            if therapist.status == TherapistStatus.ACTIVE:
                availability_stats["active_therapists"] += 1
            elif therapist.status == TherapistStatus.BUSY:
                availability_stats["busy_therapists"] += 1
            else:
                availability_stats["offline_therapists"] += 1
            
            if therapist.role == TherapistRole.CRISIS_SPECIALIST:
                availability_stats["crisis_specialists"] += 1
            
            availability_stats["therapist_details"].append({
                "id": str(therapist.id),
                "name": therapist.name,
                "role": therapist.role.value,
                "status": therapist.status.value,
                "active_crisis_count": active_crisis,
                "active_session_count": active_sessions,
                "total_workload": workload
            })
        
        if len(therapists) > 0:
            availability_stats["average_workload"] = round(total_workload / len(therapists), 2)
        
        return availability_stats