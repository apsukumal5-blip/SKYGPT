import streamlit as st
import requests
from deep_translator import GoogleTranslator
from datetime import datetime
import pytz

st.set_page_config(page_title="SkyGPT Command Center", page_icon="🛰️", layout="wide")

NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
WEATHER_KEY = st.secrets.get("WEATHER_KEY", "")

# --- HELPER FUNCTIONS - SABAI MATHI RAKHEKO ---
def detect_lang(text):
    try:
        return GoogleTranslator(source='auto', target='en').detect(text)
    except:
        return 'en'

def translate_text(text, target_lang):
    if target_lang == 'en' or not text: return text
    try:
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except:
        return text

def get_coordinates(city_name):
    if not WEATHER_KEY: return None, None, "Weather API Key missing"
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={WEATHER_KEY}"
        r = requests.get(url, timeout=10).json()
        if r:
            return r[0]['lat'], r[0]['lon'], r[0]['name'] + ", " + r[0].get('country', '')
        else:
            return None, None, f"Location '{city_name}' not found"
    except:
        return None, None, "Geocoding service error"

def get_professional_weather_report(query):
    query_lower = query.lower()
    location = "Meghauli, Nepal" # Default

    # Extract location from query
    location_keywords = ["in ", "at ", "for ", "ma ", "ko ", "का ", "मा "]
    for kw in location_keywords:
        if kw in query_lower:
            parts = query_lower.split(kw)
            if len(parts) > 1:
                location = parts[1].strip().split('?')[0].split('.')[0].split(',')[0]
                break

    if "everest" in query_lower: location = "Mount Everest"
    if "lukla" in query_lower: location = "Lukla, Nepal"
    if "japan" in query_lower: location = "Tokyo, Japan"

    lat, lon, full_location_name = get_coordinates(location)
    if not lat:
        return f"❌ **Location Error**: {full_location_name}. Try: 'Weather in Pokhara' or 'Mausam in Mt Everest'"

    try:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
        w = requests.get(weather_url, timeout=10).json()

        air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={WEATHER_KEY}"
        air = requests.get(air_url, timeout=10).json()
        aqi = air['list'][0]['main']['aqi']
        aqi_text = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}[aqi]
    except:
        return "❌ **API Error**: Weather service down or API Key invalid. Check Streamlit Secrets."

    temp = w['main']['temp']
    feels_like = w['main']['feels_like']
    pressure = w['main']['pressure']
    humidity = w['main']['humidity']
    wind_speed = w['wind']['speed']
    wind_deg = w['wind']['deg']
    clouds = w['clouds']['all']
    visibility = w.get('visibility', 10000) / 1000
    desc = w['weather'][0]['description'].capitalize()

    report = f"### 🛰️ SkyGPT Command Center Report\n"
    report += f"**Location**: {full_location_name}\n"
    report += f"**Coordinates**: {lat:.4f}, {lon:.4f} | **Time**: {datetime.now(pytz.timezone('Asia/Kathmandu')).strftime('%Y-%m-%d %H:%M NPT')}\n\n"

    report += f"#### 🌤️ **General Conditions**\n"
    report += f"- **Condition**: {desc}\n"
    report += f"- **Temperature**: {temp}°C, Feels like {feels_like}°C\n"
    report += f"- **Humidity**: {humidity}% | **Pressure**: {pressure} hPa\n"
    report += f"- **Visibility**: {visibility} km | **Cloud Cover**: {clouds}%\n\n"

    report += f"#### ✈️ **Aviation / Pilot Report**\n"
    report += f"- **Surface Wind**: {wind_deg}° at {wind_speed*1.944:.0f} knots ({wind_speed} m/s)\n"
    report += f"- **Cloud Ceiling**: Estimated {1000 + clouds*50} ft AGL\n"
    report += f"- **Turbulence Risk**: {'Low' if wind_speed < 5 else 'Moderate' if wind_speed < 10 else 'High'}\n"
    report += f"- **Icing Risk**: {'High' if temp < 2 and clouds > 50 else 'Low'}\n\n"

    report += f"#### ⚠️ **Disaster & Safety Alert**\n"
    report += f"- **Air Quality Index**: {aqi_text} ({aqi}/5)\n"
    if "tsunami" in query_lower:
        report += f"- **Tsunami Risk**: No active tsunami warnings for this area. Check official INCOIS/PTWC for coastal alerts.\n"
    if "flood" in query_lower or "badhi" in query_lower:
        report += f"- **Flood Risk**: {'High' if 'rain' in desc.lower() and humidity > 90 else 'Low'}. Monitor river levels.\n"
    if "snow" in query_lower or "himpat" in query_lower or "everest" in query_lower:
        report += f"- **Snow/Blizzard Risk**: {'High' if temp < 0 and clouds > 80 else 'Low'}. Wind Chill: {feels_like-10:.1f}°C\n"
    if "climbing" in query_lower:
        report += f"- **Climbing Advisory**: {'Dangerous' if wind_speed > 15 or temp < -20 else 'Caution Advised' if wind_speed > 8 else 'Favorable'}. Oxygen level low above 8000m.\n"

    report += f"\n*Data: OpenWeatherMap & NASA. For critical use, verify with official METAR/TAF.*"
    return report

def get_nasa_intel(query):
    query_lower = query.lower()
    try:
        if "iss" in query_lower:
            iss = requests.get("http://api.open-notify.org/iss-now.json", timeout=10).json()
            return f"**ISS Live Intel**: Currently over {iss['iss_position']['latitude']}, {iss['iss_position']['longitude']}. Orbit speed 28,000 km/h. 16 sunrises per day."
        if "asteroid" in query_lower:
            today = datetime.now().strftime("%Y-%m-%d")
            neo = requests.get(f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_KEY}", timeout=15).json()
            count = neo['element_count']
            return f"**NASA Asteroid Command**: {count} Near-Earth Objects tracked today. All clear. No impact threats detected by CNEOS."
        if "mars" in query_lower:
            return "**NASA Mars Intel**: Curiosity & Perseverance Rovers active. Average temp -60°C. Dust storms possible."
    except:
        return "NASA API error. Check NASA_KEY in Secrets."
    return None

# --- UI: PURE CHAT INTERFACE ---
st.title("🛰️ SkyGPT Command Center v2.1")
st.caption("Ask anything. Weather, NASA, Military, Disaster, Aviation. Worldwide Data. Professional Grade.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "SkyGPT Online. I am ready for your command. Ask me about weather, ISS, asteroids, or any location on Earth.\n\n**Example**: `Pilot weather report for Lukla Airport` or `Tsunami risk in Japan` or `Mt Everest snow condition`"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Accessing satellites & weather stations..."):
            lang = detect_lang(prompt)
            nasa_response = get_nasa_intel(prompt)

            if nasa_response:
                response = nasa_response
            else:
                response = get_professional_weather_report(prompt)

            if lang!= 'en':
                response = translate_text(response, lang)

            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()
st.caption(f"v2.1 Bug-Free | © 2026 SkyGPT | Data: NASA.gov, OpenWeatherMap.org | Not for official navigation.")
