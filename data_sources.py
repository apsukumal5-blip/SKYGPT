"""
SkyGPT World AI v3.0 - Data Sources
CREATOR: Saroj Kumal
Handles: All API calls, Geocoders, Caching, Retries
"""
import streamlit as st
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
import pytz
from datetime import datetime

@st.cache_data(ttl=600, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def safe_api_call(url, headers=None, timeout=8):
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except: return {"error": "API_FAILED"}

# --- GLOBAL LOCATION INTELLIGENCE ---
@st.cache_data(ttl=86400)
def geocode_nominatim(query):
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=5&addressdetails=1"
    data = safe_api_call(url, headers={'User-Agent': 'SkyGPT-v3-SarojKumal'})
    if 'error' in data or not data: return []
    results = []
    for item in data:
        addr = item.get('address', {})
        tz = safe_api_call(f"https://api.timezonedb.com/v2.1/get-time-zone?key=demo&format=json&by=position&lat={item['lat']}&lng={item['lon']}")
        results.append({
            "lat": float(item['lat']), "lon": float(item['lon']),
            "name": item.get('display_name', '').split(',')[0],
            "display": item.get('display_name', ''),
            "country": addr.get('country', ''),
            "state": addr.get('state', addr.get('province', addr.get('region', ''))),
            "city": addr.get('city', addr.get('town', addr.get('village', addr.get('hamlet', '')))),
            "timezone": tz.get('zoneName', 'UTC') if 'error' not in tz else 'UTC',
            "type": item.get('type', 'place')
        })
    return results

@st.cache_data(ttl=86400)
def geocode_photon(query):
    url = f"https://photon.komoot.io/api/?q={query}&limit=3"
    data = safe_api_call(url)
    if 'error' in data or not data.get('features'): return []
    results = []
    for feat in data['features']:
        props, coords = feat['properties'], feat['geometry']['coordinates']
        results.append({
            "lat": coords[1], "lon": coords[0], "name": props.get('name', 'Unknown'),
            "display": f"{props.get('name', '')}, {props.get('country', '')}",
            "country": props.get('country', ''), "state": props.get('state', ''),
            "city": props.get('city', props.get('name', '')), "timezone": 'UTC',
            "type": props.get('osm_value', 'place')
        })
    return results

# --- WEATHER + DISASTERS + SPACE ---
@st.cache_data(ttl=900)
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,visibility&hourly=precipitation_probability&daily=precipitation_sum,wind_speed_10m_max&timezone=auto"
    return safe_api_call(url)

@st.cache_data(ttl=1800)
def get_earthquakes():
    data = safe_api_call("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson")
    if 'error' in data: return []
    return [{"mag": q['properties']['mag'], "place": q['properties']['place'],
             "time": q['properties']['time'], "coords": q['geometry']['coordinates']}
            for q in data['features'][:5]]

@st.cache_data(ttl=3600)
def get_eonet_events():
    data = safe_api_call("https://eonet.gsfc.nasa.gov/api/v3/events?limit=20&status=open")
    if 'error' in data: return {"wildfire": [], "cyclone": []}
    wildfires = [e for e in data['events'] if e['categories'][0]['id'] == 'wildfires']
    cyclones = [e for e in data['events'] if e['categories'][0]['id'] == 'severeStorms']
    return {"wildfire": wildfires[:3], "cyclone": cyclones[:3]}

@st.cache_data(ttl=21600)
def get_nasa_apod(nasa_key):
    return safe_api_call(f"https://api.nasa.gov/planetary/apod?api_key={nasa_key}")

@st.cache_data(ttl=300)
def get_iss_location():
    return safe_api_call("http://api.open-notify.org/iss-now.json")
