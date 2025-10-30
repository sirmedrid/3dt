import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random
from datetime import datetime
from components.achievements import init_achievements, check_achievement, display_achievements
from components.stats import init_stats, update_stats, display_stats
from components.themes import init_theme, get_current_theme, apply_theme, display_theme_selector
from components.user_system import init_user_system, render_auth_ui, display_user_stats
from components.stats_dashboard import display_leaderboard, display_global_stats
from components.tutorial import run_tutorial
from components.tournament import init_tournament_system, handle_tournament_ui
from components.power_ups import init_power_ups, award_power_up, display_power_ups, handle_power_up_effects
from components.chat import init_chat, display_chat, send_game_event
from database.manager import DatabaseManager

# Page config
st.set_page_config(page_title="3D Tic Tac Toe", page_icon="🎮", layout="wide")

# Initialize all session state
# Initialize all session state
# Ensure power_ups is always a dictionary
if 'power_ups' not in st.session_state or not isinstance(st.session_state.power_ups, dict):
    st.session_state.power_ups = {'X': [], 'O': []}

if 'board' not in st.session_state:
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False
    st.session_state.game_mode = 'human'
    st.session_state.difficulty = 'medium'
    st.session_state.last_camera = None
    st.session_state.move_count = 0
    st.session_state.game_start_time = datetime.now()
    st.session_state.current_time = datetime.now()
    st.session_state.moves_history = []
    st.session_state.tournament_active = False
    st.session_state.chat_messages = []
    st.session_state.show_devtools = False

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
    x, y, z, text = [], [], [], []
    marker_colors = []
    marker_sizes = []
    
    for i in range(4):
        for j in range(4):
            for k in range(4):
                x.append(i)
                y.append(j)
                z.append(k)
                cell_value = st.session_state.board[i, j, k]
                text.append(cell_value if cell_value != '' else '')
                
                if cell_value == 'X':
                    marker_colors.append('rgba(0, 0, 0, 1.0)')
                    marker_sizes.append(45)
                elif cell_value == 'O':
                    marker_colors.append('rgba(255, 255, 255, 1.0)')
                    marker_sizes.append(45)
                else:
                    marker_colors.append('rgba(220, 220, 220, 0.25)')
                    marker_sizes.append(35)

    fig = go.Figure(data=[
        go.Scatter3d(
            x=x, y=y, z=z, 
            mode='markers+text',
            marker=dict(
                size=marker_sizes,
                color=marker_colors,
                line=dict(width=2, color='#666666')
            ),
            text=text,
            textfont=dict(size=22, color='#333333', family='Arial Black'),
            textposition="middle center",
            hoverinfo='skip'
        )
    ])

    # Add enhanced grid lines
    for i in range(5):
        for j in range(5):
            for lines in [
                ([i-0.5, i-0.5], [j-0.5, j-0.5], [-0.5, 3.5]),
                ([i-0.5, i-0.5], [-0.5, 3.5], [j-0.5, j-0.5]),
                ([-0.5, 3.5], [i-0.5, i-0.5], [j-0.5, j-0.5])
            ]:
                fig.add_trace(go.Scatter3d(
                    x=lines[0], y=lines[1], z=lines[2],
                    mode='lines', 
                    line=dict(color='#BBBBBB', width=1.5), 
                    showlegend=False,
                    hoverinfo='skip'
                ))

    # Save the last camera state if available
    if 'relayoutData' in st._config._config_options['plotly_config']:
        camera_data = st._config._config_options['plotly_config']['relayoutData']
        if 'scene.camera' in camera_data:
            st.session_state.last_camera = camera_data['scene.camera']
    
    # Use the saved camera or default
    camera = st.session_state.last_camera or dict(
        up=dict(x=0, y=0, z=1),
        center=dict(x=1.5, y=1.5, z=1.5),
        eye=dict(x=3.5, y=3.5, z=3.5)  # Moved camera further back for better view
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showticklabels=False, showbackground=False),
            yaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showticklabels=False, showbackground=False),
            zaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showticklabels=False, showbackground=False),
            bgcolor='rgba(245, 245, 245, 0.3)'
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        scene_camera=camera,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        uirevision='constant',
        height=500
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
    # Straight lines
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
        if all(board[k, k, i] == board[0, 0, i] != '' for k in range(4)):
            return board[0, 0, i]
        if all(board[k, 3-k, i] == board[0, 3, i] != '' for k in range(4)):
            return board[0, 3, i]
    
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
    """Evaluate the board state"""
    winner = check_winner(board)
    if winner == 'O':
        return 1000
    elif winner == 'X':
        return -1000
    
    score = 0
    for i in range(4):
        for j in range(4):
            row = board[i, j, :]
            score += evaluate_line(row)
            col = board[i, :, j]
            score += evaluate_line(col)
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
        return 100
    elif x_count == 3 and o_count == 0:
        return -100
    elif o_count == 2 and x_count == 0:
        return 10
    elif x_count == 2 and o_count == 0:
        return -10
    elif o_count == 1 and x_count == 0:
        return 1
    elif x_count == 1 and o_count == 0:
        return -1
    
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
        if random.random() < 0.2:
            z, y, x = make_smart_move(empty_cells, depth=1)
        else:
            z, y, x = random.choice(empty_cells)
    elif difficulty == 'medium':
        if random.random() < 0.7:
            z, y, x = make_smart_move(empty_cells, depth=2)
        else:
            z, y, x = random.choice(empty_cells)
    else:  # hard
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
    
    # Check if current player has any active power-ups
    current_player = st.session_state.current_player
    if st.session_state.power_ups.get(current_player, []):
        handle_power_up_effects()
    
    st.session_state.board[z, y, x] = st.session_state.current_player
    send_game_event(f"Player {st.session_state.current_player} → L{z+1}R{y+1}C{x+1}")
    
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
            if st.session_state.stats.get('current_streak', 0) == 4:
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
    
    # Force refresh after any move
    st.rerun()

def reset_game():
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False
    st.session_state.move_count = 0
    st.session_state.game_start_time = datetime.now()
    st.session_state.moves_history = []
    st.session_state.power_ups = {'X': [], 'O': []}  # Reset power-ups
    init_power_ups()  # Re-initialize power-ups system
    st.rerun()

# ============= UI =============

# Header
st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1 style='margin: 0; font-size: 3rem; font-weight: 700;'>🎮 3D Tic Tac Toe</h1>
        <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; color: #666;'>4×4×4 Cube Challenge</p>
    </div>
""", unsafe_allow_html=True)

# Auth UI and User Stats
try:
    render_auth_ui()
    display_user_stats()
except Exception as e:
    st.error("Authentication system error. Please try again later.")
    st.stop()

# Check if user is logged in
if not st.session_state.get('user'):
    st.warning("👋 Please log in to play the game!")
    st.stop()

# Main game area
col_left, col_right = st.columns([2, 1])

with col_left:
    # Game status
    if st.session_state.game_over:
        if st.session_state.winner:
            duration = (datetime.now() - st.session_state.game_start_time).seconds
            st.success(f"🏆 Player **{st.session_state.winner}** wins in {st.session_state.move_count} moves! ({duration}s)")
            if st.session_state.winner == 'X' and st.session_state.game_mode == 'bot':
                st.info("🎯 Victory against the bot!")
        else:
            st.info("🤝 It's a draw! Well played!")
    else:
        player_label = "Your turn" if st.session_state.current_player == 'X' else \
                      ("Bot's turn" if st.session_state.game_mode == 'bot' else f"Player {st.session_state.current_player}'s turn")
        st.info(f"📍 {player_label} • Move #{st.session_state.move_count + 1}")
        
        if st.session_state.moves_history:
            last_z, last_y, last_x, last_player = st.session_state.moves_history[-1]
            st.caption(f"Last: Player {last_player} at Layer {last_z+1}, Row {last_y+1}, Column {last_x+1}")
    
    # 3D Board
    # Use move count in key to force refresh
    st.plotly_chart(create_3d_board(), width='stretch', key=f"board_3d_{st.session_state.move_count}")
    
    # 2D Layer Controls
    st.markdown("### 📊 Layer Controls")
    
    # Custom CSS for grid buttons
    st.markdown("""
        <style>
            /* Grid container styling */
            .layer-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 1rem;
                margin-bottom: 2rem;
            }
            
            /* Layer title */
            .layer-title {
                text-align: center;
                font-size: 1.2rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
                padding: 0.5rem;
                background: #f0f2f6;
                border-radius: 5px;
            }
            
            /* Grid cell styling */
            .grid-row {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 0.5rem;
                margin-bottom: 0.5rem;
            }
            
            /* Button styling */
            .stButton > button {
                width: 100% !important;
                height: 0 !important;
                padding-bottom: 100% !important;
                position: relative !important;
                border: 2px solid #ddd !important;
                background: white !important;
                border-radius: 8px !important;
                font-size: 24px !important;
                font-weight: bold !important;
                margin: 0 !important;
            }
            
            .stButton > button:hover:not(:disabled) {
                border-color: #888 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
            }
            
            .stButton > button:disabled {
                background: #f5f5f5 !important;
                cursor: not-allowed !important;
            }
            
            /* Layer separator */
            .layer-separator {
                height: 2px;
                background: #ddd;
                margin: 1rem 0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Create grid layout
    layers = st.columns(4)
    for z in range(4):
        with layers[z]:
            st.markdown(f'<div class="layer-title">Layer {z+1}</div>', unsafe_allow_html=True)
            for y in range(4):
                cols = st.columns(4)
                for x in range(4):
                    with cols[x]:
                        cell_value = st.session_state.board[z, y, x]
                        label = cell_value if cell_value else "·"
                        disabled = st.session_state.game_over or cell_value != '' or \
                                 (st.session_state.game_mode == 'bot' and st.session_state.current_player == 'O')
                        
                        # Custom button styling based on state
                        button_style = """
                            background-color: var(--primary-color) !important;
                            color: white !important;
                        """ if cell_value else ""
                        
                        if st.button(
                            label,
                            key=f"b_{z}_{y}_{x}",
                            disabled=disabled,
                            use_container_width=True
                        ):
                            make_move(z, y, x)
            
            # Add separator between layers
            if z < 3:
                st.markdown('<div class="layer-separator"></div>', unsafe_allow_html=True)

with col_right:
    # Game Controls
    st.markdown("### ⚙️ Game Settings")
    
    game_mode = st.selectbox(
        "Mode",
        ['Human vs Human', 'Human vs Bot'],
        index=0 if st.session_state.game_mode == 'human' else 1,
        key="mode_selector"
    )
    st.session_state.game_mode = 'human' if game_mode == 'Human vs Human' else 'bot'
    
    if st.session_state.game_mode == 'bot':
        difficulty = st.selectbox(
            "Difficulty",
            ['Easy', 'Medium', 'Hard'],
            index=['easy', 'medium', 'hard'].index(st.session_state.difficulty),
            key="difficulty_selector"
        )
        st.session_state.difficulty = difficulty.lower()
    
    if st.button("🔄 New Game", use_container_width=True, type="primary"):
        reset_game()
    
    st.divider()
    
    # Power-ups for both players
    st.markdown("### 🎮 Power-ups")
    
    # Display power-ups in two columns
    powerup_cols = st.columns(2)
    
    with powerup_cols[0]:
        st.markdown(f"**Player X**")
        if st.session_state.current_player == 'X':
            display_power_ups('X')
        else:
            # Show but disable power-ups for inactive player
            display_power_ups('X', disabled=True)
    
    with powerup_cols[1]:
        st.markdown(f"**Player O**")
        if st.session_state.current_player == 'O':
            display_power_ups('O')
        else:
            # Show but disable power-ups for inactive player
            display_power_ups('O', disabled=True)
    
    # Quick Stats
    st.markdown("### 📈 Quick Stats")
    stats = st.session_state.get('stats', {})
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Wins", stats.get('wins', 0))
    with col2:
        st.metric("Games", stats.get('total_games', 0))

# Social Features
st.divider()
social_col1, social_col2, social_col3 = st.columns([1, 1, 1])
with social_col1:
    handle_tournament_ui()
with social_col2:
    display_chat()
with social_col3:
    st.markdown("### 🏆 Achievements")
    display_achievements()

# Instructions
with st.expander("ℹ️ How to Play"):
    st.markdown("""
    **Rules:**
    - Play on a 4×4×4 cube (4 layers)
    - Players alternate placing X and O
    - Get **4 in a row** to win (any direction!)
    - Rotate the 3D view by dragging
    - Click layer buttons to place your mark
    
    **Winning Lines:**
    - Horizontal, vertical, or depth lines
    - Face diagonals (on any 2D plane)
    - Space diagonals (through the cube)
    """)

# Dev Tools (hidden by default, accessible only with proper authentication)
if st.session_state.get('is_admin', False):
    with st.sidebar.expander("🔧 Admin Tools"):
        if st.button("Seed Database"):
            try:
                DatabaseManager.seed_database()
                st.success("✅ Database seeded")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Enhanced Styling
st.markdown("""
<style>
    /* Button styling */
    .stButton button {
        font-size: 20px;
        font-weight: bold;
        height: 55px;
        border-radius: 8px;
        border: 2px solid #ddd;
        transition: all 0.2s;
    }
    
    .stButton button:hover:not(:disabled) {
        border-color: #888;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    
    .stButton button:disabled {
        opacity: 0.4;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
        padding: 1rem;
        font-size: 1.1rem;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Selectbox styling */
    .stSelectbox {
        margin-bottom: 1rem;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .stButton button {
            height: 45px;
            font-size: 18px;
        }
    }
</style>
""", unsafe_allow_html=True)
