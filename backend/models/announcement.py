from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from database.db import Base
import enum

class RecipientTypeEnum(str, enum.Enum):
    GLOBAL = "GLOBAL"
    DEPARTMENT = "DEPARTMENT"
    EMPLOYEE = "EMPLOYEE"

class AnnouncementStatusEnum(str, enum.Enum):
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_type = Column(Enum(RecipientTypeEnum), nullable=False)
    recipient_id = Column(Integer, nullable=True)  # Department ID or User ID
    status = Column(Enum(AnnouncementStatusEnum), default=AnnouncementStatusEnum.SENT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Announcement(id={self.id}, sender_id={self.sender_id}, type={self.recipient_type})>"
