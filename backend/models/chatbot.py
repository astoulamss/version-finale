from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Boolean
from sqlalchemy.orm import relationship
from database.db import Base


class ChatbotConversation(Base):
    __tablename__ = "chatbot_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted_by_user = Column(Boolean, default=False, nullable=False)

    # Relations
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship("ChatbotMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatbotConversation(id={self.id}, user_id={self.user_id}, title={self.title})>"


class ChatbotMessage(Base):
    __tablename__ = "chatbot_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chatbot_conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sender = Column(String(50), nullable=False)  # "user" ou "bot"
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    conversation = relationship("ChatbotConversation", back_populates="messages")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<ChatbotMessage(id={self.id}, sender={self.sender})>"


class ChatbotLog(Base):
    __tablename__ = "chatbot_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    conversation_id = Column(Integer, ForeignKey("chatbot_conversations.id"), nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    response_status = Column(String(50), nullable=True)
    risk_level = Column(String(50), nullable=True)  # ex: "low", "medium", "high"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    user = relationship("User", foreign_keys=[user_id])
    conversation = relationship("ChatbotConversation", foreign_keys=[conversation_id])

    def __repr__(self):
        return f"<ChatbotLog(id={self.id}, user_id={self.user_id}, risk_level={self.risk_level})>"
