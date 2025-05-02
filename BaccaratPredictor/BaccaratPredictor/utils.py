import streamlit as st

def init_session_state():
    """Initialize session state variables if they don't exist"""
    
    if 'history' not in st.session_state:
        st.session_state.history = []
        
    if 'prediction' not in st.session_state:
        st.session_state.prediction = "B"
        
    if 'confidence' not in st.session_state:
        st.session_state.confidence = 50
