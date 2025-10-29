import streamlit as st

ACHIEVEMENTS = {
    'first_win': {
        'title': 'First Victory',
        'description': 'Win your first game',
        'icon': '🏆'
    },
    'bot_master': {
        'title': 'Bot Master',
        'description': 'Win against the hard bot',
        'icon': '🤖'
    },
    'speed_demon': {
        'title': 'Speed Demon',
        'description': 'Win a game in under 30 seconds',
        'icon': '⚡'
    },
    'diagonal_win': {
        'title': '3D Thinker',
        'description': 'Win with a 3D diagonal',
        'icon': '🎯'
    },
    'undefeated': {
        'title': 'Undefeated',
        'description': 'Win 5 games in a row',
        'icon': '👑'
    }
}

def init_achievements():
    if 'achievements' not in st.session_state:
        st.session_state.achievements = {k: False for k in ACHIEVEMENTS.keys()}
    if 'achievement_times' not in st.session_state:
        st.session_state.achievement_times = {}

def check_achievement(achievement_id):
    if not st.session_state.achievements[achievement_id]:
        st.session_state.achievements[achievement_id] = True
        st.session_state.achievement_times[achievement_id] = st.session_state.current_time
        return True
    return False

def display_achievements():
    st.sidebar.markdown("## Achievements")
    for ach_id, achievement in ACHIEVEMENTS.items():
        unlocked = st.session_state.achievements[ach_id]
        color = "green" if unlocked else "gray"
        time_str = f" (Unlocked: {st.session_state.achievement_times[ach_id].strftime('%Y-%m-%d %H:%M')})" if unlocked else ""
        st.sidebar.markdown(
            f"<div style='color: {color}'>{achievement['icon']} "
            f"<b>{achievement['title']}</b><br/>"
            f"{achievement['description']}{time_str}</div>",
            unsafe_allow_html=True
        )