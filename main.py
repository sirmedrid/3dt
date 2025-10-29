import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random
from datetime import datetime
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

# Toggle to make Dev Tools visible to anyone (temporary)
FORCE_DEVTOOLS = True

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
init_user_system()

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
    """Evaluate the board state with a more sophisticated scoring system"""
    winner = check_winner(board)
    if winner == 'O':
        return 1000
    elif winner == 'X':
        return -1000
    
    score = 0
    # Check for potential winning moves
    for i in range(4):
        for j in range(4):
            # Check rows
            row = board[i, j, :]
            score += evaluate_line(row)
            # Check columns
            col = board[i, :, j]
            score += evaluate_line(col)
            # Check depth
            depth = board[:, i, j]
            score += evaluate_line(depth)
    
    return score

def evaluate_line(line):
    """Evaluate a line of 4 cells"""
    if '' not in line:
        return 0
    
    x_count = np.count_nonzero(line == 'X')
    o_count = np.count_nonzero(line == 'O')
    
    if o_count == 3 and x_count == 0:
        return 100  # Near win for O
    elif x_count == 3 and o_count == 0:
        return -100  # Near win for X
    elif o_count == 2 and x_count == 0:
        return 10  # Good position for O
    elif x_count == 2 and o_count == 0:
        return -10  # Good position for X
    elif o_count == 1 and x_count == 0:
        return 1  # Slight advantage for O
    elif x_count == 1 and o_count == 0:
        return -1  # Slight advantage for X
    
    return 0

def get_empty_cells(board):
    return [(z, y, x) for z in range(4) for y in range(4) for x in range(4) if board[z, y, x] == '']

def minimax(board, depth, is_maximizing, alpha, beta):
    """Minimax algorithm with alpha-beta pruning"""
    winner = check_winner(board)
    if winner == 'O':
        return 1000 + depth
    if winner == 'X':
        return -1000 - depth
    if depth == 0 or not np.any(board == ''):
        return evaluate_board(board)
    
    empty_cells = get_empty_cells(board)
    if is_maximizing:
        max_eval = float('-inf')
        for z, y, x in empty_cells:
            board[z, y, x] = 'O'
            eval = minimax(board, depth - 1, False, alpha, beta)
            board[z, y, x] = ''
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for z, y, x in empty_cells:
            board[z, y, x] = 'X'
            eval = minimax(board, depth - 1, True, alpha, beta)
            board[z, y, x] = ''
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def make_bot_move():
    """Make a move for the bot based on difficulty level"""
    empty_cells = get_empty_cells(st.session_state.board)
    if not empty_cells:
        return
    
    difficulty = st.session_state.difficulty
    if difficulty == 'easy':
        # Random move with 20% chance of making a good move
        if random.random() < 0.2:
            z, y, x = make_smart_move(empty_cells, depth=1)
        else:
            z, y, x = random.choice(empty_cells)
    
    elif difficulty == 'medium':
        # Smart move with depth 2, but 30% chance of random move
        if random.random() < 0.7:
            z, y, x = make_smart_move(empty_cells, depth=2)
        else:
            z, y, x = random.choice(empty_cells)
    
    else:  # hard
        # Full minimax with depth 3
        z, y, x = make_smart_move(empty_cells, depth=3)
    
    make_move(z, y, x)

def make_smart_move(empty_cells, depth):
    """Make a move using minimax algorithm"""
    best_score = float('-inf')
    best_move = empty_cells[0]
    
    for z, y, x in empty_cells:
        board_copy = st.session_state.board.copy()
        board_copy[z, y, x] = 'O'
        score = minimax(board_copy, depth, False, float('-inf'), float('inf'))
        if score > best_score:
            best_score = score
            best_move = (z, y, x)
            
    return best_move

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
        duration = (datetime.now() - st.session_state.game_start_time).total_seconds()
        if winner == 'X':
            if check_achievement('first_win'):
                st.balloons()
            if duration < 30:
                check_achievement('speed_demon')
            if st.session_state.game_mode == 'bot' and st.session_state.difficulty == 'hard':
                check_achievement('bot_master')
            if is_diagonal_win():
                check_achievement('diagonal_win')
            if st.session_state.stats['current_streak'] == 4:
                check_achievement('undefeated')
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
    """Update the game display with enhanced feedback"""
    with st.session_state.status_container:
        st.empty()
        if st.session_state.game_over:
            if st.session_state.winner:
                win_message = (
                    "🏆 Congratulations! "
                    f"Player {st.session_state.winner} wins in {st.session_state.move_count} moves! "
                    f"Game duration: {(datetime.now() - st.session_state.game_start_time).seconds} seconds"
                )
                st.success(win_message)
                # Show game statistics
                st.info(f"Moves played: {len(st.session_state.moves_history)}")
                if st.session_state.winner == 'X' and st.session_state.game_mode == 'bot':
                    st.success("Impressive! You've beaten the bot! 🎮")
            else:
                st.info("🤝 It's a draw! Well played by both sides!")
        else:
            player_turn = "Your turn" if st.session_state.current_player == 'X' else "Bot's turn" \
                if st.session_state.game_mode == 'bot' else f"Player {st.session_state.current_player}'s turn"
            st.info(f"📍 {player_turn} (Move {st.session_state.move_count + 1})")
            
            # Show last move if available
            if st.session_state.moves_history:
                last_z, last_y, last_x, last_player = st.session_state.moves_history[-1]
                st.text(f"Last move: Player {last_player} at Layer {last_z+1}, Row {last_y+1}, Column {last_x+1}")
    
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

# Dev Tools section at the top (visible to anyone when FORCE_DEVTOOLS=True)
if FORCE_DEVTOOLS or st.session_state.get('user'):
    with st.expander("🛠️ Dev Tools (temporary - visible to all)"):
        if st.button("Seed Database with Sample Data", type="primary"):
            try:
                DatabaseManager.seed_database()
                st.success("✅ Database seeded with sample users and games. Sample users (password is 'password'):\n- alice\n- bob\n- carol\n- dave")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to seed database: {str(e)}")
                if "DB_URL not found in Streamlit secrets" in str(e):
                    st.info("💡 Make sure to add your DB_URL in your Streamlit secrets. [Learn more](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)")

# Render auth UI (sidebar) and user stats
try:
    render_auth_ui()
    display_user_stats()
except Exception:
    # Render/auth functions expect session_state keys to be initialized.
    # init_user_system() above should prevent errors, but swallow any unexpected
    # issues in UI rendering so the main app stays up.
    pass

# Social Features
col1, col2 = st.columns([2, 3])
with col1:
    handle_tournament_ui()
with col2:
    display_chat()

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

# Developer tools (sidebar duplicate) - shown when forced or user present
if FORCE_DEVTOOLS or st.session_state.get('user'):
    with st.sidebar.expander("Dev Tools"):
        if st.button("Seed Database (dev)"):
            try:
                DatabaseManager.seed_database()
                st.success("Database seeded with sample users and games.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to seed database: {e}")
