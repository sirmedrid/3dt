import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random
from datetime import datetime
from streamlit_particles import particles
from streamlit_confetti import st_confetti
from streamlit_js_eval import streamlit_js_eval
from components.achievements import init_achievements, check_achievement, display_achievements, ACHIEVEMENTS
from components.stats import init_stats, update_stats, display_stats
from components.themes import init_theme, get_current_theme, apply_theme, display_theme_selector
from components.user_system import init_user_system,import streamlit as st
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
    st.session_state.last_camera = None  # Store camera position
    st.session_state.move_count = 0
    st.session_state.game_start_time = datetime.now()
    st.session_state.current_time = datetime.now()
    st.session_state.moves_history = []  # For replay feature
    st.session_state.power_ups = {}  # Store active power-ups
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
    x, y, z = [], [], []
    text = []
    colors = []
    opacity = []
    
    for i in range(4):
        for j in range(4):
            for k in range(4):
                x.append(i)
                y.append(j)
                z.append(k)
                cell_value = st.session_state.board[i, j, k]
                text.append(cell_value if cell_value != '' else '')
                if cell_value == 'X':
                    colors.append('#000000')  # Black for X
                    opacity.append(1.0)
                elif cell_value == 'O':
                    colors.append('#FFFFFF')  # White for O
                    opacity.append(1.0)
                else:
                    colors.append('#E0E0E0')  # Light gray for empty
                    opacity.append(0.3)  # More transparent for empty cells

    fig = go.Figure(data=[
        go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(
                size=40,
                color=colors,
                opacity=opacity,
                line=dict(
                    width=1,
                    color='#808080'
                )
            ),
            text=text,
            textposition="middle center",
            textfont=dict(size=20),
            hoverinfo='none'
        )
    ])

    # Add grid lines
    for i in range(5):
        # Vertical lines
        for j in range(5):
            fig.add_trace(go.Scatter3d(
                x=[i-0.5, i-0.5], y=[j-0.5, j-0.5], z=[-0.5, 3.5],
                mode='lines',
                line=dict(color='#CCCCCC', width=1),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[i-0.5, i-0.5], y=[-0.5, 3.5], z=[j-0.5, j-0.5],
                mode='lines',
                line=dict(color='#CCCCCC', width=1),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[-0.5, 3.5], y=[i-0.5, i-0.5], z=[j-0.5, j-0.5],
                mode='lines',
                line=dict(color='#CCCCCC', width=1),
                showlegend=False
            ))

    # Use the last camera position if available
    camera = st.session_state.last_camera if st.session_state.last_camera else dict(
        up=dict(x=0, y=0, z=1),
        center=dict(x=1.5, y=1.5, z=1.5),
        eye=dict(x=2.5, y=2.5, z=2.5)
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=True, backgroundcolor='white'),
            yaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=True, backgroundcolor='white'),
            zaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=True, backgroundcolor='white'),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        scene_camera=camera,
        paper_bgcolor='white',
        plot_bgcolor='white',
        uirevision=True  # This preserves the camera position on updates
    )
    
    return fig

def is_diagonal_win():
    """Check if the last win was achieved through a diagonal"""
    # Check space diagonals
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
    # Check rows, columns, and pillars
    for i in range(4):
        for j in range(4):
            # Rows (across x-axis)
            if all(board[i, j, k] == board[i, j, 0] != '' for k in range(4)):
                return board[i, j, 0]
            # Columns (across y-axis)
            if all(board[i, k, j] == board[i, 0, j] != '' for k in range(4)):
                return board[i, 0, j]
            # Pillars (across z-axis)
            if all(board[k, i, j] == board[0, i, j] != '' for k in range(4)):
                return board[0, i, j]
    
    # Check face diagonals (12 faces, 2 diagonals each = 24)
    for i in range(4):
        # XY plane diagonals at fixed z
        if all(board[i, k, k] == board[i, 0, 0] != '' for k in range(4)):
            return board[i, 0, 0]
        if all(board[i, k, 3-k] == board[i, 0, 3] != '' for k in range(4)):
            return board[i, 0, 3]
        
        # XZ plane diagonals at fixed y
        if all(board[k, i, k] == board[0, i, 0] != '' for k in range(4)):
            return board[0, i, 0]
        if all(board[k, i, 3-k] == board[0, i, 3] != '' for k in range(4)):
            return board[0, i, 3]
        
        # YZ plane diagonals at fixed x
        if all(board[i, k, k] == board[i, 0, 0] != '' for k in range(4)):
            return board[i, 0, 0]
        if all(board[i, k, 3-k] == board[i, 0, 3] != '' for k in range(4)):
            return board[i, 0, 3]
    
    # Check space diagonals (4 main diagonals through the cube)
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
    """Evaluate the board state for the bot"""
    winner = check_winner(board)
    if winner == 'O':
        return 1
    elif winner == 'X':
        return -1
    return 0

def get_empty_cells(board):
    """Get list of empty cells"""
    return [(z, y, x) for z in range(4) for y in range(4) for x in range(4) if board[z, y, x] == '']

def make_bot_move():
    """Make a move for the bot based on difficulty"""
    empty_cells = get_empty_cells(st.session_state.board)
    
    if not empty_cells:
        return
    
    if st.session_state.difficulty == 'easy':
        # Random move
        z, y, x = random.choice(empty_cells)
    elif st.session_state.difficulty == 'medium':
        # Mix of random and smart moves
        if random.random() < 0.7:  # 70% chance of making a smart move
            best_score = float('-inf')
            best_move = empty_cells[0]
            
            for z, y, x in empty_cells:
                board_copy = st.session_state.board.copy()
                board_copy[z, y, x] = 'O'
                score = evaluate_board(board_copy)
                
                if score > best_score:
                    best_score = score
                    best_move = (z, y, x)
            
            z, y, x = best_move
        else:
            z, y, x = random.choice(empty_cells)
    else:  # hard
        # Always make the best move
        best_score = float('-inf')
        best_move = empty_cells[0]
        
        for z, y, x in empty_cells:
            board_copy = st.session_state.board.copy()
            board_copy[z, y, x] = 'O'
            score = evaluate_board(board_copy)
            
            if score > best_score:
                best_score = score
                best_move = (z, y, x)
        
        z, y, x = best_move
    
    make_move(z, y, x)

def make_move(z, y, x):
    """Make a move at the specified position"""
    if st.session_state.game_over:
        return
    
    if st.session_state.board[z, y, x] == '':
        # Record the move for replay
        st.session_state.moves_history.append((z, y, x, st.session_state.current_player))
        st.session_state.move_count += 1
        
        # Apply any active power-up effects
        if 'power_ups' in st.session_state and st.session_state.power_ups:
            handle_power_up_effects(z, y, x)
            
        # Make the move
        st.session_state.board[z, y, x] = st.session_state.current_player
        
        # Send game event to chat
        send_game_event(f"Player {st.session_state.current_player} placed at Layer {z+1}, Row {y+1}, Column {x+1}")
        
        # Check win condition
        winner = check_winner(st.session_state.board)
        game_end = False
        
        if winner:
            st.session_state.winner = winner
            st.session_state.game_over = True
            game_end = True
            
            # Calculate game duration
            duration = (datetime.now() - st.session_state.game_start_time).total_seconds()
            
            # Check achievements
            if winner == 'X':
                if check_achievement('first_win'):
                    st_confetti()
                if duration < 30 and check_achievement('speed_demon'):
                    st_confetti()
                if st.session_state.game_mode == 'bot' and st.session_state.difficulty == 'hard' and check_achievement('bot_master'):
                    st_confetti()
                if is_diagonal_win() and check_achievement('diagonal_win'):
                    st_confetti()
                if st.session_state.stats['current_streak'] == 4 and check_achievement('undefeated'):
                    st_confetti()
            
        elif not np.any(st.session_state.board == ''):
            st.session_state.game_over = True
            game_end = True
        else:
            st.session_state.current_player = 'O' if st.session_state.current_player == 'X' else 'X'
        
            # Update stats if game ended
            if game_end:
                duration = (datetime.now() - st.session_state.game_start_time).total_seconds()
                update_stats(winner, st.session_state.move_count, duration)
                
                # Handle tournament progress if active
                if st.session_state.tournament_active and winner:
                    handle_tournament_ui(winner)        # If it's bot's turn, make a move
        if not st.session_state.game_over and st.session_state.game_mode == 'bot' and st.session_state.current_player == 'O':
            make_bot_move()
        
        # Update the containers instead of rerunning
        update_game_display()

def update_game_display():
    """Update only the necessary parts of the display"""
    # Update status
    with st.session_state.status_container:
        st.empty()  # Clear the container
        if st.session_state.game_over:
            if st.session_state.winner:
                st.success(f"Player {st.session_state.winner} wins!")
            else:
                st.info("It's a draw!")
        else:
            st.info(f"Current Player: **{st.session_state.current_player}**")
    
    # Update board
    with st.session_state.board_container:
        st.empty()  # Clear the container
        refresh_board()

def refresh_board():
    """Refresh the game board display"""
    # 3D Visualization
    st.plotly_chart(create_3d_board(), use_container_width=True)

    # 2D Layer view for interaction
    st.markdown("### Game Board")
    layers = st.columns(4)

    for z in range(4):
        with layers[z]:
            st.markdown(f"**Layer {z+1}**")
            
            # Create a 4x4 grid for this layer
            for y in range(4):
                cols = st.columns(4)
                for x in range(4):
                    with cols[x]:
                        cell_value = st.session_state.board[z, y, x]
                        
                        # Display button with appropriate styling
                        if cell_value == '':
                            label = " "  # Empty space instead of dot
                            disabled = st.session_state.game_over
                        else:
                            label = cell_value
                            disabled = True
                        
                        if st.button(
                            label,
                            key=f"btn_{z}_{y}_{x}",
                            disabled=disabled,
                            use_container_width=True
                        ):
                            make_move(z, y, x)

def reset_game():
    """Reset the game to initial state"""
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False
    update_game_display()

# Initialize container keys in session state if they don't exist
if 'game_container' not in st.session_state:
    st.session_state.game_container = st.empty()
if 'status_container' not in st.session_state:
    st.session_state.status_container = st.empty()
if 'board_container' not in st.session_state:
    st.session_state.board_container = st.empty()

# UI Header (this won't be refreshed)
st.title("3D Tic Tac Toe")
st.markdown("**4x4x4 Cube** - Get 4 in a row to win!")

# Social & Tournament features
social_col1, social_col2 = st.columns(2)
with social_col1:
    handle_tournament_ui()  # Show tournament bracket and controls
with social_col2:
    display_chat()  # Show real-time chat

# Power-ups display
if st.session_state.current_player == 'X':  # Only show for human player
    display_power_ups()

# Game settings container (this won't be refreshed)
settings_col1, settings_col2, settings_col3 = st.columns(3)
with settings_col1:
    game_mode = st.selectbox("Game Mode", ['Human vs Human', 'Human vs Bot'], 
                        index=0 if st.session_state.game_mode == 'human' else 1,
                        key='game_mode_select')
    st.session_state.game_mode = 'human' if game_mode == 'Human vs Human' else 'bot'

with settings_col2:
    if st.session_state.game_mode == 'bot':
        difficulty = st.selectbox("Bot Difficulty", ['Easy', 'Medium', 'Hard'],
                            index=['easy', 'medium', 'hard'].index(st.session_state.difficulty),
                            key='difficulty_select')
        st.session_state.difficulty = difficulty.lower()

with settings_col3:
    if st.button("Reset Game", use_container_width=True):
        reset_game()

# Game status (will be refreshed)
with st.session_state.status_container:
    if st.session_state.game_over:
        if st.session_state.winner:
            st.success(f"Player {st.session_state.winner} wins!")
        else:
            st.info("It's a draw!")
    else:
        st.info(f"Current Player: **{st.session_state.current_player}**")

# 3D Visualization
st.plotly_chart(create_3d_board(), use_container_width=True)

# Display the 4 layers
st.markdown("### Game Board (4 Layers)")
layers = st.columns(4)

for z in range(4):
    with layers[z]:
        st.markdown(f"**Layer {z+1}**")
        
        # Create a 4x4 grid for this layer
        for y in range(4):
            cols = st.columns(4)
            for x in range(4):
                with cols[x]:
                    cell_value = st.session_state.board[z, y, x]
                    
                    # Display button with appropriate styling
                    if cell_value == '':
                        label = "·"
                        disabled = st.session_state.game_over
                    else:
                        label = cell_value
                        disabled = True
                    
                    if st.button(
                        label,
                        key=f"btn_{z}_{y}_{x}",
                        disabled=disabled,
                        use_container_width=True
                    ):
                        make_move(z, y, x)
                        st.rerun()

# Instructions
with st.expander("ℹ️ How to Play"):
    st.markdown("""
    **3D Tic Tac Toe Rules:**
    
    - The game is played on a 4x4x4 cube (4 layers)
    - Players alternate placing X's and O's
    - Get **4 in a row** to win!
    - Use the 3D view to see the board from different angles
    - Click on the 2D layers below to make moves
    
    **Game Modes:**
    - Human vs Human: Play against another person
    - Human vs Bot: Play against the computer
      - Easy: Bot makes random moves
      - Medium: Bot makes smart moves 70% of the time
      - Hard: Bot always makes the best possible move
    
    **Winning combinations:**
    - 4 across any row (horizontal)
    - 4 down any column (vertical)
    - 4 through any pillar (depth)
    - 4 along any diagonal (face or space diagonal)
    
    There are 76 possible winning combinations in total!
    """)

# Add some styling
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
    /* Custom styling for game status messages */
    .st-success {
        font-size: 24px;
        padding: 1rem;
        border-radius: 10px;
    }
    .st-info {
        font-size: 20px;
        padding: 0.8rem;
        border-radius: 10px;
    }
    /* Improved button colors for X and O */
    .stButton button:contains("X") {
        background-color: #000000 !important;
        color: white !important;
        border: none !important;
    }
    .stButton button:contains("O") {
        background-color: #FFFFFF !important;
        color: black !important;
        border: 2px solid #000000 !important;
    }
    /* Remove emojis from expander */
    .streamlit-expanderHeader {
        font-size: 16px;
        color: #333333;
    }
</style>
""", unsafe_allow_html=True) render_auth_ui, display_user_stats
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
    st.session_state.last_camera = None  # Store camera position
    st.session_state.move_count = 0
    st.session_state.game_start_time = datetime.now()
    st.session_state.current_time = datetime.now()
    st.session_state.moves_history = []  # For replay feature
    st.session_state.show_particles = False
    st.session_state.power_ups = {}  # Store active power-ups
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
    x, y, z = [], [], []
    text = []
    colors = []
    opacity = []
    
    for i in range(4):
        for j in range(4):
            for k in range(4):
                x.append(i)
                y.append(j)
                z.append(k)
                cell_value = st.session_state.board[i, j, k]
                text.append(cell_value if cell_value != '' else '')
                if cell_value == 'X':
                    colors.append('#000000')  # Black for X
                    opacity.append(1.0)
                elif cell_value == 'O':
                    colors.append('#FFFFFF')  # White for O
                    opacity.append(1.0)
                else:
                    colors.append('#E0E0E0')  # Light gray for empty
                    opacity.append(0.3)  # More transparent for empty cells

    fig = go.Figure(data=[
        go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(
                size=40,
                color=colors,
                opacity=opacity,
                line=dict(
                    width=1,
                    color='#808080'
                )
            ),
            text=text,
            textposition="middle center",
            textfont=dict(size=20),
            hoverinfo='none'
        )
    ])

    # Add grid lines
    for i in range(5):
        # Vertical lines
        for j in range(5):
            fig.add_trace(go.Scatter3d(
                x=[i-0.5, i-0.5], y=[j-0.5, j-0.5], z=[-0.5, 3.5],
                mode='lines',
                line=dict(color='#CCCCCC', width=1),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[i-0.5, i-0.5], y=[-0.5, 3.5], z=[j-0.5, j-0.5],
                mode='lines',
                line=dict(color='#CCCCCC', width=1),
                showlegend=False
            ))
            fig.add_trace(go.Scatter3d(
                x=[-0.5, 3.5], y=[i-0.5, i-0.5], z=[j-0.5, j-0.5],
                mode='lines',
                line=dict(color='#CCCCCC', width=1),
                showlegend=False
            ))

    # Use the last camera position if available
    camera = st.session_state.last_camera if st.session_state.last_camera else dict(
        up=dict(x=0, y=0, z=1),
        center=dict(x=1.5, y=1.5, z=1.5),
        eye=dict(x=2.5, y=2.5, z=2.5)
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=True, backgroundcolor='white'),
            yaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=True, backgroundcolor='white'),
            zaxis=dict(range=[-1, 4], showgrid=False, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=True, backgroundcolor='white'),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        scene_camera=camera,
        paper_bgcolor='white',
        plot_bgcolor='white',
        uirevision=True  # This preserves the camera position on updates
    )
    
    return fig

def is_diagonal_win():
    """Check if the last win was achieved through a diagonal"""
    # Check space diagonals
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
    # Check rows, columns, and pillars
    for i in range(4):
        for j in range(4):
            # Rows (across x-axis)
            if all(board[i, j, k] == board[i, j, 0] != '' for k in range(4)):
                return board[i, j, 0]
            # Columns (across y-axis)
            if all(board[i, k, j] == board[i, 0, j] != '' for k in range(4)):
                return board[i, 0, j]
            # Pillars (across z-axis)
            if all(board[k, i, j] == board[0, i, j] != '' for k in range(4)):
                return board[0, i, j]
    
    # Check face diagonals (12 faces, 2 diagonals each = 24)
    for i in range(4):
        # XY plane diagonals at fixed z
        if all(board[i, k, k] == board[i, 0, 0] != '' for k in range(4)):
            return board[i, 0, 0]
        if all(board[i, k, 3-k] == board[i, 0, 3] != '' for k in range(4)):
            return board[i, 0, 3]
        
        # XZ plane diagonals at fixed y
        if all(board[k, i, k] == board[0, i, 0] != '' for k in range(4)):
            return board[0, i, 0]
        if all(board[k, i, 3-k] == board[0, i, 3] != '' for k in range(4)):
            return board[0, i, 3]
        
        # YZ plane diagonals at fixed x
        if all(board[i, k, k] == board[i, 0, 0] != '' for k in range(4)):
            return board[i, 0, 0]
        if all(board[i, k, 3-k] == board[i, 0, 3] != '' for k in range(4)):
            return board[i, 0, 3]
    
    # Check space diagonals (4 main diagonals through the cube)
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
    """Evaluate the board state for the bot"""
    winner = check_winner(board)
    if winner == 'O':
        return 1
    elif winner == 'X':
        return -1
    return 0

def get_empty_cells(board):
    """Get list of empty cells"""
    return [(z, y, x) for z in range(4) for y in range(4) for x in range(4) if board[z, y, x] == '']

def make_bot_move():
    """Make a move for the bot based on difficulty"""
    empty_cells = get_empty_cells(st.session_state.board)
    
    if not empty_cells:
        return
    
    if st.session_state.difficulty == 'easy':
        # Random move
        z, y, x = random.choice(empty_cells)
    elif st.session_state.difficulty == 'medium':
        # Mix of random and smart moves
        if random.random() < 0.7:  # 70% chance of making a smart move
            best_score = float('-inf')
            best_move = empty_cells[0]
            
            for z, y, x in empty_cells:
                board_copy = st.session_state.board.copy()
                board_copy[z, y, x] = 'O'
                score = evaluate_board(board_copy)
                
                if score > best_score:
                    best_score = score
                    best_move = (z, y, x)
            
            z, y, x = best_move
        else:
            z, y, x = random.choice(empty_cells)
    else:  # hard
        # Always make the best move
        best_score = float('-inf')
        best_move = empty_cells[0]
        
        for z, y, x in empty_cells:
            board_copy = st.session_state.board.copy()
            board_copy[z, y, x] = 'O'
            score = evaluate_board(board_copy)
            
            if score > best_score:
                best_score = score
                best_move = (z, y, x)
        
        z, y, x = best_move
    
    make_move(z, y, x)

def make_move(z, y, x):
    """Make a move at the specified position"""
    if st.session_state.game_over:
        return
    
    if st.session_state.board[z, y, x] == '':
        # Record the move for replay
        st.session_state.moves_history.append((z, y, x, st.session_state.current_player))
        st.session_state.move_count += 1
        
        # Apply any active power-up effects
        if 'power_ups' in st.session_state and st.session_state.power_ups:
            handle_power_up_effects(z, y, x)
            
        # Make the move
        st.session_state.board[z, y, x] = st.session_state.current_player
        
        # Send game event to chat
        send_game_event(f"Player {st.session_state.current_player} placed at Layer {z+1}, Row {y+1}, Column {x+1}")
        
        # Check win condition
        winner = check_winner(st.session_state.board)
        game_end = False
        
        if winner:
            st.session_state.winner = winner
            st.session_state.game_over = True
            game_end = True
            st.session_state.show_particles = True
            
            # Calculate game duration
            duration = (datetime.now() - st.session_state.game_start_time).total_seconds()
            
            # Check achievements
            if winner == 'X':
                if check_achievement('first_win'):
                    st_confetti()
                if duration < 30 and check_achievement('speed_demon'):
                    st_confetti()
                if st.session_state.game_mode == 'bot' and st.session_state.difficulty == 'hard' and check_achievement('bot_master'):
                    st_confetti()
                if is_diagonal_win() and check_achievement('diagonal_win'):
                    st_confetti()
                if st.session_state.stats['current_streak'] == 4 and check_achievement('undefeated'):
                    st_confetti()
            
        elif not np.any(st.session_state.board == ''):
            st.session_state.game_over = True
            game_end = True
        else:
            st.session_state.current_player = 'O' if st.session_state.current_player == 'X' else 'X'
        
            # Update stats if game ended
            if game_end:
                duration = (datetime.now() - st.session_state.game_start_time).total_seconds()
                update_stats(winner, st.session_state.move_count, duration)
                
                # Handle tournament progress if active
                if st.session_state.tournament_active and winner:
                    handle_tournament_ui(winner)        # If it's bot's turn, make a move
        if not st.session_state.game_over and st.session_state.game_mode == 'bot' and st.session_state.current_player == 'O':
            make_bot_move()
        
        # Update the containers instead of rerunning
        update_game_display()

def update_game_display():
    """Update only the necessary parts of the display"""
    # Update status
    with st.session_state.status_container:
        st.empty()  # Clear the container
        if st.session_state.game_over:
            if st.session_state.winner:
                st.success(f"Player {st.session_state.winner} wins!")
            else:
                st.info("It's a draw!")
        else:
            st.info(f"Current Player: **{st.session_state.current_player}**")
    
    # Update board
    with st.session_state.board_container:
        st.empty()  # Clear the container
        refresh_board()

def refresh_board():
    """Refresh the game board display"""
    # 3D Visualization
    st.plotly_chart(create_3d_board(), use_container_width=True)

    # 2D Layer view for interaction
    st.markdown("### Game Board")
    layers = st.columns(4)

    for z in range(4):
        with layers[z]:
            st.markdown(f"**Layer {z+1}**")
            
            # Create a 4x4 grid for this layer
            for y in range(4):
                cols = st.columns(4)
                for x in range(4):
                    with cols[x]:
                        cell_value = st.session_state.board[z, y, x]
                        
                        # Display button with appropriate styling
                        if cell_value == '':
                            label = " "  # Empty space instead of dot
                            disabled = st.session_state.game_over
                        else:
                            label = cell_value
                            disabled = True
                        
                        if st.button(
                            label,
                            key=f"btn_{z}_{y}_{x}",
                            disabled=disabled,
                            use_container_width=True
                        ):
                            make_move(z, y, x)

def reset_game():
    """Reset the game to initial state"""
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False
    update_game_display()

# Initialize container keys in session state if they don't exist
if 'game_container' not in st.session_state:
    st.session_state.game_container = st.empty()
if 'status_container' not in st.session_state:
    st.session_state.status_container = st.empty()
if 'board_container' not in st.session_state:
    st.session_state.board_container = st.empty()

# UI Header (this won't be refreshed)
st.title("3D Tic Tac Toe")
st.markdown("**4x4x4 Cube** - Get 4 in a row to win!")

# Social & Tournament features
social_col1, social_col2 = st.columns(2)
with social_col1:
    handle_tournament_ui()  # Show tournament bracket and controls
with social_col2:
    display_chat()  # Show real-time chat

# Power-ups display
if st.session_state.current_player == 'X':  # Only show for human player
    display_power_ups()

# Game settings container (this won't be refreshed)
settings_col1, settings_col2, settings_col3 = st.columns(3)
with settings_col1:
    game_mode = st.selectbox("Game Mode", ['Human vs Human', 'Human vs Bot'], 
                        index=0 if st.session_state.game_mode == 'human' else 1,
                        key='game_mode_select')
    st.session_state.game_mode = 'human' if game_mode == 'Human vs Human' else 'bot'

with settings_col2:
    if st.session_state.game_mode == 'bot':
        difficulty = st.selectbox("Bot Difficulty", ['Easy', 'Medium', 'Hard'],
                            index=['easy', 'medium', 'hard'].index(st.session_state.difficulty),
                            key='difficulty_select')
        st.session_state.difficulty = difficulty.lower()

with settings_col3:
    if st.button("Reset Game", use_container_width=True):
        reset_game()

# Game status (will be refreshed)
with st.session_state.status_container:
    if st.session_state.game_over:
        if st.session_state.winner:
            st.success(f"Player {st.session_state.winner} wins!")
        else:
            st.info("It's a draw!")
    else:
        st.info(f"Current Player: **{st.session_state.current_player}**")

# 3D Visualization
st.plotly_chart(create_3d_board(), use_container_width=True)

# Display the 4 layers
st.markdown("### Game Board (4 Layers)")
layers = st.columns(4)

for z in range(4):
    with layers[z]:
        st.markdown(f"**Layer {z+1}**")
        
        # Create a 4x4 grid for this layer
        for y in range(4):
            cols = st.columns(4)
            for x in range(4):
                with cols[x]:
                    cell_value = st.session_state.board[z, y, x]
                    
                    # Display button with appropriate styling
                    if cell_value == '':
                        label = "·"
                        disabled = st.session_state.game_over
                    else:
                        label = cell_value
                        disabled = True
                    
                    if st.button(
                        label,
                        key=f"btn_{z}_{y}_{x}",
                        disabled=disabled,
                        use_container_width=True
                    ):
                        make_move(z, y, x)
                        st.rerun()

# Instructions
with st.expander("ℹ️ How to Play"):
    st.markdown("""
    **3D Tic Tac Toe Rules:**
    
    - The game is played on a 4x4x4 cube (4 layers)
    - Players alternate placing X's and O's
    - Get **4 in a row** to win!
    - Use the 3D view to see the board from different angles
    - Click on the 2D layers below to make moves
    
    **Game Modes:**
    - Human vs Human: Play against another person
    - Human vs Bot: Play against the computer
      - Easy: Bot makes random moves
      - Medium: Bot makes smart moves 70% of the time
      - Hard: Bot always makes the best possible move
    
    **Winning combinations:**
    - 4 across any row (horizontal)
    - 4 down any column (vertical)
    - 4 through any pillar (depth)
    - 4 along any diagonal (face or space diagonal)
    
    There are 76 possible winning combinations in total!
    """)

# Add some styling
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
    /* Custom styling for game status messages */
    .st-success {
        font-size: 24px;
        padding: 1rem;
        border-radius: 10px;
    }
    .st-info {
        font-size: 20px;
        padding: 0.8rem;
        border-radius: 10px;
    }
    /* Improved button colors for X and O */
    .stButton button:contains("X") {
        background-color: #000000 !important;
        color: white !important;
        border: none !important;
    }
    .stButton button:contains("O") {
        background-color: #FFFFFF !important;
        color: black !important;
        border: 2px solid #000000 !important;
    }
    /* Remove emojis from expander */
    .streamlit-expanderHeader {
        font-size: 16px;
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)