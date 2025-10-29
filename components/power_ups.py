import streamlit as st
import random

POWER_UPS = {
    'extra_move': {
        'name': 'Extra Move',
        'description': 'Make two moves in a row',
        'icon': '⚡',
        'rarity': 'common'
    },
    'swap': {
        'name': 'Position Swap',
        'description': 'Swap any two pieces on the board',
        'icon': '🔄',
        'rarity': 'rare'
    },
    'peek': {
        'name': 'Future Peek',
        'description': "See your opponent's next move",
        'icon': '👁️',
        'rarity': 'uncommon'
    },
    'block': {
        'name': 'Cell Block',
        'description': 'Block a cell from being used',
        'icon': '🚫',
        'rarity': 'uncommon'
    },
    'mirror': {
        'name': 'Mirror Move',
        'description': 'Copy your last move to another position',
        'icon': '🪞',
        'rarity': 'rare'
    }
}

def init_power_ups():
    """Initialize power-ups state for both players"""
    # Initialize power-ups dictionary if not exists
    if 'power_ups' not in st.session_state:
        st.session_state.power_ups = {'X': [], 'O': []}
    elif not isinstance(st.session_state.power_ups, dict):
        st.session_state.power_ups = {'X': [], 'O': []}
    
    # Always ensure both players have lists
    st.session_state.power_ups['X'] = st.session_state.power_ups.get('X', [])
    st.session_state.power_ups['O'] = st.session_state.power_ups.get('O', [])
    
    # Other power-up related states
    if 'blocked_cells' not in st.session_state:
        st.session_state.blocked_cells = set()
    if 'extra_move_active' not in st.session_state:
        st.session_state.extra_move_active = False

def award_power_up(player):
    """Randomly award a power-up based on rarity"""
    rarity_weights = {
        'common': 0.6,
        'uncommon': 0.3,
        'rare': 0.1
    }
    
    available_power_ups = []
    weights = []
    
    for power_up_id, power_up in POWER_UPS.items():
        available_power_ups.append(power_up_id)
        weights.append(rarity_weights[power_up['rarity']])
    
    if random.random() < 0.3:  # 30% chance to get a power-up
        power_up = random.choices(available_power_ups, weights=weights)[0]
        st.session_state.power_ups[player].append(power_up)
        return power_up
    return None

def use_power_up(power_up_id, player):
    """Use a power-up and apply its effect"""
    if power_up_id not in st.session_state.power_ups[player]:
        return False
    
    st.session_state.power_ups[player].remove(power_up_id)
    
    if power_up_id == 'extra_move':
        st.session_state.extra_move_active = True
    elif power_up_id == 'block':
        # Logic for blocking cells implemented in the main game loop
        pass
    elif power_up_id == 'swap':
        # Logic for swapping pieces implemented in the main game loop
        pass
    elif power_up_id == 'peek':
        # Logic for peeking implemented in the bot's move function
        pass
    elif power_up_id == 'mirror':
        # Logic for mirroring moves implemented in the main game loop
        pass
    
    return True

def display_power_ups():
    """Display available power-ups for the current player"""
    # Ensure power-ups are initialized
    if 'power_ups' not in st.session_state:
        init_power_ups()
        
    current_player = st.session_state.current_player
    if not st.session_state.power_ups.get(current_player):
        return
    
    st.markdown("### Power-ups")
    cols = st.columns(len(st.session_state.power_ups[current_player]))
    
    for idx, power_up_id in enumerate(st.session_state.power_ups[st.session_state.current_player]):
        power_up = POWER_UPS[power_up_id]
        with cols[idx]:
            if st.button(
                f"{power_up['icon']} {power_up['name']}",
                help=power_up['description'],
                key=f"power_up_{idx}"
            ):
                use_power_up(power_up_id, st.session_state.current_player)
                st.rerun()

def handle_power_up_effects():
    """Handle the effects of active power-ups"""
    # Extra move handling
    if st.session_state.extra_move_active:
        st.session_state.current_player = st.session_state.current_player  # Keep same player
        st.session_state.extra_move_active = False
        return True
    
    return False