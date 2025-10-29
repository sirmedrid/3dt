import streamlit as st
import pandas as pd
from datetime import datetime

def init_stats():
    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'games_played': 0,
            'wins_x': 0,
            'wins_o': 0,
            'draws': 0,
            'avg_moves': 0,
            'total_moves': 0,
            'fastest_win': float('inf'),
            'win_streak': 0,
            'current_streak': 0,
            'history': []
        }

def update_stats(winner, moves, duration):
    stats = st.session_state.stats
    stats['games_played'] += 1
    
    if winner == 'X':
        stats['wins_x'] += 1
        stats['current_streak'] += 1
    elif winner == 'O':
        stats['wins_o'] += 1
        stats['current_streak'] = 0
    else:
        stats['draws'] += 1
        stats['current_streak'] = 0
    
    stats['win_streak'] = max(stats['win_streak'], stats['current_streak'])
    stats['total_moves'] += moves
    stats['avg_moves'] = stats['total_moves'] / stats['games_played']
    
    if winner and duration < stats['fastest_win']:
        stats['fastest_win'] = duration
    
    # Add to history
    stats['history'].append({
        'date': datetime.now(),
        'winner': winner if winner else 'Draw',
        'moves': moves,
        'duration': duration,
        'mode': st.session_state.game_mode,
        'difficulty': st.session_state.difficulty if st.session_state.game_mode == 'bot' else None
    })

def display_stats():
    st.sidebar.markdown("## Game Statistics")
    stats = st.session_state.stats
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Games Played", stats['games_played'])
        st.metric("Player X Wins", stats['wins_x'])
        st.metric("Draws", stats['draws'])
    with col2:
        st.metric("Win Streak", stats['current_streak'])
        st.metric("Player O Wins", stats['wins_o'])
        st.metric("Avg. Moves", f"{stats['avg_moves']:.1f}")
    
    if stats['fastest_win'] != float('inf'):
        st.sidebar.metric("Fastest Win", f"{stats['fastest_win']:.1f}s")
    
    if stats['history']:
        st.sidebar.markdown("### Recent Games")
        history_df = pd.DataFrame(stats['history'][-5:])
        st.sidebar.dataframe(
            history_df[['winner', 'moves', 'duration', 'mode']],
            hide_index=True
        )