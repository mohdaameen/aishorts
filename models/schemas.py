from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
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

    preferences = relationship("UserPreference", backref="user", cascade="all, delete-orphan")

class UserPreference(Base):
    __tablename__ = 'user_preference'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_credential.id"), nullable=False)
    keyword = Column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'keyword', name='uq_user_keyword'),
    )

class VideoSummaryGlobal(Base):
    __tablename__ = 'video_summary_global'
    id = Column(Integer, primary_key=True)
    video_id = Column(String(255), unique=True, nullable=False)
    video_title = Column(String(512))
    video_link = Column(String(1024))
    summary = Column(String)
    tags = Column(String)
    category = Column(String)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user_links = relationship("UserVideoMap", backref="video", cascade="all, delete-orphan")
class UserVideoMap(Base):
    __tablename__ = 'user_video_map'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_credential.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("video_summary_global.id"), nullable=False)
    matched_keywords = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='uq_user_video_map'),
    )


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


