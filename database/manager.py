from datetime import datetime, timedelta
import json
import bcrypt
import random
import streamlit as st
from .models import User, Game, UserAchievement, GlobalStats, get_db_session, Base
from sqlalchemy.orm import Session
from sqlalchemy import func, create_engine

class DatabaseManager:
    @staticmethod
    def create_user(username: str, password: str) -> User:
        with get_db_session() as session:
            # Hash password
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # Create user
            user = User(username=username, password_hash=password_hash)
            session.add(user)
            session.commit()
            return user
    
    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False
            if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                # Update session state with admin status
                st.session_state.is_admin = user.is_admin
                return True
            return False

    @staticmethod
    def make_admin(username: str) -> bool:
        """Make a user an admin"""
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False
            user.is_admin = True
            session.commit()
            return True
    
    @staticmethod
    def save_game(
        username: str,
        winner: str,
        moves_count: int,
        duration: float,
        game_mode: str,
        difficulty: str,
        moves_history: list
    ) -> Game:
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return None
            
            game = Game(
                user_id=user.id,
                winner=winner,
                moves_count=moves_count,
                duration=duration,
                game_mode=game_mode,
                difficulty=difficulty,
                moves_history=json.dumps(moves_history)
            )
            session.add(game)
            
            # Update global stats
            stats = session.query(GlobalStats).first()
            if not stats:
                stats = GlobalStats()
                session.add(stats)
            
            stats.total_games += 1
            stats.total_moves += moves_count
            if winner == 'X':
                stats.x_wins += 1
            elif winner == 'O':
                stats.o_wins += 1
            else:
                stats.draws += 1
            
            if winner and (not stats.fastest_win or duration < stats.fastest_win):
                stats.fastest_win = duration
            
            session.commit()
            return game
    
    @staticmethod
    def unlock_achievement(username: str, achievement_id: str) -> bool:
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False
            
            # Check if already unlocked
            existing = session.query(UserAchievement).filter(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == achievement_id
            ).first()
            
            if existing:
                return False
            
            achievement = UserAchievement(
                user_id=user.id,
                achievement_id=achievement_id
            )
            session.add(achievement)
            session.commit()
            return True
    
    @staticmethod
    def get_user_stats(username: str) -> dict:
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return None
            
            games = session.query(Game).filter(Game.user_id == user.id)
            achievements = session.query(UserAchievement).filter(
                UserAchievement.user_id == user.id
            )
            
            total_games = games.count()
            if total_games == 0:
                return {
                    'total_games': 0,
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                    'win_rate': 0,
                    'avg_moves': 0,
                    'total_time': 0,
                    'achievements': []
                }
            
            stats = {
                'total_games': total_games,
                'wins': games.filter(Game.winner == 'X').count(),
                'losses': games.filter(Game.winner == 'O').count(),
                'draws': games.filter(Game.winner == None).count(),
                'win_rate': games.filter(Game.winner == 'X').count() / total_games * 100,
                'avg_moves': games.with_entities(func.avg(Game.moves_count)).scalar() or 0,
                'total_time': games.with_entities(func.sum(Game.duration)).scalar() or 0,
                'achievements': [a.achievement_id for a in achievements.all()]
            }
            
            return stats
    
    @staticmethod
    def get_leaderboard() -> list:
        with get_db_session() as session:
            # Get top 10 players by win rate (minimum 10 games)
            leaderboard = []
            users = session.query(User).all()
            
            for user in users:
                games = session.query(Game).filter(Game.user_id == user.id)
                total_games = games.count()
                
                if total_games >= 10:
                    wins = games.filter(Game.winner == 'X').count()
                    win_rate = wins / total_games * 100
                    leaderboard.append({
                        'username': user.username,
                        'games': total_games,
                        'wins': wins,
                        'win_rate': win_rate
                    })
            
            return sorted(leaderboard, key=lambda x: x['win_rate'], reverse=True)[:10]
    
    @staticmethod
    def get_global_stats() -> dict:
        with get_db_session() as session:
            stats = session.query(GlobalStats).first()
            if not stats:
                return {
                    'total_games': 0,
                    'total_moves': 0,
                    'x_wins': 0,
                    'o_wins': 0,
                    'draws': 0,
                    'fastest_win': None,
                    'longest_win_streak': 0
                }
            
            return {
                'total_games': stats.total_games,
                'total_moves': stats.total_moves,
                'x_wins': stats.x_wins,
                'o_wins': stats.o_wins,
                'draws': stats.draws,
                'fastest_win': stats.fastest_win,
                'longest_win_streak': stats.longest_win_streak
            }

    @staticmethod
    def seed_database():
        """Seed the database with sample users and games for development/testing."""
        sample_users = {
            "alice": {
                "games": 20,  # More games for Alice
                "achievements": ["first_win", "speed_demon", "bot_master", "diagonal_win", "undefeated"],
                "win_ratio": 0.7  # 70% win rate
            },
            "bob": {"games": 5, "achievements": ["first_win"], "win_ratio": 0.4},
            "carol": {"games": 5, "achievements": [], "win_ratio": 0.5},
            "dave": {"games": 5, "achievements": [], "win_ratio": 0.3}
        }

        with get_db_session() as session:
            created_users = []
            
            # Create or update users
            for uname, user_data in sample_users.items():
                user = session.query(User).filter(User.username == uname).first()
                if not user:
                    password_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()
                    user = User(username=uname, password_hash=password_hash)
                    session.add(user)
                    session.flush()
                
                # Clear existing games and achievements for clean slate
                session.query(Game).filter(Game.user_id == user.id).delete()
                session.query(UserAchievement).filter(UserAchievement.user_id == user.id).delete()
                
                # Add achievements
                for achievement_id in user_data["achievements"]:
                    achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=achievement_id,
                        unlocked_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                    )
                    session.add(achievement)
                
                # Add games with specified win ratio
                num_games = user_data["games"]
                wins = int(num_games * user_data["win_ratio"])
                losses = int(num_games * (1 - user_data["win_ratio"]))
                draws = num_games - wins - losses
                
                # Generate games with proper distribution
                for outcome in (['X'] * wins + ['O'] * losses + [None] * draws):
                    moves = random.randint(8, 40)
                    duration = round(random.uniform(15.0, 600.0), 2)
                    # Ensure some fast wins for achievements
                    if uname == "alice" and outcome == 'X' and random.random() < 0.2:
                        duration = round(random.uniform(10.0, 25.0), 2)
                    
                    game = Game(
                        user_id=user.id,
                        winner=outcome,
                        moves_count=moves,
                        duration=duration,
                        game_mode=random.choice(['human', 'bot']),
                        difficulty=random.choice(['easy', 'medium', 'hard']),
                        moves_history=json.dumps([]),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                    )
                    session.add(game)
                
                created_users.append(user)
            
            # Ensure GlobalStats record exists and update it
            stats = session.query(GlobalStats).first()
            if not stats:
                stats = GlobalStats()
                session.add(stats)
            
            session.commit()
            
            # Recompute aggregate stats from games
            stats.total_games = session.query(func.count(Game.id)).scalar() or 0
            stats.total_moves = session.query(func.coalesce(func.sum(Game.moves_count), 0)).scalar() or 0
            stats.x_wins = session.query(func.count(Game.id)).filter(Game.winner == 'X').scalar() or 0
            stats.o_wins = session.query(func.count(Game.id)).filter(Game.winner == 'O').scalar() or 0
            stats.draws = session.query(func.count(Game.id)).filter(Game.winner == None).scalar() or 0
            stats.fastest_win = session.query(func.min(Game.duration)).filter(Game.winner.isnot(None)).scalar()
            
            # Update streak information
            consecutive_wins = 4  # For undefeated achievement
            stats.longest_win_streak = consecutive_wins
            
            session.commit()
            
            return True