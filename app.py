"""
PROJECT: SkyGPT World AI
CREATOR: Saroj Kumal
MISSION: Global AI-powered Earth Intelligence Platform
BRAIN: Google Gemini 1.5 Flash
DATA: NASA, Open-Meteo, OpenStreetMap, USGS, EONET
"""
import streamlit as st
import requests
import google.generativeai as genai
from streamlit_chat import message
from datetime import datetime, timezone
import json

# --- 1. APP CONFIG & SECRETS ---
st.set_page_config(
    page_title="SkyGPT World AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GEMINI_KEY = st.secrets.get("GEMINI_KEY")
NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
CREATOR = "Saroj Kumal"

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    MODEL = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ AI Brain OFF. Please add GEMINI_KEY in Streamlit Secrets.")
    st.stop()

# --- 2. UI: DARK THEME & HEADER ---
st.markdown("""
<style>
   .main-header {text-align: center; background: linear-gradient(90deg, #0E1117, #1E3A8A, #0E1117);
                  padding: 1rem; border-radius: 10px; margin-bottom: 1rem;}
   .st-emotion-cache-16txtl3 {padding: 1rem 2rem 1rem;}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="main-header">
    <h1>🌍 SkyGPT World AI</h1>
    <p>Ask Earth Anything | Built by {CREATOR}</p>
</div>
""", unsafe_allow_html=True)

# --- 3. CORE MODULES: DATA SOURCES ---

def get_geocoding(location_text):
    """OpenStreetMap Geocoding: Free, Worldwide"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location_text}&format=json&limit=1"
        res = requests.get(url, headers={'User-Agent': 'SkyGPT-SarojKumal'}, timeout=5).json()
        if res:
            return float(res[0]['lat']), float(res[0]['lon']), res[0]['display_name'].split(',')[0]
    except: return None, None, "Kathmandu"
    return 27.7172, 85.3240, "Kathmandu"

def get_weather_intel(lat, lon):
    """Open-Meteo: Free Weather, Rain, Wind. No Key Needed."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation_probability,rain&daily=precipitation_sum&timezone=auto"
        data = requests.get(url, timeout=5).json()
        current = data['current_weather']
        rain_prob = data['hourly']['precipitation_probability'][0]
        rain_sum = data['daily']['precipitation_sum'][0]
        return {
            "temp": f"{current['temperature']}°C", "wind": f"{current['windspeed']} km/h",
            "rain_prob": f"{rain_prob}%", "rain_24h": f"{rain_sum} mm", "code": current['weathercode']
        }
    except: return {"error": "Weather data unavailable"}

def get_disaster_intel(lat, lon):
    """NASA EONET: Wildfire, Cyclone, Flood. USGS: Earthquake."""
    intel = {}
    try: # NASA EONET
        eonet = requests.get("https://eonet.gsfc.nasa.gov/api/v3/events?limit=5&status=open", timeout=5).json()
        intel['wildfire'] = [e['title'] for e in eonet['events'] if e['categories'][0]['id'] == 'wildfires']
        intel['cyclone'] = [e['title'] for e in eonet['events'] if e['categories'][0]['id'] == 'severeStorms']
    except: pass
    try: # USGS Earthquake
        quake = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson", timeout=5).json()
        intel['earthquake'] = [f"M{q['properties']['mag']} - {q['properties']['place']}" for q in quake['features'][:3]]
    except: pass
    return intel

def get_nasa_intel():
    """NASA APOD, ISS Location"""
    intel = {}
    try:
        iss = requests.get("http://api.open-notify.org/iss-now.json", timeout=3).json()
        intel['iss'] = f"Lat: {iss['iss_position']['latitude']}, Lon: {iss['iss_position']['longitude']}"
    except: pass
    try:
        apod = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={NASA_KEY}", timeout=5).json()
        intel['apod'] = {"title": apod['title'], "url": apod['url']}
    except: pass
    return intel

# --- 4. AI BRAIN: GEMINI CORE LOGIC ---
def ask_skygpt_brain(prompt, context_data):
    """Core LLM function with Rules from Spec"""
    system_prompt = f"""
    You are SkyGPT World AI, created by Saroj Kumal. You are a professional Earth Intelligence Assistant.
    RULES:
    1. Never invent live data. Use ONLY this context: {json.dumps(context_data)}
    2. Explain in simple language. English, Nepali, Hindi support.
    3. Mention uncertainty if data is incomplete: "Data anusar..."
    4. For weather disasters, ALWAYS give safety guidance.
    5. Be concise and professional. Use ✅ ❌ ⚠️ emojis for risk levels.
    6. Respond in the user's language.
    7. For Flood/Landslide: Use Risk levels: Low, Moderate, High.

    CONTEXT DATA: {json.dumps(context_data)}
    USER QUESTION: {prompt}
    """
    try:
        response = MODEL.generate_content(system_prompt)
        return response.text
    except Exception as e:
        return f"🧠 AI Brain Error: {e}. Check Gemini API Key."

# --- 5. INTELLIGENCE ENGINES: RISK ASSESSMENT ---

def assess_flood_risk(weather):
    """CORE FEATURE 3: Flood Risk Intelligence"""
    if 'error' in weather: return "Data unavailable"
    rain_24h = float(weather['rain_24h'].split()[0])
    if rain_24h > 100: return "🔴 High: >100mm rain. Flash flood risk. Avoid rivers, move to higher ground."
    elif rain_24h > 50: return "🟠 Moderate: 50-100mm rain. Waterlogging possible. Stay alert."
    else: return "🟢 Low: <50mm rain. No immediate flood risk."

def assess_landslide_risk(weather, location):
    """CORE FEATURE 4: Landslide Risk"""
    if 'error' in weather: return "Data unavailable"
    rain_24h = float(weather['rain_24h'].split()[0])
    mountain_keywords = ['lukla', 'everest', 'pokhara', 'manang', 'mustang', 'himal']
    if any(k in location.lower() for k in mountain_keywords) and rain_24h > 75:
        return "🔴 High: Heavy rain in mountain region. Landslide risk. Avoid travel on hilly roads."
    elif rain_24h > 40: return "🟠 Moderate: Monitor slopes if continuous rain."
    else: return "🟢 Low: No significant landslide risk."

# --- 6. MAIN APP: CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Namaste! I am SkyGPT World AI. Ask me about weather, floods, earthquakes, mountains, or space. Eg: 'Lukla ma aaja landslide risk cha?'"}]

# Display chat history
for i, msg in enumerate(st.session_state.messages):
    message(msg["content"], is_user=msg["role"] == "user", key=str(i))

# Chat input
if prompt := st.chat_input("Ask Earth Anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True, key=str(len(st.session_state.messages)))

    with st.spinner("🧠 SkyGPT Brain analyzing Earth data..."):
        # Step 1: Get Location
        lat, lon, loc_name = get_geocoding(prompt)

        # Step 2: Gather All Intel
        context_data = {
            "location": loc_name, "coords": f"{lat}, {lon}",
            "weather": get_weather_intel(lat, lon),
            "disasters": get_disaster_intel(lat, lon),
            "nasa": get_nasa_intel(),
            "risk_analysis": {
                "flood": assess_flood_risk(get_weather_intel(lat, lon)),
                "landslide": assess_landslide_risk(get_weather_intel(lat, lon), loc_name)
            }
        }

        # Step 3: Ask Gemini Brain
        response = ask_skygpt_brain(prompt, context_data)
        st.session_state.messages.append({"role": "assistant", "content": response})
        message(response, key=str(len(st.session_state.messages)))

# --- 7. FOOTER ---
st.divider()
st.markdown(f"""
<div style='text-align: center; color: grey; font-size: 12px;'>
    <b>SkyGPT World AI</b> | Created by {CREATOR} | Powered by Google Gemini <br>
    Data Sources: NASA, Weather APIs, OpenStreetMap, USGS <br>
    <i>Ask Earth Anything</i>
</div>
""", unsafe_allow_html=True)
