import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random
from datetime import datetime
from streamlit_confetti import st_confetti
from streamlit_js_eval import streamlit_js_eval
from components.achievements import init_achievements, check_achievement, display_achievements, ACHIEVEMENTS
from components.stats import init_stats, update_stats, display_stats
from components.themes import init_theme, get_current_theme, apply_theme, display_theme_selector
from components.user_system import init_user_system, render_auth_ui, display_user_stats
from components.stats_dashboard import display_leaderboard, display_global_stats
from components.tutorial import run_tutorial
from components.tournament import init_tournament_system, handle_tournament_ui
from components.power_ups import init_power_ups, award_power_up, display_power_ups, handle_power_up_effects, POWER_UPS
from components.chat import init_chat, display_chat, send_game_event
from database.manager import DatabaseManager

# Initialize all session state
if 'board' not in st.session_state:
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False
    st.session_state.game_mode = 'human'  # 'human' or 'bot'
    st.session_state.difficulty = 'easy'  # 'easy', 'medium', 'hard'
    st.session_state.last_camera = None
    st.session_state.move_count = 0
    st.session_state.game_start_time = datetime.now()
    st.session_state.current_time = datetime.now()
    st.session_state.moves_history = []
    st.session_state.show_particles = False
    st.session_state.power_ups = {}
    st.session_state.tournament_active = False
    st.session_state.chat_messages = []

# Initialize components
init_achievements()
init_stats()
init_theme()
init_tournament_system()
init_power_ups()
init_chat()

def create_3d_board():
    """Create a 3D visualization of the game board using Plotly"""
    x, y, z, text, colors, opacity = [], [], [], [], [], []
    
    for i in range(4):
        for j in range(4):
            for k in range(4):
                x.append(i)
                y.append(j)
                z.append(k)
                cell_value = st.session_state.board[i, j, k]
                text.append(cell_value if cell_value != '' else '')
                if cell_value == 'X':
                    colors.append('#000000')
                    opacity.append(1.0)
                elif cell_value == 'O':
                    colors.append('#FFFFFF')
                    opacity.append(1.0)
                else:
                    colors.append('#E0E0E0')
                    opacity.append(0.3)

    fig = go.Figure(data=[
        go.Scatter3d(
            x=x, y=y, z=z, mode='markers',
            marker=dict(size=40, color=colors, opacity=opacity, line=dict(width=1, color='#808080')),
            text=text, textposition="middle center", textfont=dict(size=20), hoverinfo='none'
        )
    ])

    # Add grid lines
    for i in range(5):
        for j in range(5):
            for lines in [
                ([i-0.5, i-0.5], [j-0.5, j-0.5], [-0.5, 3.5]),
                ([i-0.5, i-0.5], [-0.5, 3.5], [j-0.5, j-0.5]),
                ([-0.5, 3.5], [i-0.5, i-0.5], [j-0.5, j-0.5])
            ]:
                fig.add_trace(go.Scatter3d(x=lines[0], y=lines[1], z=lines[2],
                                           mode='lines', line=dict(color='#CCCCCC', width=1), showlegend=False))

    camera = st.session_state.last_camera or dict(
        up=dict(x=0, y=0, z=1),
        center=dict(x=1.5, y=1.5, z=1.5),
        eye=dict(x=2.5, y=2.5, z=2.5)
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showticklabels=False),
            zaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showticklabels=False),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        scene_camera=camera,
        paper_bgcolor='white',
        plot_bgcolor='white',
        uirevision=True
    )
    return fig

def is_diagonal_win():
    """Check if the last win was achieved through a diagonal"""
    diagonals = [
        [(i, i, i) for i in range(4)],
        [(i, i, 3-i) for i in range(4)],
        [(i, 3-i, i) for i in range(4)],
        [(i, 3-i, 3-i) for i in range(4)]
    ]
    board = st.session_state.board
    winner = st.session_state.winner
    for diagonal in diagonals:
        if all(board[z, y, x] == winner for z, y, x in diagonal):
            return True
    return False

def check_winner(board):
    """Check all possible winning combinations in 3D tic-tac-toe"""
    for i in range(4):
        for j in range(4):
            if all(board[i, j, k] == board[i, j, 0] != '' for k in range(4)):
                return board[i, j, 0]
            if all(board[i, k, j] == board[i, 0, j] != '' for k in range(4)):
                return board[i, 0, j]
            if all(board[k, i, j] == board[0, i, j] != '' for k in range(4)):
                return board[0, i, j]
    # Face diagonals
    for i in range(4):
        if all(board[i, k, k] == board[i, 0, 0] != '' for k in range(4)):
            return board[i, 0, 0]
        if all(board[i, k, 3-k] == board[i, 0, 3] != '' for k in range(4)):
            return board[i, 0, 3]
        if all(board[k, i, k] == board[0, i, 0] != '' for k in range(4)):
            return board[0, i, 0]
        if all(board[k, i, 3-k] == board[0, i, 3] != '' for k in range(4)):
            return board[0, i, 3]
    # Space diagonals
    if all(board[k, k, k] == board[0, 0, 0] != '' for k in range(4)):
        return board[0, 0, 0]
    if all(board[k, k, 3-k] == board[0, 0, 3] != '' for k in range(4)):
        return board[0, 0, 3]
    if all(board[k, 3-k, k] == board[0, 3, 0] != '' for k in range(4)):
        return board[0, 3, 0]
    if all(board[k, 3-k, 3-k] == board[0, 3, 3] != '' for k in range(4)):
        return board[0, 3, 3]
    return None

def evaluate_board(board):
    winner = check_winner(board)
    return 1 if winner == 'O' else -1 if winner == 'X' else 0

def get_empty_cells(board):
    return [(z, y, x) for z in range(4) for y in range(4) for x in range(4) if board[z, y, x] == '']

def make_bot_move():
    empty_cells = get_empty_cells(st.session_state.board)
    if not empty_cells:
        return
    difficulty = st.session_state.difficulty
    if difficulty == 'easy':
        z, y, x = random.choice(empty_cells)
    elif difficulty == 'medium':
        if random.random() < 0.7:
            best_score, best_move = float('-inf'), empty_cells[0]
            for z, y, x in empty_cells:
                b = st.session_state.board.copy()
                b[z, y, x] = 'O'
                s = evaluate_board(b)
                if s > best_score:
                    best_score, best_move = s, (z, y, x)
            z, y, x = best_move
        else:
            z, y, x = random.choice(empty_cells)
    else:
        best_score, best_move = float('-inf'), empty_cells[0]
        for z, y, x in empty_cells:
            b = st.session_state.board.copy()
            b[z, y, x] = 'O'
            s = evaluate_board(b)
            if s > best_score:
                best_score, best_move = s, (z, y, x)
        z, y, x = best_move
    make_move(z, y, x)

def make_move(z, y, x):
    if st.session_state.game_over:
        return
    if st.session_state.board[z, y, x] != '':
        return
    st.session_state.moves_history.append((z, y, x, st.session_state.current_player))
    st.session_state.move_count += 1
    if st.session_state.power_ups:
        handle_power_up_effects(z, y, x)
    st.session_state.board[z, y, x] = st.session_state.current_player
    send_game_event(f"Player {st.session_state.current_player} placed at Layer {z+1}, Row {y+1}, Column {x+1}")
    winner = check_winner(st.session_state.board)
    game_end = False
    if winner:
        st.session_state.winner = winner
        st.session_state.game_over = True
        game_end = True
        st.session_state.show_particles = True
        duration = (datetime.now() - st.session_state.game_start_time).total_seconds()
        if winner == 'X':
            if check_achievement('first_win'): st_confetti()
            if duration < 30 and check_achievement('speed_demon'): st_confetti()
            if st.session_state.game_mode == 'bot' and st.session_state.difficulty == 'hard' and check_achievement('bot_master'): st_confetti()
            if is_diagonal_win() and check_achievement('diagonal_win'): st_confetti()
            if st.session_state.stats['current_streak'] == 4 and check_achievement('undefeated'): st_confetti()
    elif not np.any(st.session_state.board == ''):
        st.session_state.game_over = True
        game_end = True
    else:
        st.session_state.current_player = 'O' if st.session_state.current_player == 'X' else 'X'
    if game_end:
        duration = (datetime.now() - st.session_state.game_start_time).total_seconds()
        update_stats(winner, st.session_state.move_count, duration)
        if st.session_state.tournament_active and winner:
            handle_tournament_ui(winner)
    if not st.session_state.game_over and st.session_state.game_mode == 'bot' and st.session_state.current_player == 'O':
        make_bot_move()
    update_game_display()

def update_game_display():
    with st.session_state.status_container:
        st.empty()
        if st.session_state.game_over:
            if st.session_state.winner:
                st.success(f"Player {st.session_state.winner} wins!")
            else:
                st.info("It's a draw!")
        else:
            st.info(f"Current Player: **{st.session_state.current_player}**")
    with st.session_state.board_container:
        st.empty()
        refresh_board()

def refresh_board():
    st.plotly_chart(create_3d_board(), use_container_width=True)
    st.markdown("### Game Board")
    layers = st.columns(4)
    for z in range(4):
        with layers[z]:
            st.markdown(f"**Layer {z+1}**")
            for y in range(4):
                cols = st.columns(4)
                for x in range(4):
                    with cols[x]:
                        cell_value = st.session_state.board[z, y, x]
                        label = cell_value if cell_value else " "
                        disabled = st.session_state.game_over or cell_value != ''
                        if st.button(label, key=f"btn_{z}_{y}_{x}", disabled=disabled, use_container_width=True):
                            make_move(z, y, x)

def reset_game():
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False
    update_game_display()

# Initialize containers
for key in ['game_container', 'status_container', 'board_container']:
    if key not in st.session_state:
        st.session_state[key] = st.empty()

# UI
st.title("3D Tic Tac Toe")
st.markdown("**4x4x4 Cube** - Get 4 in a row to win!")

# Social & Tournament
social_col1, social_col2 = st.columns(2)
with social_col1: handle_tournament_ui()
with social_col2: display_chat()

# Power-ups
if st.session_state.current_player == 'X':
    display_power_ups()

# Settings
col1, col2, col3 = st.columns(3)
with col1:
    game_mode = st.selectbox("Game Mode", ['Human vs Human', 'Human vs Bot'],
                             index=0 if st.session_state.game_mode == 'human' else 1)
    st.session_state.game_mode = 'human' if game_mode == 'Human vs Human' else 'bot'
with col2:
    if st.session_state.game_mode == 'bot':
        difficulty = st.selectbox("Bot Difficulty", ['Easy', 'Medium', 'Hard'],
                                  index=['easy', 'medium', 'hard'].index(st.session_state.difficulty))
        st.session_state.difficulty = difficulty.lower()
with col3:
    if st.button("Reset Game", use_container_width=True):
        reset_game()

# Status
with st.session_state.status_container:
    if st.session_state.game_over:
        if st.session_state.winner:
            st.success(f"Player {st.session_state.winner} wins!")
        else:
            st.info("It's a draw!")
    else:
        st.info(f"Current Player: **{st.session_state.current_player}**")

# Board
st.plotly_chart(create_3d_board(), use_container_width=True)
refresh_board()

# Instructions
with st.expander("ℹ️ How to Play"):
    st.markdown("""
    **3D Tic Tac Toe Rules:**
    - The game is played on a 4x4x4 cube (4 layers)
    - Players alternate placing X's and O's
    - Get **4 in a row** to win!
    - Use the 3D view to see the cube from different angles
    - Click on the 2D layers to make moves
    """)

# Styling
st.markdown("""
<style>
.stButton button {
    font-size: 24px;
    font-weight: bold;
    height: 60px;
    background-color: #FFFFFF;
    color: #333333;
    border: 1px solid #CCCCCC;
}
.st-success {font-size: 24px; padding: 1rem; border-radius: 10px;}
.st-info {font-size: 20px; padding: 0.8rem; border-radius: 10px;}
.streamlit-expanderHeader {font-size: 16px; color: #333;}
</style>
""", unsafe_allow_html=True)
