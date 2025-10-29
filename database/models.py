from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import streamlit as st

# Create SQLAlchemy base class
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    games = relationship('Game', back_populates='user')
    achievements = relationship('UserAchievement', back_populates='user')

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    winner = Column(String)  # 'X', 'O', or None for draw
    moves_count = Column(Integer)
    duration = Column(Float)  # in seconds
    game_mode = Column(String)  # 'human' or 'bot'
    difficulty = Column(String)  # 'easy', 'medium', 'hard', or None
    moves_history = Column(String)  # JSON string of moves
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='games')

class UserAchievement(Base):
    __tablename__ = 'user_achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    achievement_id = Column(String)
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='achievements')

class GlobalStats(Base):
    __tablename__ = 'global_stats'
    
    id = Column(Integer, primary_key=True)
    total_games = Column(Integer, default=0)
    total_moves = Column(Integer, default=0)
    x_wins = Column(Integer, default=0)
    o_wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    fastest_win = Column(Float)  # in seconds
    longest_win_streak = Column(Integer, default=0)

# Database connection and session management
def init_db():
    try:
        db_url = st.secrets["DB_URL"]
    except KeyError:
        raise ValueError("DB_URL not found in Streamlit secrets. Please add it in your Streamlit settings.")
    
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# Create session factory
SessionFactory = None

def get_db_session():
    global SessionFactory
    if SessionFactory is None:
        SessionFactory = init_db()
    return SessionFactory()