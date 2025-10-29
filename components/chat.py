import streamlit as st
from datetime import datetime

def init_chat():
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'chat_expanded' not in st.session_state:
        st.session_state.chat_expanded = False

def add_chat_message(username, message):
    """Add a new chat message"""
    st.session_state.chat_messages.append({
        'username': username,
        'message': message,
        'timestamp': datetime.now()
    })
    
    # Keep only last 50 messages
    if len(st.session_state.chat_messages) > 50:
        st.session_state.chat_messages = st.session_state.chat_messages[-50:]

def display_chat():
    """Display the chat interface"""
    if not st.session_state.user:
        return
    
    st.sidebar.markdown("---")
    
    # Chat toggle
    if st.sidebar.button("💬 Toggle Chat"):
        st.session_state.chat_expanded = not st.session_state.chat_expanded
    
    if not st.session_state.chat_expanded:
        return
    
    st.sidebar.markdown("### Game Chat")
    
    # Display messages
    chat_container = st.sidebar.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            timestamp = msg['timestamp'].strftime("%H:%M")
            is_current_user = msg['username'] == st.session_state.user
            
            st.markdown(
                f"""
                <div style='
                    text-align: {'right' if is_current_user else 'left'};
                    margin: 5px;
                '>
                    <small style='color: gray;'>{timestamp}</small><br/>
                    <div style='
                        display: inline-block;
                        padding: 8px;
                        border-radius: 15px;
                        background-color: {'#E3F2FD' if is_current_user else '#F5F5F5'};
                        max-width: 80%;
                    '>
                        <small><b>{msg['username']}</b></small><br/>
                        {msg['message']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Message input
    message = st.sidebar.text_input("Message", key="chat_input")
    if message:
        add_chat_message(st.session_state.user, message)
        st.sidebar.text_input("Message", value="", key="chat_input_clear")
        st.rerun()

def send_game_event(event_type, data=None):
    """Send a game event to the chat"""
    messages = {
        'move': "{username} made a move at position {position}",
        'win': "🎉 {username} won the game!",
        'draw': "🤝 The game ended in a draw!",
        'power_up': "💫 {username} used {power_up}!",
        'join': "👋 {username} joined the game",
        'leave': "👋 {username} left the game"
    }
    
    if event_type in messages and st.session_state.user:
        message = messages[event_type].format(
            username=st.session_state.user,
            **data if data else {}
        )
        add_chat_message('System', message)