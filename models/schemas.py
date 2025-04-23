from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, backref
from datetime import datetime

Base = declarative_base()

# Association table for Summary <-> Tag (Many-to-Many)
class SummaryTagMap(Base):
    __tablename__ = 'summary_tag_map'
    summary_id = Column(Integer, ForeignKey('summaries.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

# Association table for User <-> Tag (User's interest tags)
class UserTagMap(Base):
    __tablename__ = 'user_tag_map'
    user_id = Column(Integer, ForeignKey('user_credentials.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

class UserCredential(Base):
    __tablename__ = 'user_credentials'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tags = relationship("Tag", secondary="user_tag_map", back_populates="users")

    def __repr__(self):
        return f"<UserCredential(id={self.id}, username='{self.username}')>"

class Summary(Base):
    __tablename__ = 'summaries'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    source = Column(String(50))  # e.g., 'youtube', 'medium'
    link = Column(String(500))
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    tags = relationship("Tag", secondary="summary_tag_map", back_populates="summaries")

    def __repr__(self):
        return f"<Summary(id={self.id}, title='{self.title}', source='{self.source}')>"

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., 'ai', 'blockchain'

    summaries = relationship("Summary", secondary="summary_tag_map", back_populates="tags")
    users = relationship("UserCredential", secondary="user_tag_map", back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"

class Database:
    def __init__(self, db_url="postgresql://postgres:aishorts%40123@db.jjcrgyehjwvvwvamqhwx.supabase.co:5432/postgres"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.SessionLocal()

    def close(self):
        self.engine.dispose()
