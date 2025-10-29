import streamlit as st
import numpy as np

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False

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

def reset_game():
    """Reset the game to initial state"""
    st.session_state.board = np.full((4, 4, 4), '', dtype=object)
    st.session_state.current_player = 'X'
    st.session_state.winner = None
    st.session_state.game_over = False

# UI
st.title("🎮 3D Tic Tac Toe")
st.markdown("**4x4x4 Cube** - Get 4 in a row to win!")

# Game status
col1, col2 = st.columns(2)
with col1:
    if st.session_state.game_over:
        if st.session_state.winner:
            st.success(f"🎉 Player {st.session_state.winner} wins!")
        else:
            st.info("🤝 It's a draw!")
    else:
        st.info(f"Current Player: **{st.session_state.current_player}**")

with col2:
    if st.button("🔄 Reset Game", use_container_width=True):
        reset_game()
        st.rerun()

st.divider()

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
</style>
""", unsafe_allow_html=True)