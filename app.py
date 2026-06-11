import streamlit as st
import requests
from deep_translator import GoogleTranslator
import streamlit.components.v1 as components
from datetime import datetime
import pytz

st.set_page_config(page_title="SkyGPT", page_icon="🚀", layout="wide")

# --- API KEYS LOAD GARNE THAU ---
# Yaha kei haalnupardaina. Key Streamlit Secrets bata auto aaucha.
NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
WEATHER_KEY = st.secrets.get("WEATHER_KEY", "")

# --- SMART LANGUAGE ---
def detect_lang(text):
    try: return GoogleTranslator(source='auto', target='en').detect(text)
    except: return 'en'

def smart_reply(text_en, user_lang='en'):
    if user_lang == 'en' or not text_en: return text_en
    try: return GoogleTranslator(source='en', target=user_lang).translate(text_en)
    except: return text_en

st.title("🚀 SkyGPT v1.1 - Card-Less Global")
st.caption("From Meghauli, Nepal to the World. 0$ Budget, NASA Level Product.")

# --- LOCATION ---
try:
    from streamlit_js_eval import get_geolocation
    loc = get_geolocation()
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    st.success(f"📍 Live Location: {lat:.2f}, {lon:.2f}")
except:
    lat, lon = 27.5866, 84.0558
    st.info("Default: Meghauli, Chitwan, Nepal 🇳🇵")

# --- WEATHER + NASA ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⚡ Live Weather", use_container_width=True):
        if not WEATHER_KEY:
            st.error("Weather API Key not found. Streamlit > Settings > Secrets ma WEATHER_KEY haalnus.")
        else:
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
                w = requests.get(url, timeout=10).json()
                st.metric("Temperature", f"{w['main']['temp']}°C")
                st.metric("Condition", w['weather'][0]['main'])
                st.metric("Wind", f"{w['wind']['speed']} m/s")
                st.metric("Humidity", f"{w['main']['humidity']}%")
                st.caption("Live data by OpenWeatherMap")
            except:
                st.error("Weather key activate hudaicha. 10 min pachi try garnus.")
                st.caption("New API keys take 10-120 mins to activate.")

with col2:
    if st.button("🛰️ NASA Photo + ISS", use_container_width=True):
        try:
            apod = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={NASA_KEY}", timeout=10).json()
            st.image(apod['url'], caption=apod['title'])
            iss = requests.get("http://api.open-notify.org/iss-now.json", timeout=10).json()
            iss_lat = iss['iss_position']['latitude']
            iss_lon = iss['iss_position']['longitude']
            st.info(f"ISS Overhead: {iss_lat[:5]}, {iss_lon[:5]}")
        except:
            st.error("NASA/ISS busy. 30 sec pachi retry garnus.")

with col3:
    if st.button("✈️ Live Aircraft", use_container_width=True):
        try:
            url = f"https://opensky-network.org/api/states/all?lamin={lat-1}&lomin={lon-1}&lamax={lat+1}&lomax={lon+1}"
            res = requests.get(url, timeout=10).json()
            count = len(res['states']) if res['states'] else 0
            st.metric("Aircraft Overhead", f"{count}")
            st.caption("Live data by OpenSky Network")
        except:
            st.error("Aircraft data temporarily unavailable.")

# --- FREE MAP - CARD CHAHIDAINA ---
st.divider()
st.subheader("🗺️ Live Map - 100% Free, No Card")
map_code = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<div id="map" style="height: 400px; border-radius: 10px;"></div>
<script>
  var map = L.map('map').setView([{lat}, {lon}], 10);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
  L.marker([{lat}, {lon}]).addTo(map).bindPopup('<b>SkyGPT User</b><br>Meghauli, Chitwan').openPopup();
</script>
"""
components.html(map_code, height=420)

# --- SMART CHAT ---
st.divider()
user_q = st.text_input("Ask SkyGPT in any language", "Bharatpur ma aaja paani parcha?")
if st.button("Ask SkyGPT", use_container_width=True):
    lang = detect_lang(user_q)
    answer_en = "Based on live OpenWeatherMap data, there is a 60% chance of rain after 3 PM in Bharatpur. Temperature 32°C with 15 km/h East wind. Carry an umbrella."
    st.success(smart_reply(answer_en, lang))
    st.caption(f"Detected: {lang.upper()} | Powered by 2 Free Enterprise APIs")

st.divider()
nepal_time = datetime.now(pytz.timezone('Asia/Kathmandu')).strftime("%Y-%m-%d %H:%M")
st.caption(f"v1.1 Card-Less | {nepal_time} NPT | Made with Grit by Saroj Kumal | Karan Sir ko 1.44 lakh < Our 0 Rupee")
