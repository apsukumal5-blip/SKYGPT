import streamlit as st
import requests
from deep_translator import GoogleTranslator
import streamlit.components.v1 as components
from datetime import datetime
import pytz
import re

st.set_page_config(page_title="SkyGPT", page_icon="🚀", layout="wide")

NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
WEATHER_KEY = st.secrets.get("WEATHER_KEY", "")

# --- CITY DATABASE FOR NEPAL ---
CITY_COORDS = {
    "denwa": [27.5866, 84.0558, "Denwa Backwater Escape Resort, Meghauli"],
    "meghauli": [27.5866, 84.0558, "Meghauli, Chitwan"],
    "bharatpur": [27.6833, 84.4333, "Bharatpur, Chitwan"],
    "kathmandu": [27.7172, 85.3240, "Kathmandu"],
    "pokhara": [28.2096, 83.9856, "Pokhara"],
    "sauraha": [27.5788, 84.4930, "Sauraha, Chitwan"]
}

def detect_lang(text):
    try: return GoogleTranslator(source='auto', target='en').detect(text)
    except: return 'en'

def translate_text(text, target_lang):
    if target_lang == 'en' or not text: return text
    try: return GoogleTranslator(source='en', target=target_lang).translate(text)
    except: return text

def get_city_from_query(query):
    query_lower = query.lower()
    for city in CITY_COORDS:
        if city in query_lower:
            return CITY_COORDS[city]
    return [27.5866, 84.0558, "Meghauli, Chitwan"] # Default

def get_live_weather(lat, lon, city_name):
    if not WEATHER_KEY:
        return "❌ Weather API Key not found. Please add WEATHER_KEY in Streamlit Secrets."
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        if r.status_code == 401:
            return "❌ Invalid Weather API Key. Check Streamlit Secrets."
        w = r.json()
        temp = w['main']['temp']
        desc = w['weather'][0]['description'].capitalize()
        feels = w['main']['feels_like']
        hum = w['main']['humidity']
        wind = w['wind']['speed']
        return f"**{city_name}**: {temp}°C, {desc}. Feels like {feels}°C. Humidity {hum}%, Wind {wind} m/s."
    except Exception as e:
        return f"Weather service error. API key may be activating. Try after 10 mins."

def get_nasa_apod():
    try:
        apod = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={NASA_KEY}", timeout=10).json()
        if 'error' in apod: return None, "NASA API Key invalid or DEMO_KEY limit reached."
        return apod, None
    except:
        return None, "NASA APOD service unavailable."

# --- UI ---
st.title("🚀 SkyGPT v1.4 Professional")
st.caption("Accurate Weather + NASA Live Data | Made in Nepal 🇳🇵")

tab1, tab2, tab3 = st.tabs(["🌤️ Live Weather", "🛰️ NASA Space", "🗺️ Live Map"])

with tab1:
    st.subheader("Select Location for Instant Weather")
    col1, col2, col3 = st.columns(3)

    if col1.button("📍 Denwa Resort", use_container_width=True):
        result = get_live_weather(27.5866, 84.0558, "Denwa Resort, Meghauli")
        st.success(result)

    if col2.button("🏙️ Bharatpur City", use_container_width=True):
        result = get_live_weather(27.6833, 84.4333, "Bharatpur")
        st.success(result)

    if col3.button("🏔️ Kathmandu", use_container_width=True):
        result = get_live_weather(27.7172, 85.3240, "Kathmandu")
        st.success(result)

with tab2:
    st.subheader("NASA Live Data")
    nasa_col1, nasa_col2 = st.columns(2)

    with nasa_col1:
        if st.button("🌌 Astronomy Photo of Day", use_container_width=True):
            apod, error = get_nasa_apod()
            if error: st.error(error)
            elif apod:
                st.image(apod['url'], caption=f"NASA: {apod['title']}")
                with st.expander("Explanation"):
                    st.write(apod['explanation'])

        if st.button("🔴 Mars Rover Photo", use_container_width=True):
            try:
                mars = requests.get(f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/latest_photos?api_key={NASA_KEY}", timeout=15).json()
                if 'latest_photos' in mars and mars['latest_photos']:
                    photo = mars['latest_photos'][0]
                    st.image(photo['img_src'], caption=f"Curiosity Rover: {photo['camera']['full_name']}")
                    st.caption(f"Earth Date: {photo['earth_date']}")
                else: st.info("No new Mars photos in last 24hrs.")
            except: st.error("Mars API error. Check NASA_KEY.")

    with nasa_col2:
        if st.button("🛰️ ISS Live Tracker", use_container_width=True):
            try:
                iss = requests.get("http://api.open-notify.org/iss-now.json", timeout=10).json()
                iss_lat = float(iss['iss_position']['latitude'])
                iss_lon = float(iss['iss_position']['longitude'])
                st.metric("ISS Latitude", f"{iss_lat:.2f}°")
                st.metric("ISS Longitude", f"{iss_lon:.2f}°")
                st.caption("ISS orbits Earth every 90 minutes at 28,000 km/h")
            except: st.error("ISS API down.")

        if st.button("☄️ Asteroid Alert", use_container_width=True):
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                neo = requests.get(f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_KEY}", timeout=15).json()
                count = neo['element_count']
                st.metric("Asteroids Near Earth Today", count)
                if count > 0:
                    hazardous = sum(1 for n in neo['near_earth_objects'][today] if n['is_potentially_hazardous_asteroid'])
                    st.warning(f"Total: {count} | Potentially Hazardous: {hazardous}")
                else:
                    st.success("Sky is clear. No asteroids today.")
            except: st.error("Asteroid API error. Check NASA_KEY.")

with tab3:
    st.subheader("Live Interactive Map")
    map_code = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="map" style="height: 500px; border-radius: 10px;"></div>
    <script>
      var map = L.map('map').setView([27.5866, 84.0558], 13);
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
      L.marker([27.5866, 84.0558]).addTo(map).bindPopup('<b>Denwa Backwater Escape Resort</b><br>SkyGPT HQ, Meghauli').openPopup();
      L.marker([27.6833, 84.4333]).addTo(map).bindPopup('<b>Bharatpur City</b>');
    </script>
    """
    components.html(map_code, height=520)

# --- SMART CHAT - ABA REAL DATA DINCHA ---
st.divider()
st.subheader("💬 Ask SkyGPT Anything")
user_q = st.text_input("Ask in Nepali/Hindi/English", "Denwa resort ma aaja mausam k cha?")

if st.button("Get Answer", use_container_width=True):
    lang = detect_lang(user_q)
    lat, lon, city_name = get_city_from_query(user_q)

    # Weather Query
    if any(word in user_q.lower() for word in ["mausam", "weather", "garmi", "temp", "paani", "rain"]):
        answer_en = get_live_weather(lat, lon, city_name)
    # NASA Query
    elif "mars" in user_q.lower():
        answer_en = "Mars is the 4th planet from Sun. Use 'Mars Rover Photo' button for latest Curiosity images."
    elif "iss" in user_q.lower() or "space station" in user_q.lower():
        answer_en = "ISS is in Low Earth Orbit. Use 'ISS Live Tracker' for real-time position."
    elif "asteroid" in user_q.lower():
        answer_en = "Check 'Asteroid Alert' button for today's near-earth objects from NASA."
    else:
        answer_en = get_live_weather(lat, lon, city_name)

    st.success(translate_text(answer_en, lang))
    st.caption(f"Source: OpenWeatherMap + NASA APIs | Detected: {lang.upper()}")

st.divider()
st.caption(f"v1.4 Professional | © 2026 SkyGPT by Saroj Kumal | For Educational Use Only")
st.caption("Data: NASA.gov, OpenWeatherMap.org. Not affiliated with NASA.")
