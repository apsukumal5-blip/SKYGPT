"""
PROJECT: SkyGPT World AI v3.2 MVP STABLE
CREATOR: Saroj Kumal
MISSION: Production Launch - 50-5000 Users/Day - Zero Crashes
DEPLOY: Streamlit Cloud Compatible | Python 3.11+
STATUS: Launch Ready - June 28/29
"""
import streamlit as st
import time
import hashlib
import logging
import re
from typing import Optional, Dict, Any, List

# --- 1. LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. SAFE IMPORTS WITH FALLBACKS ---
try:
    from brain import get_ai_response_multilingual, extract_location_multilingual, detect_user_language
    from data_sources import geocode_nominatim, geocode_photon, get_weather, get_earthquakes, get_eonet_events, get_nasa_apod, get_iss_location
    from risk_engine import assess_flood_risk, assess_landslide_risk, get_earthquake_advice
    from ui import render_header, render_sidebar, render_chat_history, render_typing_indicator, render_footer
except ImportError as e:
    st.error(f"🔴 Critical Import Error: {e}")
    st.error("Missing required modules. Check deployment. App cannot start.")
    st.stop()

# --- 3. CACHED API WRAPPERS - v3.2: PREVENTS QUOTA DEATH ---
@st.cache_data(ttl=1800, show_spinner=False, max_entries=100)
def get_cached_earthquakes() -> List:
    """Cache earthquake data 30min. Prevents 1000s of API calls."""
    try:
        return get_earthquakes()
    except Exception as e:
        logger.error(f"earthquake_api_fail: {str(e)[:100]}")
        return []

@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def get_cached_eonet() -> List:
    """Cache EONET events 1hr."""
    try:
        return get_eonet_events()
    except Exception as e:
        logger.error(f"eonet_api_fail: {str(e)[:100]}")
        return []

@st.cache_data(ttl=300, show_spinner=False, max_entries=10)
def get_cached_iss() -> Dict:
    """Cache ISS location 5min."""
    try:
        return get_iss_location()
    except Exception as e:
        logger.error(f"iss_api_fail: {str(e)[:100]}")
        return {}

@st.cache_data(ttl=86400, show_spinner=False, max_entries=20)
def get_cached_apod(nasa_key: str) -> Dict:
    """Cache APOD 24hr. NASA updates once daily."""
    try:
        return get_nasa_apod(nasa_key)
    except Exception as e:
        logger.error(f"apod_api_fail: {str(e)[:100]}")
        return {}

@st.cache_data(ttl=86400, show_spinner=False, max_entries=1000)
def cached_geocode(query: str) -> List:
    """Cache geocode results 24hr. Same query = 0 API calls."""
    try:
        results = geocode_nominatim(query) or []
        if not results:
            results = geocode_photon(query) or []
        return results
    except Exception as e:
        logger.error(f"geocode_fail: {query[:30]} | {str(e)[:100]}")
        return []

@st.cache_data(ttl=600, show_spinner=False, max_entries=500)
def cached_weather(lat: float, lon: float) -> Dict:
    """Cache weather 10min per location."""
    try:
        return get_weather(lat, lon)
    except Exception as e:
        logger.error(f"weather_api_fail: {lat},{lon} | {str(e)[:100]}")
        return {}

# --- 4. STREAMLIT CONFIG ---
st.set_page_config(
    page_title="SkyGPT World AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
if NASA_KEY == "DEMO_KEY":
    st.sidebar.warning("⚠️ NASA_KEY missing. Using demo limits (30/hour).")

# --- 5. UI RENDER ---
render_header()

# --- 6. SESSION STATE - v3.2: BOUNDED + SAFE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Namaste! I am SkyGPT World AI v3.2. Ask me about any location on Earth in your language. Eg: 'एभरेस्ट बेस क्याम्पको मौसम' or 'Flood risk in Tokyo?'"
    }]
if "current_location" not in st.session_state:
    st.session_state.current_location = None
if "last_query_hash" not in st.session_state:
    st.session_state.last_query_hash = None
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

# v3.2: MEMORY LEAK FIX - Trim old messages
if len(st.session_state.messages) > 60:
    st.session_state.messages = st.session_state.messages[-40:]
    logger.info(f"Memory trimmed: {len(st.session_state.messages)} messages kept")

# --- 7. SIDEBAR - v3.2: CACHED CALLS ONLY ---
with st.sidebar:
    st.markdown("### 🛰️ Live Space Data")
    space_data = {"iss": get_cached_iss()}
    quake_data = get_cached_earthquakes()

    # v3.2: Safe render with fallback
    try:
        render_sidebar(space_data, quake_data)
    except Exception as e:
        st.error("Sidebar load error")
        logger.error(f"sidebar_fail: {str(e)[:100]}")

    st.divider()
    st.markdown("### ⚙️ Session Control")
    if st.button("🔄 Reset Location & Chat", use_container_width=True):
        st.session_state.current_location = None
        st.session_state.messages = [st.session_state.messages[0]] # Keep welcome
        st.session_state.last_query_hash = None
        st.success("Session reset!")
        time.sleep(0.5)
        st.rerun()

    st.caption(f"Messages: {len(st.session_state.messages)}/60 | Requests: {st.session_state.request_count}/100")

# --- 8. CHAT HISTORY ---
render_chat_history(st.session_state.messages)

# --- 9. CORE LOGIC: USER INPUT - v3.2: NO RERUN RACES ---
if prompt := st.chat_input("Ask Earth Anything..."):
    # v3.2: DoS PROTECTION
    if len(prompt) > 3000:
        st.warning("⚠️ Query too long. Max 3000 characters. Truncated.")
        prompt = prompt[:3000]

    # v3.2: RATE LIMITING
    st.session_state.request_count += 1
    if st.session_state.request_count > 100:
        st.error("🚫 Rate limit: 100 messages per session reached. Please refresh to continue.")
        st.stop()

    # v3.2: DEDUPLICATION - Prevent double-click API waste
    query_hash = hashlib.md5(prompt.encode()).hexdigest()
    if query_hash == st.session_state.last_query_hash:
        st.toast("Duplicate request ignored", icon="⚠️")
        st.stop()
    st.session_state.last_query_hash = query_hash

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # v3.2: SINGLE SPINNER - No manual empty/rerun races
    with st.spinner("🌍 Analyzing Earth data..."):
        try:
            # Step 1: Language + Location Detection
            lang_code = detect_user_language(prompt)
            location_query = extract_location_multilingual(prompt, lang_code)

            loc_data = None
            # v3.2: H2 FIX - str() cast prevents AttributeError
            if not location_query or str(location_query).lower() == "none":
                if st.session_state.current_location:
                    loc_data = st.session_state.current_location
                    logger.info(f"Using cached location: {loc_data['display']}")
                else:
                    response = get_ai_response_multilingual(
                        "Ask user for location politely",
                        {"error": "no_location", "lang": lang_code},
                        st.session_state.messages
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun() # Only rerun here, safe exit

            # Step 2: Multi-Geocoder Fallback - v3.2: CACHED
            if not loc_data and location_query:
                results = cached_geocode(location_query)
                if not results:
                    response = get_ai_response_multilingual(
                        f"I could not find location '{location_query}'. Ask user to specify city and country clearly.",
                        {"error": "location_not_found", "query": location_query, "lang": lang_code},
                        st.session_state.messages
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                elif len(results) > 1:
                    options = "\n".join([f"{i+1}. {r['display']}" for i, r in enumerate(results[:3])])
                    response = get_ai_response_multilingual(
                        f"Multiple locations found for '{location_query}'. Options: {options}. Ask user to choose number.",
                        {"error": "multiple_locations", "options": options, "lang": lang_code},
                        st.session_state.messages
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                else:
                    loc_data = results[0]
                    st.session_state.current_location = loc_data
                    logger.info(f"Location set: {loc_data['display']}")

            # Step 3: Gather All Intel - v3.2: ALL CACHED
            weather = cached_weather(loc_data['lat'], loc_data['lon']) if loc_data else {}
            disasters = {
                "earthquake": get_cached_earthquakes(),
                "eonet": get_cached_eonet()
            }
            space = {
                "apod": get_cached_apod(NASA_KEY),
                "iss": get_cached_iss()
            }

            # v3.2: L4 FIX - Handle None weather
            safe_weather = weather or {}
            context = {
                "location": loc_data,
                "weather": safe_weather,
                "flood_risk": assess_flood_risk(safe_weather),
                "landslide_risk": assess_landslide_risk(safe_weather, loc_data['display']) if loc_data else {},
                "disasters": disasters,
                "space": space
            }

            # Step 4: Get AI Response - v3.2: ERROR BOUNDARY
            response = get_ai_response_multilingual(prompt, context, st.session_state.messages)

            # v3.2: SECURITY - Sanitize secrets from response
            response = str(response).replace(NASA_KEY, "***") if NASA_KEY!= "DEMO_KEY" else str(response)

        except Exception as e:
            # v3.2: C4 FIX - Never show stack trace to user
            logger.error(f"app_crash: {str(e)[:300]}", exc_info=True)
            response = "Sorry, I encountered a temporary error processing your request. Please try again or rephrase your question. If this persists, our service may be experiencing high load."

    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

    # v3.2: Single rerun at end only - No races
    st.rerun()

# --- 10. FOOTER ---
render_footer()
