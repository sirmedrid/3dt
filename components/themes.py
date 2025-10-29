import streamlit as st

THEMES = {
    'classic': {
        'name': 'Classic',
        'x_color': '#000000',
        'o_color': '#FFFFFF',
        'grid_color': '#CCCCCC',
        'empty_color': '#E0E0E0',
        'background': 'white'
    },
    'neon': {
        'name': 'Neon',
        'x_color': '#FF00FF',
        'o_color': '#00FFFF',
        'grid_color': '#2F2F2F',
        'empty_color': '#1A1A1A',
        'background': 'black'
    },
    'forest': {
        'name': 'Forest',
        'x_color': '#2D5A27',
        'o_color': '#A0C49D',
        'grid_color': '#86A789',
        'empty_color': '#EBF3E8',
        'background': '#F2F9F1'
    },
    'sunset': {
        'name': 'Sunset',
        'x_color': '#FF6B6B',
        'o_color': '#4ECDC4',
        'grid_color': '#FFE66D',
        'empty_color': '#FFF1E6',
        'background': '#FFF8F0'
    }
}

def init_theme():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'classic'

def get_current_theme():
    return THEMES[st.session_state.theme]

def apply_theme(theme_name):
    st.session_state.theme = theme_name
    theme = THEMES[theme_name]
    
    st.markdown(f"""
        <style>
        .main {{
            background-color: {theme['background']};
        }}
        .stButton button {{
            font-size: 24px;
            font-weight: bold;
            height: 60px;
            background-color: {theme['background']};
            color: #333333;
            border: 1px solid {theme['grid_color']};
        }}
        .stButton button:contains("X") {{
            background-color: {theme['x_color']} !important;
            color: {'white' if theme_name != 'classic' else 'white'} !important;
            border: none !important;
        }}
        .stButton button:contains("O") {{
            background-color: {theme['o_color']} !important;
            color: {'white' if theme_name != 'classic' else 'black'} !important;
            border: 2px solid {theme['x_color']} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

def display_theme_selector():
    st.sidebar.markdown("## Theme")
    theme_names = [theme['name'] for theme in THEMES.values()]
    selected_theme = st.sidebar.selectbox(
        "Select Theme",
        theme_names,
        index=list(THEMES.keys()).index(st.session_state.theme)
    )
    
    # Convert theme name back to key
    selected_key = [k for k, v in THEMES.items() if v['name'] == selected_theme][0]
    if selected_key != st.session_state.theme:
        apply_theme(selected_key)