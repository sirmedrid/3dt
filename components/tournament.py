import streamlit as st
from database.manager import DatabaseManager
import json
from datetime import datetime, timedelta

def init_tournament_system():
    if 'tournament' not in st.session_state:
        st.session_state.tournament = {
            'active': False,
            'players': [],
            'matches': [],
            'current_match': None,
            'bracket': [],
            'winner': None
        }

def create_tournament():
    """Create a new tournament with registered players"""
    if len(st.session_state.tournament['players']) < 4:
        st.error("Need at least 4 players to start a tournament!")
        return False
    
    players = st.session_state.tournament['players'].copy()
    random.shuffle(players)
    
    # Create matches
    matches = []
    bracket = []
    round_num = 1
    
    while len(players) > 1:
        round_matches = []
        new_players = []
        
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                match = {
                    'round': round_num,
                    'player1': players[i],
                    'player2': players[i + 1],
                    'winner': None,
                    'status': 'pending'
                }
                round_matches.append(match)
            else:
                new_players.append(players[i])  # Bye round
        
        matches.extend(round_matches)
        bracket.append(round_matches)
        players = new_players
        round_num += 1
    
    st.session_state.tournament['matches'] = matches
    st.session_state.tournament['bracket'] = bracket
    st.session_state.tournament['active'] = True
    st.session_state.tournament['current_match'] = matches[0]
    return True

def display_tournament_bracket():
    """Display the tournament bracket visualization"""
    if not st.session_state.tournament['active']:
        return
    
    st.markdown("## Tournament Bracket")
    
    bracket = st.session_state.tournament['bracket']
    cols = st.columns(len(bracket))
    
    for round_idx, round_matches in enumerate(bracket):
        with cols[round_idx]:
            st.markdown(f"### Round {round_idx + 1}")
            for match in round_matches:
                status_color = {
                    'pending': 'gray',
                    'in_progress': 'blue',
                    'completed': 'green'
                }[match['status']]
                
                winner_text = f"Winner: {match['winner']}" if match['winner'] else ""
                
                st.markdown(f"""
                <div style='border: 1px solid {status_color}; padding: 10px; margin: 5px; border-radius: 5px;'>
                    <p>{match['player1']} vs {match['player2']}</p>
                    <p style='color: {status_color};'>{winner_text}</p>
                </div>
                """, unsafe_allow_html=True)

def handle_tournament_ui():
    """Handle tournament UI and controls"""
    st.markdown("## Tournament System")
    
    if not st.session_state.tournament['active']:
        # Tournament registration
        st.markdown("### Join Tournament")
        if st.session_state.user and st.session_state.user not in st.session_state.tournament['players']:
            if st.button("Join Tournament"):
                st.session_state.tournament['players'].append(st.session_state.user)
        
        # Display registered players
        st.markdown("### Registered Players")
        for player in st.session_state.tournament['players']:
            st.markdown(f"- {player}")
        
        # Start tournament button
        if len(st.session_state.tournament['players']) >= 4:
            if st.button("Start Tournament"):
                create_tournament()
                st.rerun()
    else:
        # Display tournament bracket
        display_tournament_bracket()
        
        # Handle current match
        current_match = st.session_state.tournament['current_match']
        if current_match and current_match['status'] == 'pending':
            st.markdown(f"### Current Match: {current_match['player1']} vs {current_match['player2']}")
            
            # If current user is one of the players
            if st.session_state.user in [current_match['player1'], current_match['player2']]:
                st.markdown("It's your match! Good luck!")
            
            # Auto-advance tournament after match
            if st.session_state.game_over and st.session_state.winner:
                winner = current_match['player1'] if st.session_state.winner == 'X' else current_match['player2']
                current_match['winner'] = winner
                current_match['status'] = 'completed'
                
                # Find next match
                next_match = None
                for match in st.session_state.tournament['matches']:
                    if match['status'] == 'pending':
                        next_match = match
                        break
                
                if next_match:
                    st.session_state.tournament['current_match'] = next_match
                else:
                    st.session_state.tournament['winner'] = winner
                    st.session_state.tournament['active'] = False
                
                st.rerun()
        
        # Display winner if tournament is complete
        if not st.session_state.tournament['active'] and st.session_state.tournament['winner']:
            st.success(f"🏆 Tournament Winner: {st.session_state.tournament['winner']}")
            if st.button("Start New Tournament"):
                st.session_state.tournament = {
                    'active': False,
                    'players': [],
                    'matches': [],
                    'current_match': None,
                    'bracket': [],
                    'winner': None
                }
                st.rerun()