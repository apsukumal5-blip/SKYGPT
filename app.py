"""
PROJECT: SkyGPT World AI v8.0 PRODUCTION
CREATOR: Saroj Kumal
MISSION: Global Earth Intelligence Platform
ARCHITECTURE: Modular, Cached, Scalable
"""
import streamlit as st
from streamlit_chat import message
from utils import detect_location, get_weather_intel, assess_flood_risk, assess_landslide_risk
from utils import get_earthquake_intel, get_eonet_intel, get_space_intel
from brain import get_skygpt_response
from datetime import datetime

# --- 1. APP CONFIG ---
st.set_page_config(page_title="SkyGPT World AI", page_icon="🌍", layout="wide")
NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
CREATOR = "Saroj Kumal"

# --- 2. UI: PROFESSIONAL HEADER + CSS ---
st.markdown("""
<style>
  .main-header {text-align: center; background: radial-gradient(circle, #1E3A8A, #0B0F19);
                  padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem; border: 1px solid #4A90E2;}
  .stChatMessage {background-color: #151B2B; border-radius: 10px;}
  .loading-text {text-align: center; color: #4A90E2; animation: pulse 2s infinite;}
   @keyframes pulse {0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="main-header">
    <h1 style='margin:0;'>🌍 SkyGPT World AI</h1>
    <p style='margin:0; opacity:0.8;'>Ask Earth Anything | Built by {CREATOR}</p>
</div>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR: SPACE MODULE ---
with st.sidebar:
    st.header("🚀 Space Intelligence")
    with st.spinner("Loading NASA Data..."):
        space_data = get_space_intel(NASA_KEY)
    if 'iss' in space_data:
        st.metric("ISS Current Location", f"{space_data['iss']['latitude'][:5]}, {space_data['iss']['longitude'][:5]}")
    if 'apod' in space_data:
        st.image(space_data['apod']['url'], caption=space_data['apod']['title'])
        with st.expander("NASA APOD Details"): st.write(space_data['apod']['desc'])

    st.divider()
    st.header("🌋 Global Alerts")
    quakes = get_earthquake_intel()
    if quakes: st.write(f"**Latest Quake:** M{quakes[0]['mag']} - {quakes[0]['place']}")
    eonet = get_eonet_intel()
    if eonet['wildfire']: st.write(f"**Active Wildfire:** {eonet['wildfire'][0]}")

# --- 4. CHAT INTERFACE: MEMORY + UX ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Namaste! I am SkyGPT World AI. Ask me about weather, floods, earthquakes, or space for any location worldwide. Eg: 'Tokyo ma typhoon ko risk cha?'"}]

for i, msg in enumerate(st.session_state.messages):
    message(msg["content"], is_user=msg["role"] == "user", key=f"msg_{i}", avatar_style="initials")

# --- 5. CORE LOGIC: USER INPUT ---
if prompt := st.chat_input("Ask Earth Anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True, key=f"user_{len(st.session_state.messages)}")

    with st.status("🧠 SkyGPT Analyzing...", expanded=False) as status:
        st.write("🌐 Detecting location...")
        loc_data = detect_location(prompt)

        if not loc_data['found']:
            response = "📍 Location detect bhayena. Please specify a city or country. Eg: 'Lukla ko weather k cha?'"
            status.update(label="Location needed", state="error")
        else:
            st.write(f"🛰️ Fetching data for {loc_data['name']}...")
            weather = get_weather_intel(loc_data['lat'], loc_data['lon'])
            disasters = {"earthquake": get_earthquake_intel(), "eonet": get_eonet_intel()}
            space = get_space_intel(NASA_KEY)

            st.write("⚡ Calculating risks...")
            context = {
                "location": loc_data['name'], "coords": f"{loc_data['lat']}, {loc_data['lon']}",
                "weather": weather, "flood_risk": assess_flood_risk(weather),
                "landslide_risk": assess_landslide_risk(weather, loc_data['name']),
                "disasters": disasters, "space": space, "timestamp": str(datetime.now(timezone.utc))
            }

            st.write("🤖 Generating AI response...")
            response = get_skygpt_response(prompt, context, st.session_state.messages)
            status.update(label="Analysis Complete", state="complete")

    st.session_state.messages.append({"role": "assistant", "content": response})
    message(response, key=f"bot_{len(st.session_state.messages)}")

# --- 6. FOOTER ---
st.divider()
st.markdown(f"""
<div style='text-align: center; color: #6B7280; font-size: 12px;'>
    <b>SkyGPT World AI</b> | Created by {CREATOR} | Powered by Google Gemini <br>
    Data Sources: NASA, Open-Meteo, OpenStreetMap, USGS <br>
    <i>Ask Earth Anything</i>
</div>
""", unsafe_allow_html=True)
