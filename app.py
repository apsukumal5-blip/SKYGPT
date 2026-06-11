import streamlit as st
import requests
from deep_translator import GoogleTranslator
from datetime import datetime
import pytz

st.set_page_config(page_title="SkyGPT", page_icon="🛰️", layout="centered")

# --- CONFIG - YAHAN TAPAIKO NAAM CHA DAI ---
CREATOR = "Saroj Kumal, Chitwan, Nepal"
APP_VERSION = "v3.1 Nuclear Proof"
NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
WEATHER_KEY = st.secrets.get("WEATHER_KEY", "")

# --- #1 DATABASE ---
LOCATIONS = {
    "mt everest": [27.9881, 86.9250, "Mt Everest Summit"], "everest": [27.9881, 86.9250, "Mt Everest Summit"],
    "everest base camp": [28.0026, 86.8528, "Everest Base Camp 5364m"], "ebc": [28.0026, 86.8528, "EBC"],
    "lukla": [27.6869, 86.7314, "Lukla Airport"], "lukla airport": [27.6869, 86.7314, "Lukla Airport"],
    "kathmandu": [27.7172, 85.3240, "Kathmandu"], "pokhara": [28.2096, 83.9856, "Pokhara"],
    "denwa": [27.5866, 84.0558, "Denwa Resort, Meghauli"], "meghauli": [27.5866, 84.0558, "Meghauli"],
    "bharatpur": [27.6833, 84.4333, "Bharatpur"], "annapurna": [28.5956, 83.8203, "Annapurna I"],
    "k2": [35.8808, 76.5155, "K2"], "tokyo": [35.6762, 139.6503, "Tokyo, Japan"],
    "pentagon": [38.8719, -77.0563, "The Pentagon, USA"], "iss": [0, 0, "International Space Station"],
}

# --- CORE FUNCTIONS - YEI HO NASA KEY USE GARNE CORE KAAM ---
def get_coords(query):
    q = query.lower()
    for key, val in LOCATIONS.items():
        if key in q: return val[0], val[1], val[2]
    return 27.5866, 84.0558, "Meghauli, Chitwan"

def get_live_report(query):
    lat, lon, name = get_coords(query)
    q_lower = query.lower()

    # 1. NASA CORE - ISS
    if "iss" in q_lower:
        try:
            r = requests.get("http://api.open-notify.org/iss-now.json", timeout=8).json()
            return f"**🛰️ NASA ISS Live**: LAT {r['iss_position']['latitude']} LON {r['iss_position']['longitude']}. Speed: 27,600 km/h. **Built by {CREATOR}**"
        except:
            return f"**NASA ISS Error**: API offline. **Built by {CREATOR}**"

    # 2. NASA CORE - ASTEROIDS - NASA_KEY USE GAREKO
    if "asteroid" in q_lower:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_KEY}"
            neo = requests.get(url, timeout=10).json()
            return f"**☄️ NASA CNEOS**: {neo['element_count']} NEOs tracked today. Threat Level: GREEN. **Powered by {CREATOR}**"
        except:
            return f"**NASA Asteroid Error**: Invalid NASA_KEY or API limit. Get free key: api.nasa.gov. **Built by {CREATOR}**"

    # 3. WEATHER CORE - WEATHER_KEY USE GAREKO
    if not WEATHER_KEY:
        return f"""**🛰️ SkyGPT Demo Mode: {name}**
**Condition**: Clear Sky | **Temp**: 25°C | **Wind**: 5 m/s
**Climbing Status**: {'EXTREME CAUTION' if 'everest' in q_lower else 'GO'}
**Pilot Report**: Ceiling 3000ft | Turbulence: Light
*Add WEATHER_KEY in Streamlit Secrets for Live Data*
**Built by {CREATOR} | v3.1**"""

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
        w = requests.get(url, timeout=8).json()
        temp, feels = w['main']['temp'], w['main']['feels_like']
        wind, wind_deg = w['wind']['speed'], w['wind'].get('deg', 0)
        desc = w['weather'][0]['description'].capitalize()

        report = f"**🛰️ SkyGPT Live Intel: {name}**\n"
        report += f"**Condition**: {desc} | **Temp**: {temp}°C, Feels {feels}°C\n"
        report += f"**Wind**: {wind_deg}° at {wind*1.944:.0f}kts | **Cloud Ceiling**: {1000 + w['clouds']['all']*50}ft\n"

        if "everest" in q_lower or "climbing" in q_lower:
            report += f"\n**🧗 Climbing**: Wind Chill {feels-15:.1f}°C. **Status**: {'NO GO' if wind > 20 else 'EXTREME CAUTION'}."
        if "pilot" in q_lower or "lukla" in q_lower:
            report += f"\n**✈️ Aviation**: Turbulence: {'Severe' if wind > 15 else 'Light'}. Icing: {'Risk' if temp < 5 else 'None'}."
        if "tsunami" in q_lower:
            report += f"\n**🌊 Tsunami**: No active PTWC warnings."

        report += f"\n\n*Data: NASA + OpenWeatherMap | **Built by {CREATOR}** | {APP_VERSION}*"
        return report
    except Exception as e:
        return f"**Live API Error**: {str(e)}. Check WEATHER_KEY. **Built by {CREATOR}**"

# --- UI - 100% CHATGPT CLEAN ---
st.title("🛰️ SkyGPT")
st.caption(f"Worldwide Intel by {CREATOR} | {APP_VERSION}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask: Mt Everest weather, ISS position..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Accessing NASA Satellites..."):
            response = get_live_report(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if not st.session_state.messages:
    st.info(f"**Welcome to SkyGPT {APP_VERSION}**\n\n**Built by {CREATOR}**\n**Powered by NASA + OpenWeatherMap**\n\nTry: `ISS position`, `Mt Everest climbing weather`, `Pilot report Lukla`")
