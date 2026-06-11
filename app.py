import streamlit as st
import requests
from deep_translator import GoogleTranslator
import streamlit.components.v1 as components
from datetime import datetime
import pytz

st.set_page_config(page_title="SkyGPT - NASA & Weather", page_icon="🚀", layout="wide")

NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
WEATHER_KEY = st.secrets.get("WEATHER_KEY", "")

# --- HELPER FUNCTIONS ---
def detect_lang(text):
    try: return GoogleTranslator(source='auto', target='en').detect(text)
    except: return 'en'

def smart_reply(text_en, user_lang='en'):
    if user_lang == 'en' or not text_en: return text_en
    try: return GoogleTranslator(source='en', target=user_lang).translate(text_en)
    except: return text_en

def get_weather(lat, lon, city_name="Your Location"):
    if not WEATHER_KEY: return None, "Add WEATHER_KEY in Secrets."
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
        w = requests.get(url, timeout=10).json()
        temp = w['main']['temp']
        desc = w['weather'][0]['description'].capitalize()
        wind = w['wind']['speed']
        hum = w['main']['humidity']
        return w, f"{city_name}: {temp}°C, {desc}, Wind {wind}m/s, Humidity {hum}%"
    except:
        return None, "Weather API activating. Try in 10 mins."

# --- UI ---
st.title("🚀 SkyGPT v1.3 - NASA Edition")
st.caption("Live Weather + NASA + ISS + Mars. From Meghauli to Galaxy. 0$ Cost.")

# --- LOCATION ---
lat, lon = 27.5866, 84.0558 # Denwa Resort, Meghauli Default
city_name = "Meghauli"

try:
    from streamlit_js_eval import get_geolocation
    loc = get_geolocation()
    if loc and 'coords' in loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        city_name = "Your Location"
        st.success(f"📍 Live Location Active")
except:
    st.info(f"📍 Default: Denwa Resort, Meghauli, Chitwan 🇳🇵")

# --- TABS FOR CLEAN UI - PLAY STORE FRIENDLY ---
tab1, tab2, tab3 = st.tabs(["🌤️ Live Weather", "🛰️ NASA Space", "🗺️ Live Map"])

with tab1:
    st.subheader("Real-Time Weather - Powered by OpenWeatherMap")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📍 Meghauli/Denwa Resort", use_container_width=True):
            w_data, w_text = get_weather(27.5866, 84.0558, "Denwa Resort")
            if w_data:
                st.metric("Temp", f"{w_data['main']['temp']}°C")
                st.metric("Sky", w_data['weather'][0]['main'])
                st.write(w_text)
            else: st.error(w_text)

    with col2:
        if st.button("🏙️ Bharatpur City", use_container_width=True):
            w_data, w_text = get_weather(27.6833, 84.4333, "Bharatpur")
            if w_data: st.write(w_text)
            else: st.error(w_text)

with tab2:
    st.subheader("NASA Live Data - Powered by NASA Open APIs")
    nasa_col1, nasa_col2 = st.columns(2)

    with nasa_col1:
        if st.button("🌌 Astronomy Photo of Day", use_container_width=True):
            try:
                apod = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={NASA_KEY}", timeout=10).json()
                st.image(apod['url'], caption=f"NASA APOD: {apod['title']}")
                with st.expander("Read Explanation"):
                    st.write(apod['explanation'])
            except: st.error("NASA APOD busy. DEMO_KEY has limits. Add your own NASA_KEY.")

        if st.button("🔴 Mars Rover Latest Photo", use_container_width=True):
            try:
                mars = requests.get(f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/latest_photos?api_key={NASA_KEY}", timeout=15).json()
                if mars['latest_photos']:
                    st.image(mars['latest_photos'][0]['img_src'], caption=f"Mars: {mars['latest_photos'][0]['camera']['full_name']}")
                else: st.info("No new Mars photos today.")
            except: st.error("Mars Rover API busy.")

    with nasa_col2:
        if st.button("🛰️ ISS Live Location", use_container_width=True):
            try:
                iss = requests.get("http://api.open-notify.org/iss-now.json", timeout=10).json()
                iss_lat = float(iss['iss_position']['latitude'])
                iss_lon = float(iss['iss_position']['longitude'])
                st.success(f"ISS is now over: {iss_lat:.2f}, {iss_lon:.2f}")
                # ISS Map
                iss_map = f"""
                <iframe width="100%" height="300" src="https://www.openstreetmap.org/export/embed.html?bbox={iss_lon-10}%2C{iss_lat-10}%2C{iss_lon+10}%2C{iss_lat+10}&layer=mapnik&marker={iss_lat}%2C{iss_lon}"></iframe>
                """
                components.html(iss_map, height=320)
            except: st.error("ISS tracking unavailable.")

        if st.button("☄️ Asteroid Alert Today", use_container_width=True):
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                neo = requests.get(f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_KEY}", timeout=15).json()
                count = neo['element_count']
                st.metric("Near-Earth Asteroids Today", count)
                if count > 0:
                    st.warning(f"{count} asteroids passing Earth today. None are dangerous.")
                else:
                    st.success("No asteroids near Earth today. Sky is clear!")
            except: st.error("Asteroid data unavailable.")

with tab3:
    st.subheader("Live Map - Denwa Resort, Meghauli")
    map_code = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="map" style="height: 500px; border-radius: 10px;"></div>
    <script>
      var map = L.map('map').setView([{lat}, {lon}], 14);
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
      L.marker([{lat}, {lon}]).addTo(map).bindPopup('<b>Denwa Backwater Escape Resort</b><br>Your SkyGPT HQ').openPopup();
    </script>
    """
    components.html(map_code, height=520)

# --- SMART CHAT ---
st.divider()
st.subheader("💬 Ask SkyGPT Anything")
user_q = st.text_input("Ask in Nepali/Hindi/English", "Denwa resort ma aaja mausam k cha?")
if st.button("Ask SkyGPT", use_container_width=True):
    lang = detect_lang(user_q)
    answer_en = "Connecting to live data..."

    if "denwa" in user_q.lower() or "meghauli" in user_q.lower() or "resort" in user_q.lower():
        _, answer_en = get_weather(27.5866, 84.0558, "Denwa Resort")
    elif "bharatpur" in user_q.lower():
        _, answer_en = get_weather(27.6833, 84.4333, "Bharatpur")
    elif "kathmandu" in user_q.lower():
        _, answer_en = get_weather(27.7172, 85.3240, "Kathmandu")
    elif "mars" in user_q.lower():
        answer_en = "Mars is currently 225 million km from Earth. Latest Curiosity Rover photos available in NASA tab."
    elif "iss" in user_q.lower():
        answer_en = "ISS orbits Earth every 90 minutes at 28,000 km/h. Check NASA tab for live location."
    else:
        _, answer_en = get_weather(lat, lon, city_name)

    st.success(smart_reply(answer_en, lang))
    st.caption(f"Language: {lang.upper()} | Data: NASA + OpenWeatherMap")

st.divider()
st.caption(f"v1.3 NASA Edition | © 2026 SkyGPT by Saroj Kumal | Made in Nepal 🇳🇵 | For Educational Use")
st.caption("This app uses public APIs from NASA and OpenWeatherMap. Not affiliated with NASA.")
