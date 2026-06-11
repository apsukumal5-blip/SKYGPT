import streamlit as st
import requests
from datetime import datetime
from deep_translator import GoogleTranslator

st.set_page_config(page_title="SkyGPT", page_icon="🚀", layout="wide")

# --- SMART LANGUAGE DETECTION ---
def detect_lang(text):
    try:
        return GoogleTranslator(source='auto', target='en').detect(text)
    except:
        return 'en'

def smart_reply(text_en, user_lang='en'):
    if user_lang == 'en': return text_en
    try:
        return GoogleTranslator(source='en', target=user_lang).translate(text_en)
    except:
        return text_en

# --- UI: 100% ENGLISH PROFESSIONAL ---
st.title("🚀 SkyGPT v1.0 - Global Sky Intelligence")
st.caption("From Meghauli, Nepal to the World. Powered by NASA, Built with Resilience.")

# 1. LOCATION
try:
    from streamlit_js_eval import get_geolocation
    loc = get_geolocation()
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    st.success(f"📍 Live Location Detected: {lat:.2f}, {lon:.2f}")
except:
    lat, lon = 27.5866, 84.0558 # Meghauli, Chitwan
    st.info("Default Location: Meghauli, Chitwan, Nepal 🇳🇵")

# 2. LIVE WEATHER - ENGLISH UI
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⚡ Live Weather & Wind", use_container_width=True):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m&timezone=auto"
        w = requests.get(url).json()['current']
        st.metric("Temperature", f"{w['temperature_2m']}°C")
        st.metric("Precipitation", f"{w['precipitation']} mm")
        st.metric("Wind Speed", f"{w['wind_speed_10m']} km/h")

with col2:
    if st.button("🛰️ Track ISS Live", use_container_width=True):
        iss = requests.get("http://api.open-notify.org/iss-now.json").json()
        iss_lat = float(iss['iss_position']['latitude'])
        iss_lon = float(iss['iss_position']['longitude'])
        st.map(data=[{"lat": iss_lat, "lon": iss_lon}])
        st.info(f"ISS Current Position: {iss_lat:.2f}, {iss_lon:.2f}")

with col3:
    if st.button("✈️ Live Aircraft Overhead", use_container_width=True):
        url = f"https://opensky-network.org/api/states/all?lamin={lat-1}&lomin={lon-1}&lamax={lat+1}&lomax={lon+1}"
        res = requests.get(url, timeout=5).json()
        count = len(res['states']) if res['states'] else 0
        st.metric("Aircraft Overhead", f"{count}")

# 3. SMART CHAT - AUTO NEPALI/FRENCH/ENGLISH REPLY
st.divider()
st.subheader("Ask SkyGPT Anything")
user_q = st.text_input("Type your question in any language", "Bharatpur ma paani parcha?")

if st.button("Get Answer"):
    lang = detect_lang(user_q)
    # Sample Logic: Yaha real AI jodne
    if "paani" in user_q or "rain" in user_q.lower():
        answer_en = "Yes, there is a 60% chance of rain in Bharatpur today after 3 PM. Carry an umbrella."
    else:
        answer_en = "I am SkyGPT. I can check weather, ISS, flights. Your location is set to Chitwan, Nepal."
    
    final_answer = smart_reply(answer_en, lang)
    st.success(final_answer)
    st.caption(f"Detected Language: {lang.upper()} | Replied in same language")

# 4. DIRECTIONS
st.divider()
dest = st.text_input("Enter Destination for Directions", "Bharatpur Airport")
if st.button("🗺️ Get Directions"):
    st.link_button("Open in Google Maps", f"https://www.google.com/maps/dir/{lat},{lon}/{dest}")

st.divider()
st.caption("Made with Grit by Saroj Kumal | Denwa Backwater Escape | Version 1.0")
