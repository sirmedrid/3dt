import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False
    st.session_state.game_mode = 'human'  # 'human' or 'bot'
    st.session_state.difficulty = 'easy'  # 'easy', 'medium', 'hard'

def create_3d_board():
    """Create a 3D visualization of the game board using Plotly"""
    x, y, z = [], [], []
    text = []
    colors = []
    
    for i in range(4):
        for j in range(4):
            for k in range(4):
                x.append(i)
                y.append(j)
                z.append(k)
                cell_value = st.session_state.board[i, j, k]
                text.append(cell_value if cell_value != '' else '·')
                if cell_value == 'X':
                    colors.append('#FF6B6B')  # Red for X
                elif cell_value == 'O':
                    colors.append('#4ECDC4')  # Blue for O
                else:
                    colors.append('#95A5A6')  # Gray for empty

    fig = go.Figure(data=[
        go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers+text',
            marker=dict(size=30, color=colors),
            text=text,
            textposition="middle center",
            textfont=dict(size=20, color='white'),
            hoverinfo='none'
        )
    ])

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-1, 4], showgrid=True, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=False),
            yaxis=dict(range=[-1, 4], showgrid=True, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=False),
            zaxis=dict(range=[-1, 4], showgrid=True, zeroline=False, showline=False, 
                      showticklabels=False, showbackground=False),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        scene_camera=dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=1.5, y=1.5, z=1.5)
        )
    )
    
    return fig

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
        st.session_state.board[z, y, x] = st.session_state.current_player
        
        winner = check_winner(st.session_state.board)
        if winner:
            st.session_state.winner = winner
            st.session_state.game_over = True
        elif not np.any(st.session_state.board == ''):
            st.session_state.game_over = True
        else:
            st.session_state.current_player = 'O' if st.session_state.current_player == 'X' else 'X'
            
            # If it's bot's turn, make a move
            if not st.session_state.game_over and st.session_state.game_mode == 'bot' and st.session_state.current_player == 'O':
                make_bot_move()

def reset_game():
    """Reset the game to initial state"""
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False

# UI
st.title("🎮 3D Tic Tac Toe")
st.markdown("**4x4x4 Cube** - Get 4 in a row to win!")

# Game settings
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
    if st.button("🔄 Reset Game", use_container_width=True):
        reset_game()
        st.rerun()

# Game status
if st.session_state.game_over:
    if st.session_state.winner:
        st.success(f"🎉 Player {st.session_state.winner} wins!")
    else:
        st.info("🤝 It's a draw!")
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
        background-color: #FF6B6B !important;
        color: white !important;
    }
    .stButton button:contains("O") {
        background-color: #4ECDC4 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)