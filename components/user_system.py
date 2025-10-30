import streamlit as st
import numpy as np
from database.manager import DatabaseManager

def init_user_system():
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False

def render_auth_ui():
    # Try to restore session from stored_user or from query params
    if 'user' not in st.session_state:
        # First try stored_user from session_state
        if 'stored_user' in st.session_state and st.session_state.stored_user:
            st.session_state.user = st.session_state.stored_user
        else:
            # Fallback: check URL query params (used to persist 'remember me')
            try:
                params = st.experimental_get_query_params()
                if 'user' in params and params['user']:
                    st.session_state.user = params['user'][0]
                    # also mirror into stored_user for this session
                    st.session_state.stored_user = st.session_state.user
            except Exception:
                # experimental_get_query_params may not be available in some envs
                pass
    
    if st.session_state.user:
        st.sidebar.markdown(f"## Welcome, {st.session_state.user}!")
        
        # Add admin section with seed button
        if st.session_state.is_admin or st.session_state.user == "admin":
            st.session_state.is_admin = True
            st.sidebar.markdown("---")
            st.sidebar.markdown("## Admin Section")
            
            # Admin controls
            if st.sidebar.button("🌱 Seed Database"):
                try:
                    users_created = DatabaseManager.seed_database()
                    st.sidebar.success(f"Database seeded successfully! Created {users_created} sample users.")
                except Exception as e:
                    st.sidebar.error(f"Error seeding database: {str(e)}")
            
            # Make user admin
            with st.sidebar.form("make_admin_form"):
                st.markdown("### Make User Admin")
                username_to_admin = st.text_input("Username")
                if st.form_submit_button("Make Admin"):
                    if DatabaseManager.make_admin(username_to_admin):
                        st.success(f"Made {username_to_admin} an admin!")
                    else:
                        st.error(f"User {username_to_admin} not found!")
        
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.stored_user = None
            st.session_state.is_admin = False
            st.rerun()
        return True
    
    st.sidebar.markdown("## Login/Signup")
    
    if st.session_state.show_signup:
        with st.sidebar.form("signup_form"):
            st.markdown("### Create Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Sign Up"):
                if password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters!")
                else:
                    try:
                        DatabaseManager.create_user(username, password)
                        st.success("Account created! Please log in.")
                        st.session_state.show_signup = False
                        st.rerun()
                    except Exception as e:
                        st.error("Username already taken!")
        
        if st.sidebar.button("Back to Login"):
            st.session_state.show_signup = False
            st.rerun()
    
    else:
        with st.sidebar.form("login_form"):
            st.markdown("### Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")
            
            if st.form_submit_button("Login"):
                if DatabaseManager.verify_user(username, password):
                    st.session_state.user = username
                    if remember_me:
                        # Persist in-session and in the URL so refresh keeps the user
                        st.session_state.stored_user = username
                        try:
                            st.experimental_set_query_params(user=username)
                        except Exception:
                            # Not critical; just keep stored_user in session
                            pass
                    st.rerun()
                else:
                    st.error("Invalid username or password!")
        
        if st.sidebar.button("Create Account"):
            st.session_state.show_signup = True
            st.rerun()
    
    return False

def display_user_stats():
    if not st.session_state.user:
        return
    
    stats = DatabaseManager.get_user_stats(st.session_state.user)
    if not stats:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Your Statistics")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Total Games", stats['total_games'])
        st.metric("Wins", stats['wins'])
        st.metric("Draws", stats['draws'])
    
    with col2:
        st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
        st.metric("Losses", stats['losses'])
        st.metric("Avg Moves", f"{stats['avg_moves']:.1f}")
    
    hours_played = stats['total_time'] / 3600
    st.sidebar.metric("Time Played", f"{hours_played:.1f} hours")