import streamlit as st
import streamlit.components.v1 as components
import requests
import google.generativeai as genai
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="SkyGPT World AI", page_icon="🌍", layout="wide")

# --- UI STYLE ---
st.markdown("""
    <style>
    .stApp { background: #0b0e14; color: #ffffff; }
    h1 { color: #ffffff; text-align: center; }
    .chat-container { border: 1px solid #333; padding: 20px; border-radius: 10px; background: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# --- SETUP & SECURITY ---
def setup_ai():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error("AI Brain connection failed. Check your API Keys in Secrets.")
        return None

model = setup_ai()

# --- DATA LAYER ---
@st.cache_data(ttl=900) # Cache for 15 minutes
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    return requests.get(url, timeout=5).json()

# --- CORE LOGIC ---
def get_ai_response(question, context):
    system_prompt = """
    You are SkyGPT, a professional Earth Intelligence Assistant by Saroj Kumal.
    Mission: Provide accurate info on weather, disasters, mountains, and space.
    Rules: 
    - Always use provided data.
    - If data is missing, admit uncertainty.
    - Be concise, professional, and provide safety guidance for risks.
    - Respond in the language of the user (Nepali, Hindi, or English).
    """
    response = model.generate_content(f"{system_prompt} \n Data: {context} \n Question: {question}")
    return response.text

# --- APP LAYOUT ---
st.title("🌍 SkyGPT World AI")
st.markdown("<p style='text-align: center;'>Ask Earth Anything | Built by Saroj Kumal</p>", unsafe_allow_html=True)

question = st.text_input("Search Earth Intel:", placeholder="e.g., Will it rain in Chitwan? Is the ISS visible?")

if question:
    with st.spinner("Analyzing global Earth data..."):
        # Default Location: Kathmandu
        data = get_weather(27.7172, 85.3240)
        
        if model:
            answer = get_ai_response(question, data)
            st.markdown(f"<div class='chat-container'>{answer}</div>", unsafe_allow_html=True)
        else:
            st.warning("AI Brain is offline.")

# --- FOOTER ---
st.divider()
st.markdown("""
    **SkyGPT World AI** | Built by Saroj Kumal  
    *Powered by Google Gemini | Data: NASA, NOAA, Open-Meteo*
    """, unsafe_allow_html=True)
        
