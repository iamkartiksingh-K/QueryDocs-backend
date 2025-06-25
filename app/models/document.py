from sqlalchemy import Column, Integer, String, ForeignKey, UUID, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    size = Column(String) 
    created = Column(String, nullable=False)

    user = relationship("User", back_populates="documents")
