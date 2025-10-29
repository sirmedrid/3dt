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
    
    st.markdown("---")
    st.markdown("### 💬 Game Chat")
    
    # Create a container for the chat history
    chat_container = st.container()
    
    # Create a form for the message input
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([4, 1])
        with cols[0]:
            message = st.text_input("Message", key="chat_input", label_visibility="collapsed")
        with cols[1]:
            submit = st.form_submit_button("Send")
        
        if submit and message.strip():
            add_chat_message(st.session_state.user, message.strip())
    
    # Display messages in the container (in reverse chronological order)
    with chat_container:
        for msg in reversed(st.session_state.chat_messages):
            timestamp = msg['timestamp'].strftime("%H:%M")
            is_current_user = msg['username'] == st.session_state.user
            
            st.markdown(
                f"""
                <div style='
                    background-color: {'#E3F2FD' if is_current_user else '#F5F5F5'};
                    padding: 10px;
                    border-radius: 10px;
                    margin: 5px;
                    text-align: {'right' if is_current_user else 'left'};
                    max-width: 80%;
                    float: {'right' if is_current_user else 'left'};
                    clear: both;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                '>
                    <small style='color: #666; font-size: 0.8em;'>{msg['username']} • {timestamp}</small><br>
                    {msg['message']}
                </div>
                <div style='clear: both;'></div>
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