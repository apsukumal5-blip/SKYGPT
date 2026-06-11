import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="SkyGPT", page_icon="🚀", layout="wide")
st.title("🚀 SkyGPT v0.2 - Live + Fast + World Wide")
st.write("From Meghauli to the World. Abhaw le Aajeya Banayo.")

# 1. LOCATION - Denwa dekhi Duniya samma
try:
    from streamlit_js_eval import get_geolocation
    loc = get_geolocation()
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    st.success(f"📍 Live Location: {lat:.2f}, {lon:.2f}")
except:
    lat, lon = 27.5866, 84.0558 # Meghauli
    st.info("Default: Meghauli, Chitwan 🇳🇵")

# 2. LIVE MAUSAM + HAWAA + PAANI
if st.button("⚡ Live Mausam + Hawa", use_container_width=True):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m,wind_direction_10m&timezone=auto"
    w = requests.get(url).json()['current']
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Taapmaan", f"{w['temperature_2m']}°C")
    c2.metric("Paani", "Parcha" if w['precipitation'] > 0 else "Pardaina")
    c3.metric("Hawa Speed", f"{w['wind_speed_10m']} km/h")
    c4.metric("Hawa Disha", f"{w['wind_direction_10m']}°")
    if w['precipitation'] > 0: st.warning("Dai chata boknus. Chuhine chano samjhinus.")

# 3. LIVE ISS - Mathi International Space Station Kaha Cha
if st.button("🛰️ ISS Kaha Cha Aile?", use_container_width=True):
    iss = requests.get("http://api.open-notify.org/iss-now.json").json()
    iss_lat = float(iss['iss_position']['latitude'])
    iss_lon = float(iss['iss_position']['longitude'])
    st.map(data=[{"lat": iss_lat, "lon": iss_lon}, {"lat": lat, "lon": lon}])
    st.info(f"ISS Aile {iss_lat:.2f}, {iss_lon:.2f} ma cha. Tapaiko mathi bata jaala 90 min ma.")
    st.balloons()

# 4. LIVE JAHAAJ + BATO
col1, col2 = st.columns(2)
with col1:
    if st.button("✈️ Mathi Kun Jahaj Cha?", use_container_width=True):
        url = f"https://opensky-network.org/api/states/all?lamin={lat-1}&lomin={lon-1}&lamax={lat+1}&lomax={lon+1}"
        res = requests.get(url, timeout=5).json()
        count = len(res['states']) if res['states'] else 0
        st.metric("Aakash ma Jahaj", f"{count} ta")
        
with col2:
    dest = st.text_input("Kaha Janne Ho?", "Bharatpur Airport")
    if st.button("🗺️ Bato Dekhau"):
        st.link_button("Google Map Kholnus", f"https://www.google.com/maps/dir/{lat},{lon}/{dest}")

st.write("---")
st.write("Made with Ris by Saroj Kumal | Denwa Backwater Escape | #1 Banna Janmeko App")
