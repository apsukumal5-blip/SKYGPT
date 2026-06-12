"""
SkyGPT World AI - Data & Intelligence Engines
CREATOR: Saroj Kumal
STATUS: Production Stable v3.2.4 - June 28/29 Launch
FIXES: Thread-safe rate limiting, strict timeouts, response validation, module isolation, safe fallbacks
"""
import streamlit as st
import requests
import time
import textwrap
import threading
from typing import Dict, Any, List, Optional, Union

# --- 0. PRODUCTION RESILIENCE LAYER ---
# Global thread-safe rate limiter for Nominatim
_nominatim_lock = threading.Lock()
_last_nominatim_call = 0

# Global safe defaults for total API failure
SAFE_DEFAULTS = {
    "location": {"found": False, "error": "Service temporarily unavailable"},
    "weather": {"error": "unavailable", "temp": None, "wind": None, "rain_prob": None, "rain_24h": None},
    "earthquake": [],
    "eonet": {"wildfire": [], "cyclone": []},
    "space": {"iss": {"error": "unavailable"}, "apod": None}
}

def validate_api_response(data: Any, required_keys: Optional[List[str]] = None) -> bool:
    """Centralized response validation. Prevents repeated error checks everywhere."""
    if not isinstance(data, dict):
        return False
    if 'error' in data:
        return False
    if required_keys:
        return all(k in data for k in required_keys)
    return True

# --- 1. PERFORMANCE: CACHING + TIMEOUT - NO RETRY ON GEOCODING ---
# Hardened timeout: 3s max for all APIs to prevent Streamlit worker blocking
def safe_api_call(url: str, headers: Optional = None, timeout: int = 3, params: Optional = None) -> Dict[str, Any]:
    """Graceful API calls with strict timeout. Never retries. Returns validated dict."""
    try:
        res = requests.get(url, headers=headers, timeout=timeout, params=params)
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, (dict, list)) else {"error": "invalid_response_type"}
    except requests.exceptions.Timeout:
        return {"error": "timeout"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"http_{e.response.status_code}"}
    except requests.exceptions.RequestException:
        return {"error": "request_failed"}
    except ValueError:
        return {"error": "invalid_json"}

# --- 2. LOCATION INTELLIGENCE - THREAD-SAFE RATE LIMIT ---
@st.cache_data(ttl=86400, max_entries=5000) # 1 day cache, bounded for 10k users
def detect_location(text_query: str) -> Dict[str, Any]:
    """Detects location from user text. Thread-safe 1 req/sec. Uses params."""
    global _last_nominatim_call

    # Thread-safe rate limit - no cross-user interference
    with _nominatim_lock:
        elapsed = time.time() - _last_nominatim_call
        if elapsed < 1.1:
            time.sleep(1.1 - elapsed)
        _last_nominatim_call = time.time()

    # Use params dict instead of f-string to prevent injection
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': text_query.strip()[:200], # Limit query length
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    headers = {'User-Agent': 'SkyGPT-SarojKumal/3.2.4 (+contact@skygpt.ai)'}

    data = safe_api_call(url, headers=headers, params=params, timeout=3)

    # Centralized validation + safe fallback
    if not validate_api_response(data):
        return SAFE_DEFAULTS["location"]

    if isinstance(data, list) and len(data) > 0:
        item = data[0]
        if not isinstance(item, dict):
            return SAFE_DEFAULTS["location"]

        try:
            lat, lon = float(item['lat']), float(item['lon'])
            name = item.get('display_name', 'Unknown').split(',')[0]
            return {"lat": lat, "lon": lon, "name": name, "found": True}
        except (KeyError, TypeError, ValueError):
            return {"found": False, "error": "Invalid coordinates received"}

    return {"found": False, "error": "Location not detected. Please specify city/country."}

# --- 3. WEATHER INTELLIGENCE - HARDENED ---
@st.cache_data(ttl=900, max_entries=2000) # 15 min cache, bounded
def get_weather_intel(lat: float, lon: float) -> Dict[str, Any]:
    """Open-Meteo: Current + Daily. Uses current block. Strict timeout."""
    # Validate coordinates before API call
    try:
        lat_f, lon_f = float(lat), float(lon)
        if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
            return SAFE_DEFAULTS["weather"]
    except (TypeError, ValueError):
        return SAFE_DEFAULTS["weather"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat_f,
        'longitude': lon_f,
        'current': 'temperature_2m,precipitation_probability,wind_speed_10m,weathercode',
        'daily': 'precipitation_sum,wind_speed_10m_max',
        'timezone': 'auto',
        'wind_speed_unit': 'kmh'
    }

    data = safe_api_call(url, params=params, timeout=3)

    # Centralized validation
    if not validate_api_response(data, ['current', 'daily']):
        return SAFE_DEFAULTS["weather"]

    try:
        current = data['current']
        daily = data['daily']

        return {
            "temp": current.get('temperature_2m'),
            "wind": current.get('wind_speed_10m'),
            "rain_prob": current.get('precipitation_probability'),
            "rain_24h": daily.get('precipitation_sum', [None])[0],
            "wind_max": daily.get('wind_speed_10m_max', [None])[0],
            "code": current.get('weathercode')
        }
    except (KeyError, IndexError, TypeError):
        return SAFE_DEFAULTS["weather"]

# --- 4. FLOOD RISK ENGINE - ISOLATED ---
def assess_flood_risk(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """CORE FEATURE 5: 4-Level Risk + Intensity. Isolated from API failures."""
    # Module isolation: Never crash if weather_data is bad
    if not validate_api_response(weather_data):
        return {"level": "Unknown", "msg": "Weather data unavailable. Check official forecasts."}

    rain = weather_data.get('rain_24h')

    if rain is None:
        return {"level": "Unknown", "msg": "Rainfall data missing"}

    try:
        rain_f = float(rain)
    except (TypeError, ValueError):
        return {"level": "Unknown", "msg": "Invalid rainfall data"}

    if rain_f > 150:
        return {"level": "Extreme", "msg": "🔴 Extreme: >150mm rain. Severe flash flood expected. Evacuate low areas NOW."}
    elif rain_f > 100:
        return {"level": "High", "msg": "🟠 High: >100mm rain. Flash flood risk. Avoid rivers, move to higher ground."}
    elif rain_f > 50:
        return {"level": "Moderate", "msg": "🟡 Moderate: 50-100mm rain. Urban flooding possible. Stay alert."}
    else:
        return {"level": "Low", "msg": "🟢 Low: <50mm rain. No immediate flood risk."}

# --- 5. LANDSLIDE RISK ENGINE - ISOLATED ---
def assess_landslide_risk(weather_data: Dict[str, Any], location_name: Optional[str]) -> Dict[str, Any]:
    """CORE FEATURE 6: Mountain + Himalaya Detection. Isolated from API failures."""
    if not validate_api_response(weather_data):
        return {"level": "Unknown", "msg": "Weather data unavailable"}

    rain = weather_data.get('rain_24h')

    if rain is None:
        return {"level": "Unknown", "msg": "Rainfall data missing"}

    try:
        rain_f = float(rain)
    except (TypeError, ValueError):
        return {"level": "Unknown", "msg": "Invalid rainfall data"}

    himalayan_regions = ['lukla', 'everest', 'pokhara', 'manang', 'mustang', 'annapurna', 'langtang', 'jomsom', 'himal']
    is_mountain = False
    if isinstance(location_name, str) and location_name:
        is_mountain = any(k in location_name.lower() for k in himalayan_regions)

    if is_mountain and rain_f > 100:
        return {"level": "Extreme", "msg": "🔴 Extreme: Heavy rain in Himalayan region. Landslide imminent. Avoid travel."}
    elif is_mountain and rain_f > 60:
        return {"level": "High", "msg": "🟠 High: Rain in mountain area. Landslide risk. Avoid hilly roads."}
    elif rain_f > 40:
        return {"level": "Moderate", "msg": "🟡 Moderate: Monitor slopes if continuous rain."}
    else:
        return {"level": "Low", "msg": "🟢 Low: No significant landslide risk."}

# --- 6. DISASTER MODULES - ISOLATED ---
@st.cache_data(ttl=1800, max_entries=100) # 30 min cache, bounded
def get_earthquake_intel() -> List[Dict[str, Any]]:
    """USGS: Latest 2.5+ magnitude. Isolated - never affects other modules."""
    data = safe_api_call("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson", timeout=3)

    if not validate_api_response(data, ['features']):
        return SAFE_DEFAULTS["earthquake"]

    features = data.get('features', [])
    if not isinstance(features, list):
        return SAFE_DEFAULTS["earthquake"]

    results = []
    for q in features[:5]:
        if not isinstance(q, dict):
            continue
        props = q.get('properties', {})
        if not isinstance(props, dict):
            continue
        results.append({
            "magnitude": props.get('mag'),
            "place": props.get('place', 'Unknown'),
            "time": props.get('time')
        })

    return results

@st.cache_data(ttl=3600, max_entries=50) # 1 hour cache, bounded
def get_eonet_intel() -> Dict[str, List[str]]:
    """NASA EONET: Wildfire, Cyclone. Isolated - never affects other modules."""
    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    params = {'limit': 20, 'status': 'open'}
    data = safe_api_call(url, params=params, timeout=3)

    if not validate_api_response(data, ['events']):
        return SAFE_DEFAULTS["eonet"]

    events = data.get('events', [])
    if not isinstance(events, list):
        return SAFE_DEFAULTS["eonet"]

    wildfires = []
    cyclones = []

    for e in events:
        if not isinstance(e, dict):
            continue

        # Safe categories access - prevents IndexError
        cats = e.get('categories', [])
        if not cats or not isinstance(cats, list):
            continue

        cat = cats[0]
        if not isinstance(cat, dict):
            continue

        cat_id = cat.get('id')
        title = e.get('title', 'Unknown')

        if cat_id == 'wildfires':
            wildfires.append(title)
        elif cat_id == 'severeStorms':
            cyclones.append(title)

    return {"wildfire": wildfires[:3], "cyclone": cyclones[:3]}

# --- 7. SPACE MODULE - ISOLATED ---
@st.cache_data(ttl=21600, max_entries=20) # 6 hour cache, bounded
def get_space_intel(nasa_key: str) -> Dict[str, Any]:
    """NASA APOD + ISS. Isolated - never affects other modules."""
    intel = {}

    # ISS HTTP may fail - graceful handling, isolated
    iss_data = safe_api_call("http://api.open-notify.org/iss-now.json", timeout=3)
    if validate_api_response(iss_data, ['iss_position']) and isinstance(iss_data.get('iss_position'), dict):
        intel['iss'] = iss_data['iss_position']
    else:
        intel['iss'] = {"error": "unavailable"}

    # Use params instead of URL string to protect API key
    apod_url = "https://api.nasa.gov/planetary/apod"
    apod_params = {'api_key': nasa_key}
    apod_data = safe_api_call(apod_url, params=apod_params, timeout=3)

    if validate_api_response(apod_data):
        desc = apod_data.get('explanation', '')
        desc_safe = textwrap.shorten(desc, width=200, placeholder='...') if desc else ''
        intel['apod'] = {
            "title": apod_data.get('title', 'Unknown'),
            "url": apod_data.get('url', ''),
            "desc": desc_safe
        }
    else:
        intel['apod'] = None

    return intel
