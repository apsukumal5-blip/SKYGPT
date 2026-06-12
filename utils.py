"""
SkyGPT World AI - Data & Intelligence Engines
CREATOR: Saroj Kumal
Handles: Caching, Retries, APIs, Risk Engines
"""
import streamlit as st
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime, timezone

# --- 1. PERFORMANCE: CACHING + RETRY + TIMEOUT ---
@st.cache_data(ttl=600, show_spinner=False) # 10 min cache
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def safe_api_call(url, headers=None, timeout=10):
    """Graceful API calls with retry + timeout protection"""
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}

# --- 2. LOCATION INTELLIGENCE ---
@st.cache_data(ttl=86400) # 1 day cache for geocoding
def detect_location(text_query):
    """Detects location from user text. No Kathmandu assumption."""
    # Extract location using Gemini would be best, but using OSM for now
    url = f"https://nominatim.openstreetmap.org/search?q={text_query}&format=json&limit=1&addressdetails=1"
    data = safe_api_call(url, headers={'User-Agent': 'SkyGPT-SarojKumal'})
    if data and 'error' not in data and len(data) > 0:
        lat, lon = float(data[0]['lat']), float(data[0]['lon'])
        name = data[0].get('display_name', 'Unknown').split(',')[0]
        return {"lat": lat, "lon": lon, "name": name, "found": True}
    return {"found": False, "error": "Location not detected. Please specify city/country."}

# --- 3. WEATHER INTELLIGENCE ---
@st.cache_data(ttl=900) # 15 min cache
def get_weather_intel(lat, lon):
    """Open-Meteo: Current, Rain, Wind, Temp"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation_probability,rain&daily=precipitation_sum,windspeed_10m_max&timezone=auto"
    data = safe_api_call(url)
    if 'error' in data: return data
    current = data['current_weather']
    return {
        "temp": current['temperature'],
        "wind": current['windspeed'],
        "rain_prob": data['hourly']['precipitation_probability'][0],
        "rain_24h": data['daily']['precipitation_sum'][0],
        "wind_max": data['daily']['windspeed_10m_max'][0],
        "code": current['weathercode']
    }

# --- 4. FLOOD RISK ENGINE - IMPROVED ---
def assess_flood_risk(weather_data):
    """CORE FEATURE 5: 4-Level Risk + Intensity"""
    if 'error' in weather_data: return {"level": "Unknown", "msg": "Weather data unavailable"}
    rain = weather_data['rain_24h']
    if rain > 150: return {"level": "Extreme", "msg": "🔴 Extreme: >150mm rain. Severe flash flood expected. Evacuate low areas NOW."}
    elif rain > 100: return {"level": "High", "msg": "🟠 High: >100mm rain. Flash flood risk. Avoid rivers, move to higher ground."}
    elif rain > 50: return {"level": "Moderate", "msg": "🟡 Moderate: 50-100mm rain. Urban flooding possible. Stay alert."}
    else: return {"level": "Low", "msg": "🟢 Low: <50mm rain. No immediate flood risk."}

# --- 5. LANDSLIDE RISK ENGINE - HIMALAYAN SUPPORT ---
def assess_landslide_risk(weather_data, location_name):
    """CORE FEATURE 6: Mountain + Himalaya Detection"""
    if 'error' in weather_data: return {"level": "Unknown", "msg": "Weather data unavailable"}
    rain = weather_data['rain_24h']
    himalayan_regions = ['lukla', 'everest', 'pokhara', 'manang', 'mustang', 'annapurna', 'langtang', 'jomsom', 'himal']
    is_mountain = any(k in location_name.lower() for k in himalayan_regions)

    if is_mountain and rain > 100: return {"level": "Extreme", "msg": "🔴 Extreme: Heavy rain in Himalayan region. Landslide imminent. Avoid travel."}
    elif is_mountain and rain > 60: return {"level": "High", "msg": "🟠 High: Rain in mountain area. Landslide risk. Avoid hilly roads."}
    elif rain > 40: return {"level": "Moderate", "msg": "🟡 Moderate: Monitor slopes if continuous rain."}
    else: return {"level": "Low", "msg": "🟢 Low: No significant landslide risk."}

# --- 6. DISASTER MODULES ---
@st.cache_data(ttl=1800) # 30 min cache
def get_earthquake_intel():
    """USGS: Latest 2.5+ magnitude"""
    data = safe_api_call("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson")
    if 'error' in data: return []
    return [{"mag": q['properties']['mag'], "place": q['properties']['place'], "time": q['properties']['time']} for q in data['features'][:5]]

@st.cache_data(ttl=3600) # 1 hour cache
def get_eonet_intel():
    """NASA EONET: Wildfire, Cyclone"""
    data = safe_api_call("https://eonet.gsfc.nasa.gov/api/v3/events?limit=20&status=open")
    if 'error' in data: return {"wildfire": [], "cyclone": []}
    wildfires = [e['title'] for e in data['events'] if e['categories'][0]['id'] == 'wildfires']
    cyclones = [e['title'] for e in data['events'] if e['categories'][0]['id'] == 'severeStorms']
    return {"wildfire": wildfires[:3], "cyclone": cyclones[:3]}

# --- 7. SPACE MODULE ---
@st.cache_data(ttl=21600) # 6 hour cache
def get_space_intel(nasa_key):
    """NASA APOD + ISS"""
    intel = {}
    iss_data = safe_api_call("http://api.open-notify.org/iss-now.json", timeout=3)
    if 'error' not in iss_data: intel['iss'] = iss_data['iss_position']

    apod_data = safe_api_call(f"https://api.nasa.gov/planetary/apod?api_key={nasa_key}")
    if 'error' not in apod_data: intel['apod'] = {"title": apod_data['title'], "url": apod_data['url'], "desc": apod_data['explanation'][:200]}
    return intel
