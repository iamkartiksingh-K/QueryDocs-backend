from sqlalchemy import Column, Integer, String, UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class User(Base):
    __tablename__="users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    documents = relationship("Document", back_populates="user")