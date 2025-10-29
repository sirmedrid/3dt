import streamlit as st
import numpy as np
from streamlit_extras.switch_page_button import switch_page
import time

def create_tutorial():
    steps = [
        {
            "title": "Welcome to 3D Tic Tac Toe!",
            "content": """
            This tutorial will guide you through the basics of playing 3D Tic Tac Toe.
            The game is played on a 4x4x4 cube, giving you many more possibilities than traditional Tic Tac Toe!
            """,
            "board": np.full((4, 4, 4), '', dtype=object)
        },
        {
            "title": "Making Moves",
            "content": """
            Click on any empty cell to make your move. The cells are organized in 4 layers,
            and you can see the 3D view above to understand how they connect.
            Let's try making a move in the center of the first layer.
            """,
            "board": create_example_board([(1, 1, 0, 'X')])
        },
        {
            "title": "Winning Combinations",
            "content": """
            You can win by getting 4 in a row in any direction:
            - Horizontally (within a layer)
            - Vertically (across layers)
            - Diagonally (both in 2D and 3D)
            Here's an example of a horizontal win:
            """,
            "board": create_example_board([(0, 0, i, 'X') for i in range(4)])
        },
        {
            "title": "3D Diagonals",
            "content": """
            The most interesting wins come from 3D diagonals!
            Here's an example of a diagonal win across layers:
            """,
            "board": create_example_board([(i, i, i, 'O') for i in range(4)])
        },
        {
            "title": "Strategy Tips",
            "content": """
            1. Think in three dimensions
            2. Watch out for diagonal threats
            3. Try to control the center positions
            4. Block your opponent's potential wins
            
            Now you're ready to play! Good luck!
            """,
            "board": np.full((4, 4, 4), '', dtype=object)
        }
    ]
    
    return steps

def create_example_board(moves):
    board = np.full((4, 4, 4), '', dtype=object)
    for z, y, x, player in moves:
        board[z, y, x] = player
    return board

def run_tutorial():
    if 'tutorial_step' not in st.session_state:
        st.session_state.tutorial_step = 0
    
    steps = create_tutorial()
    step = steps[st.session_state.tutorial_step]
    
    st.markdown(f"## {step['title']}")
    st.markdown(step['content'])
    
    # Show example board state
    st.session_state.board = step['board']
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.tutorial_step > 0:
            if st.button("← Previous"):
                st.session_state.tutorial_step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.tutorial_step < len(steps) - 1:
            if st.button("Next →"):
                st.session_state.tutorial_step += 1
                st.rerun()
        elif st.button("Start Playing!"):
            st.session_state.tutorial_completed = True
            switch_page("main")