from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class UserCredential(Base):
    __tablename__ = 'user_credential'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    user_video_maps = relationship("UserVideoMap", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return f"<UserCredential(id={self.id}, username='{self.username}')>"
    

    
class UserPreference(Base):
    __tablename__ = 'user_preference'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_credential.id"), nullable=False)
    keyword = Column(String(255), nullable=False)

    user = relationship("UserCredential", back_populates="preferences")

    __table_args__ = (
        UniqueConstraint('user_id', 'keyword', name='uq_user_keyword'),
    )

    def __str__(self):
        return f"<UserPreference(id={self.id}, user_id={self.user_id}, keyword='{self.keyword}')>"


class VideoSummaryGlobal(Base):
    __tablename__ = 'video_summary_global'
    id = Column(Integer, primary_key=True)
    video_id = Column(String(255), unique=True, nullable=False)
    video_title = Column(String(512))
    video_link = Column(String(1024))
    summary = Column(Text)
    tags = Column(String)
    category = Column(String)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user_links = relationship("UserVideoMap", back_populates="video", cascade="all, delete-orphan")

    def __str__(self):
        return f"<VideoSummaryGlobal(id={self.id}, video_id='{self.video_id}', title='{self.video_title}')>"



class UserVideoMap(Base):
    __tablename__ = 'user_video_map'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_credential.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("video_summary_global.id"), nullable=False)
    matched_keywords = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserCredential", back_populates="user_video_maps")
    video = relationship("VideoSummaryGlobal", back_populates="user_links")

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='uq_user_video_map'),
    )


    def __str__(self):
        return f"<UserVideoMap(id={self.id}, user_id={self.user_id}, video_id={self.video_id})>"


class Database:
    def __init__(self, db_url="postgresql://postgres:aishorts%40123@db.jjcrgyehjwvvwvamqhwx.supabase.co:5432/postgres"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()

    def close(self):
        """Close the database connection"""
        self.engine.dispose()


