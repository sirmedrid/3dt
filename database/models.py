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
    # Try to use DB_URL from Streamlit secrets. If connection fails (for example
    # due to SSL/network issues), fall back to a local SQLite file so development
    # and seeding can continue without a remote DB.
    db_url = None
    try:
        db_url = st.secrets.get("DB_URL")
    except Exception:
        db_url = None

    if db_url:
        try:
            # Use pool_pre_ping to help recover stale connections
            engine = create_engine(db_url, pool_pre_ping=True)
            # Try a quick connect to verify availability
            conn = engine.connect()
            conn.close()
            Base.metadata.create_all(engine)
            return sessionmaker(bind=engine)
        except Exception as exc:
            # Inform the user (visible in Streamlit UI) and fall back
            try:
                st.warning(f"Could not connect to DB at st.secrets['DB_URL']: {exc}. Falling back to local SQLite (dev.db) for development.")
            except Exception:
                # st may not be available in some contexts; ignore
                pass

    # Fallback to local SQLite file for development/testing
    local_url = "sqlite:///./dev.db"
    engine = create_engine(local_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# Create session factory
SessionFactory = None

def get_db_session():
    global SessionFactory
    if SessionFactory is None:
        SessionFactory = init_db()
    return SessionFactory()