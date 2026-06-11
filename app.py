import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="SkyGPT", page_icon="🚀", layout="wide")
st.title("🚀 SkyGPT - Live Aakash, Mausam, Bato")
st.write("From Meghauli to the World. Built by Pain, for the People.")

# 1. LIVE LOCATION - User ko thau pata laune
try:
    from streamlit_js_eval import get_geolocation
    loc = get_geolocation()
    if loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success(f"📍 Tapaiko Live Location: {lat:.2f}, {lon:.2f}")
    else:
        lat, lon = 27.5866, 84.0558 # Default: Meghauli, Chitwan
        st.info("Location milena. Default: Meghauli, Chitwan")
except:
    lat, lon = 27.5866, 84.0558
    st.info("Location milena. Default: Meghauli, Chitwan")

# 2. LIVE MAUSAM - World Wide, Real Time
def get_live_mausam(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m&timezone=auto"
    data = requests.get(url).json()['current']
    temp = data['temperature_2m']
    pani = data['precipitation']
    hawa = data['wind_speed_10m']
    return temp, pani, hawa

# 3. LIVE JAHAAJ - Mathi kun udiracha
def get_live_plane(lat, lon):
    url = f"https://opensky-network.org/api/states/all?lamin={lat-1}&lomin={lon-1}&lamax={lat+1}&lomax={lon+1}"
    try:
        res = requests.get(url, timeout=5).json()
        if res['states']:
            return len(res['states'])
        return 0
    except:
        return 0

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Live Mausam Herau", use_container_width=True):
        temp, pani, hawa = get_live_mausam(lat, lon)
        st.metric("Taapmaan", f"{temp}°C")
        st.metric("Paani", "Pariracha" if pani > 0 else "Pardaina")
        st.metric("Hawa ko Speed", f"{hawa} km/hr")
        if pani > 0:
            st.warning("Dai, chata boknus. Meghauli ko chano samjhinus.")

with col2:
    if st.button("Mathi Kun Jahaj Cha?", use_container_width=True):
        plane_count = get_live_plane(lat, lon)
        st.metric("Live Jahaj", f"{plane_count} ta")
        if plane_count > 0:
            st.info("Aakash tira hera dai. Tapai ko sapana jastai udiracha.")
        st.balloons()

with col3:
    if st.button("NASA ko Aaja ko Photo", use_container_width=True):
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        data = requests.get(url).json()
        st.image(data['url'], caption=data['title'])

# 4. LIVE BATO - Google Map
st.subheader("Yaha bata kaha janne?")
destination = st.text_input("Thau ko naam lekhus", "Denwa Backwater Escape Resort")
if st.button("Bato Dekhau"):
    st.link_button("Google Map Ma Kholnus", f"https://www.google.com/maps/dir/{lat},{lon}/{destination}")

st.write("---")
st.write("Made with Ris by Saroj Kumal 🇳🇵 | #1 Banna Janmeko App")
