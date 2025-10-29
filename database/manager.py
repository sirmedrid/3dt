from datetime import datetime
import json
import bcrypt
from .models import User, Game, UserAchievement, GlobalStats, get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import func

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
            return bcrypt.checkpw(password.encode(), user.password_hash.encode())
    
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