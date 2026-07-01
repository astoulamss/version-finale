"""
Module Chatbot / Assistant IA RH
=================================
Endpoints :
  POST   /api/chatbot/conversations             — Démarrer une conversation
  GET    /api/chatbot/conversations             — Lister SES conversations (ou toutes si admin)
  GET    /api/chatbot/conversations/{id}        — Détail d'une conversation + messages
  DELETE /api/chatbot/conversations/{id}/close  — Clore une conversation
  POST   /api/chatbot/conversations/{id}/messages — Envoyer un message, recevoir la réponse IA

  GET    /api/chatbot/logs                      — Logs d'audit (admin only)
  GET    /api/chatbot/admin/conversations       — Toutes les conversations (admin only)
"""

import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.security import get_current_user, require_role
from database.db import get_db
from models.chatbot import ChatbotConversation, ChatbotLog, ChatbotMessage
from models.user import RoleEnum
from schemas.chatbot import (
    ChatbotLogOut,
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
    MessageOut,
    MessageSend,
)

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


# ─── Bot IA simulé ──────────────────────────────────────────────────────────

_RESPONSES = [
    (
        r"cong[eé]|vacance|absence",
        (
            "Votre solde de congés est disponible dans la section «\u202fCongés\u202f». "
            "Pour toute demande, rendez-vous dans «\u202fDemander un congé\u202f». "
            "Si votre solde semble incorrect, contactez votre RH."
        ),
        "low",
    ),
    (
        r"salaire|paie|fiche de paie|bulletin",
        (
            "Vos bulletins de salaire sont accessibles dans la section «\u202fDocuments\u202f». "
            "Pour toute question sur votre rémunération, rapprochez-vous de votre gestionnaire RH."
        ),
        "low",
    ),
    (
        r"formation|apprentissage|cours|certification",
        (
            "Le catalogue des formations disponibles se trouve dans la section «\u202fFormations\u202f». "
            "Vous pouvez vous inscrire directement depuis votre espace personnel."
        ),
        "low",
    ),
    (
        r"contrat|cdi|cdd|période d'essai",
        (
            "Votre contrat de travail est disponible dans la section «\u202fDocuments\u202f». "
            "Pour toute modification contractuelle, contactez votre RH."
        ),
        "low",
    ),
    (
        r"tél[eé]travail|remote|travail à distance",
        (
            "La politique de télétravail de votre entreprise est définie par votre accord collectif. "
            "Pour connaître votre quota, consultez votre responsable ou votre RH."
        ),
        "low",
    ),
    (
        r"arr[eê]t maladie|maladie|médecin|certificat",
        (
            "En cas d'arrêt maladie, transmettez votre certificat médical à votre RH "
            "dans les 48\u202fheures. Votre arrêt sera saisi dans le système."
        ),
        "medium",
    ),
    (
        r"harcèlement|discrimination|plainte|signalement",
        (
            "⚠️\u202fCe sujet est sensible. Contactez immédiatement votre référent RH "
            "ou le service médiation de l'entreprise. Vos droits sont protégés."
        ),
        "high",
    ),
    (
        r"bonjour|salut|hello|bonsoir",
        (
            "Bonjour ! Je suis votre assistant RH. Comment puis-je vous aider aujourd'hui ?"
        ),
        "low",
    ),
    (
        r"merci|thank",
        "Avec plaisir ! N'hésitez pas si vous avez d'autres questions.",
        "low",
    ),
]

_DEFAULT_RESPONSE = (
    "Je n'ai pas de réponse précise à votre question pour l'instant. "
    "Consultez votre responsable RH ou envoyez un e-mail à rh@entreprise.com "
    "pour obtenir de l'aide.",
    "medium",
)


def _bot_reply(user_message: str, db: Session = None, current_user = None) -> tuple[str, str]:
    """Retourne (réponse_texte, risk_level)."""
    msg = user_message.lower()
    
    if current_user and db:
        if re.search(r"burnout|surmenage|risque|score", msg):
            from models.user import RoleEnum
            if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.MEDECINE_TRAVAIL]:
                return "Désolé, l'accès aux scores de risques et de burnout est strictement réservé aux managers et au personnel RH/Médical.", "high"
                
            from models.features import RiskScore
            from models.user import User
            risks = db.query(RiskScore).join(User).order_by(RiskScore.burnout_risk.desc()).limit(3).all()
            
            if not risks:
                return "Aucune donnée de risque de burnout n'est actuellement disponible dans la base.", "low"
                
            response = "Voici les collaborateurs présentant les indicateurs de burnout les plus élevés actuellement :\n\n"
            for r in risks:
                score = round(float(r.burnout_risk or 0), 1)
                response += f"- **{r.employee.prenom} {r.employee.nom}** : Score {score}%\n"
            response += "\nJe vous recommande de planifier un entretien ou de consulter le guide de prévention dans la base documentaire."
            return response, "high"
            
        if re.search(r"base documentaire|protocole|guide|prévention|politique", msg):
            return (
                "Pour consulter la base documentaire complète, les protocoles de sécurité, ou les guides de prévention (comme le guide de prévention du burnout), "
                "veuillez vous rendre dans l'onglet **Documents** ou utiliser la **Base de Connaissance IA** pour une recherche sémantique dans nos PDF."
            ), "low"

    for pattern, reply, risk in _RESPONSES:
        if re.search(pattern, msg):
            return reply, risk
    return _DEFAULT_RESPONSE


# ─── Helpers ────────────────────────────────────────────────────────────────

def _get_own_conversation(
    conversation_id: int,
    current_user,
    db: Session,
) -> ChatbotConversation:
    """Récupère une conversation ; lève 404/403 si introuvable ou non autorisée."""
    conv = (
        db.query(ChatbotConversation)
        .filter(ChatbotConversation.id == conversation_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    # Admins voient tout, les autres voient uniquement les leurs
    if current_user.role != RoleEnum.ADMIN and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return conv


# ─── Endpoints utilisateur ──────────────────────────────────────────────────


@router.post(
    "/conversations",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Démarrer une nouvelle conversation",
)
def create_conversation(
    payload: ConversationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tout utilisateur authentifié peut créer une conversation."""
    conv = ChatbotConversation(
        user_id=current_user.id,
        title=payload.title or f"Conversation du {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get(
    "/conversations",
    response_model=List[ConversationOut],
    summary="Lister mes conversations",
)
def list_conversations(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne les conversations de l'utilisateur courant."""
    return (
        db.query(ChatbotConversation)
        .filter(ChatbotConversation.user_id == current_user.id)
        .filter(ChatbotConversation.is_deleted_by_user == False)
        .order_by(ChatbotConversation.started_at.desc())
        .all()
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Détail d'une conversation (avec messages)",
)
def get_conversation(
    conversation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_own_conversation(conversation_id, current_user, db)


@router.delete(
    "/conversations/{conversation_id}/close",
    summary="Clore une conversation",
)
def close_conversation(
    conversation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_own_conversation(conversation_id, current_user, db)
    if conv.ended_at:
        raise HTTPException(status_code=400, detail="Conversation déjà clôturée")
    conv.ended_at = datetime.now(timezone.utc)
    db.commit()
    return {"detail": "Conversation clôturée avec succès"}


@router.delete(
    "/conversations/{conversation_id}",
    summary="Supprimer une conversation",
)
def delete_conversation(
    conversation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_own_conversation(conversation_id, current_user, db)
    # Anonymization / Soft Delete:
    # Instead of physically deleting the conversation, we mark it as deleted by the user.
    # We also detach the user_id from the conversation, messages, and logs to make them anonymous.
    
    # 1. Detach from chatbot_logs
    db.execute(
        text("UPDATE chatbot_logs SET user_id = NULL WHERE conversation_id = :cid AND user_id = :uid"), 
        {"cid": conv.id, "uid": current_user.id}
    )
    
    # 2. Detach from chatbot_messages
    db.execute(
        text("UPDATE chatbot_messages SET user_id = NULL WHERE conversation_id = :cid AND user_id = :uid"), 
        {"cid": conv.id, "uid": current_user.id}
    )
    
    # 3. Soft delete the conversation
    conv.is_deleted_by_user = True
    conv.user_id = None
    
    db.commit()
    return {"detail": "Conversation anonymisée avec succès"}


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageOut],
    status_code=status.HTTP_201_CREATED,
    summary="Envoyer un message et recevoir la réponse IA",
)
def send_message(
    conversation_id: int,
    payload: MessageSend,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sauvegarde le message utilisateur, génère la réponse bot et crée un log d'audit.
    Retourne [message_utilisateur, message_bot].
    """
    conv = _get_own_conversation(conversation_id, current_user, db)

    # Réouverture automatique si clôturée
    if conv.ended_at:
        conv.ended_at = None
        db.commit()

    # 1. Message utilisateur
    user_msg = ChatbotMessage(
        conversation_id=conv.id,
        user_id=current_user.id,
        sender="user",
        message=payload.message,
    )
    db.add(user_msg)
    db.flush()  # obtient l'id sans commit

    # 2. Réponse IA
    try:
        from ai.services.chat_service import chat as ai_chat
        ai_response, _, _, _, _ = ai_chat(
            query=payload.message,
            user=current_user,
            db=db,
            conversation_id=conv.id,
        )
        bot_text = ai_response
        risk = "low"
    except Exception:
        bot_text, risk = _bot_reply(payload.message, db, current_user)

    bot_msg = ChatbotMessage(
        conversation_id=conv.id,
        user_id=None,
        sender="bot",
        message=bot_text,
    )
    db.add(bot_msg)
    db.flush()

    # 3. Log d'audit
    log = ChatbotLog(
        user_id=current_user.id,
        conversation_id=conv.id,
        query=payload.message,
        response=bot_text,
        response_status="success",
        risk_level=risk,
    )
    db.add(log)
    db.commit()
    db.refresh(user_msg)
    db.refresh(bot_msg)

    return [user_msg, bot_msg]


# ─── Endpoints admin ────────────────────────────────────────────────────────


@router.get(
    "/admin/conversations",
    response_model=List[ConversationOut],
    summary="[Admin] Toutes les conversations de tous les utilisateurs",
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
def admin_list_all_conversations(
    user_id: Optional[int] = Query(None, description="Filtrer par utilisateur"),
    db: Session = Depends(get_db),
):
    q = db.query(ChatbotConversation)
    if user_id:
        q = q.filter(ChatbotConversation.user_id == user_id)
    return q.order_by(ChatbotConversation.started_at.desc()).all()


@router.get(
    "/logs",
    response_model=List[ChatbotLogOut],
    summary="[Admin] Logs d'audit du chatbot",
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
def get_chatbot_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    risk_level: Optional[str] = Query(None, description="Filtrer par niveau de risque : low | medium | high"),
    db: Session = Depends(get_db),
):
    q = db.query(ChatbotLog)
    if risk_level:
        q = q.filter(ChatbotLog.risk_level == risk_level)
    return (
        q.order_by(ChatbotLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
