import streamlit as st
from database.manager import DatabaseManager
import plotly.express as px
import pandas as pd

def display_leaderboard():
    st.markdown("## Global Leaderboard")
    
    leaderboard = DatabaseManager.get_leaderboard()
    if not leaderboard:
        st.info("No players have played enough games yet to be ranked!")
        return
    
    df = pd.DataFrame(leaderboard)
    
    # Create a bar chart for win rates
    fig = px.bar(
        df,
        x='username',
        y='win_rate',
        title='Top Players by Win Rate',
        labels={'username': 'Player', 'win_rate': 'Win Rate (%)'},
        color='win_rate',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Display detailed stats
    st.dataframe(
        df.style.format({
            'win_rate': '{:.1f}%',
            'games': '{:,d}',
            'wins': '{:,d}'
        }),
        hide_index=True,
        use_container_width=True
    )

def display_global_stats():
    st.markdown("## Global Statistics")
    
    stats = DatabaseManager.get_global_stats()
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Games", f"{stats['total_games']:,}")
        st.metric("Player X Wins", f"{stats['x_wins']:,}")
    with col2:
        st.metric("Total Moves", f"{stats['total_moves']:,}")
        st.metric("Player O Wins", f"{stats['o_wins']:,}")
    with col3:
        avg_moves = stats['total_moves'] / stats['total_games'] if stats['total_games'] > 0 else 0
        st.metric("Avg Moves/Game", f"{avg_moves:.1f}")
        st.metric("Draws", f"{stats['draws']:,}")
    
    # Create pie chart for win distribution
    win_data = pd.DataFrame([
        {'outcome': 'Player X', 'games': stats['x_wins']},
        {'outcome': 'Player O', 'games': stats['o_wins']},
        {'outcome': 'Draw', 'games': stats['draws']}
    ])
    
    fig = px.pie(
        win_data,
        values='games',
        names='outcome',
        title='Game Outcomes Distribution',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Display fastest win
    if stats['fastest_win']:
        st.markdown(f"### 🏃‍♂️ Fastest Win: {stats['fastest_win']:.1f} seconds")
    
    # Display longest streak
    st.markdown(f"### 🔥 Longest Win Streak: {stats['longest_win_streak']} games")