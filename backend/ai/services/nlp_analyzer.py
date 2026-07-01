import re
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.chatbot import ChatbotMessage
from models.features import RiskScore
from models.employees import Employee

STRESS_KEYWORDS = ["épuisé", "fatigué", "stress", "trop de travail", "n'en peux plus", "pression", "débordé", "insomnie", "angoisse", "surmenage", "bout du rouleau", "craquer"]
DISENGAGEMENT_KEYWORDS = ["démission", "partir", "quitter", "ennui", "dégoût", "inutile", "départ", "changer d'entreprise", "autre opportunité", "recherche", "cv"]
POSITIVE_KEYWORDS = ["super", "motivé", "merci", "heureux", "satisfait", "j'adore", "passionnant", "génial", "content", "top"]

def analyze_employee_sentiment(db: Session, user_id: int, days_back: int = 7):
    # Fetch messages sent by the user in the last N days
    since = datetime.now() - timedelta(days=days_back)
    messages = db.query(ChatbotMessage).filter(
        ChatbotMessage.user_id == user_id,
        ChatbotMessage.sender == "user",
        ChatbotMessage.created_at >= since
    ).all()

    if not messages:
        return None

    stress_score = 0
    disengagement_score = 0
    positive_score = 0
    total_words = 0

    for msg in messages:
        if not msg.message:
            continue
        text = msg.message.lower()
        words = len(text.split())
        total_words += words
        
        for kw in STRESS_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                stress_score += 15
                
        for kw in DISENGAGEMENT_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                disengagement_score += 20
                
        for kw in POSITIVE_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                positive_score += 10

    if total_words == 0:
        return None
        
    # Cap scores to 100
    final_stress = min(100, max(0, stress_score - positive_score))
    final_disengagement = min(100, max(0, disengagement_score - positive_score))
    
    return {
        "nlp_stress": final_stress,
        "nlp_disengagement": final_disengagement,
        "analyzed_messages": len(messages)
    }

def run_nightly_nlp_pipeline(db: Session):
    """
    To be run as a cron job or background task.
    Analyzes chatbot logs and updates RiskScore.
    """
    employees = db.query(Employee).filter(Employee.status == "active").all()
    count = 0
    for emp in employees:
        res = analyze_employee_sentiment(db, emp.user_id)
        if res and res["analyzed_messages"] > 0:
            # Update the latest RiskScore or create one if it doesn't exist
            latest_risk = db.query(RiskScore).filter(RiskScore.employee_id == emp.user_id).order_by(RiskScore.generated_at.desc()).first()
            if latest_risk:
                # Blend the NLP score with the existing ML score
                # Simple blending: 70% ML, 30% NLP
                if latest_risk.burnout_risk is not None:
                    latest_risk.burnout_risk = (latest_risk.burnout_risk * 0.7) + (res["nlp_stress"] * 0.3)
                if latest_risk.engagement_risk is not None:
                    # engagement_risk tracks "disengagement" risk level
                    latest_risk.engagement_risk = (latest_risk.engagement_risk * 0.7) + (res["nlp_disengagement"] * 0.3)
                if latest_risk.turnover_risk is not None:
                    latest_risk.turnover_risk = (latest_risk.turnover_risk * 0.8) + (res["nlp_disengagement"] * 0.2)
                
                db.add(latest_risk)
                count += 1
                
    db.commit()
    return count
