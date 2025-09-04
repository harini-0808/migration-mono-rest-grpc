from sqlalchemy import Column, String, DateTime, Text, JSON
from datetime import datetime, timezone
from config.db_config import Base
import uuid
from sqlalchemy.dialects.mysql import LONGTEXT

class Analysis(Base):
    __tablename__ = "analysis"
 
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    repo_url = Column(String(255), nullable=False)  
    target_version = Column(String(20), nullable=False)  
    structure = Column(JSON, nullable=True)
    analysis = Column(JSON, nullable=True)
    instruction = Column(Text, nullable=True)
    api_type = Column(String(255), nullable=True)
    zip_content = Column(Text(length=4294967295), nullable=True)  # 4 GB limit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
 
    def __repr__(self):
        return f"<Analysis(repo_url='{self.repo_url}', target_version='{self.target_version}')>"

class User(Base):
    __tablename__ = "users"
 
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(64), nullable=False)  # SHA-256 hash is 64 characters
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
 
    def __repr__(self):
        return f"<User(username='{self.username}')>"