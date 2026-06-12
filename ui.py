"""
SkyGPT World AI v3.0 - UI Components
CREATOR: Saroj Kumal
Handles: Chat UI, Sidebar, Animations, Mobile
"""
import streamlit as st
from streamlit_chat import message

def render_header():
    st.markdown("""
    <style>
       .main-header {text-align: center; background: radial-gradient(circle at top, #1E3A8A, #030712);
                      padding: 2rem; border-radius: 20px; margin-bottom: 1rem; border: 1px solid #4A90E2;}
       .stChatMessage {background-color: #111827; border: 1px solid #1F2937; border-radius: 12px;}
       .typing-indicator {display: flex; align-items: center; color: #4A90E2; font-style: italic;}
       .typing-dot {width: 8px; height: 8px; margin: 0 2px; background: #4A90E2; border-radius: 50%; animation: bounce 1.4s infinite;}
        @keyframes bounce {0%, 80%, 100% {transform: scale(0);} 40% {transform: scale(1);}}
       .st-emotion-cache-16txtl3 {padding: 1rem 1rem 10rem;}
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size:2.5rem;'>🌍 SkyGPT World AI</h1>
        <p style='margin:0; opacity:0.8; font-size:1.1rem;'>Ask Earth Anything | Created by Saroj Kumal</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(space_data, quake_data):
    with st.sidebar:
        st.header("🚀 Live Space Data")
        if space_data.get('iss'):
            iss = space_data['iss']['iss_position']
            st.metric("ISS Location", f"{iss['latitude'][:6]}, {iss['longitude'][:6]}")

        st.divider()
        st.header("🌋 Global Alerts")
        if quake_data:
            st.warning(f"M{quake_data[0]['mag']} Earthquake: {quake_data[0]['place']}")

        st.divider()
        st.caption("v3.0 | Saroj Kumal | Gemini + NASA + USGS")

def render_chat_history(messages):
    for i, msg in enumerate(messages):
        message(msg["content"], is_user=msg["role"] == "user", key=f"msg_{i}",
                avatar_style="thumbs" if msg["role"] == "user" else "bottts")

def render_typing_indicator():
    return st.markdown("""
    <div class="typing-indicator">
        <span>SkyGPT Analyzing</span>
        <div class="typing-dot"></div><div class="typing-dot" style="animation-delay:0.2s"></div>
        <div class="typing-dot" style="animation-delay:0.4s"></div>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #6B7280; font-size: 12px;'>
        <b>SkyGPT World AI v3.0</b> | Created by Saroj Kumal | Powered by Google Gemini <br>
        Data Sources: NASA, Open-Meteo, OpenStreetMap, USGS <br>
        <i>Ask Earth Anything</i>
    </div>
    """, unsafe_allow_html=True)
