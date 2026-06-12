"""
PROJECT: SkyGPT World AI v3.1 POLYGLOT MASTER
CREATOR: Saroj Kumal
MISSION: World's Most Useful Earth Intelligence AI
"""
import streamlit as st
from brain import get_ai_response_multilingual, extract_location_multilingual, detect_user_language
from data_sources import geocode_nominatim, geocode_photon, get_weather, get_earthquakes, get_eonet_events, get_nasa_apod, get_iss_location
from risk_engine import assess_flood_risk, assess_landslide_risk, get_earthquake_advice
from ui import render_header, render_sidebar, render_chat_history, render_typing_indicator, render_footer
import time

st.set_page_config(page_title="SkyGPT World AI", page_icon="🌍", layout="wide")
NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")

# --- 1. UI RENDER ---
render_header()

# --- 2. SESSION STATE + MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Namaste! I am SkyGPT World AI v3.1. Ask me about any location on Earth in your language. Eg: 'एभरेस्ट बेस क्याम्पको मौसम' or 'Flood risk in Tokyo?'"}]
if "current_location" not in st.session_state:
    st.session_state.current_location = None

# --- 3. SIDEBAR ---
space_data = {"iss": get_iss_location()}
quake_data = get_earthquakes()
render_sidebar(space_data, quake_data)

# --- 4. CHAT HISTORY ---
render_chat_history(st.session_state.messages)

# --- 5. CORE LOGIC: USER INPUT ---
if prompt := st.chat_input("Ask Earth Anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.container():
        typing_placeholder = st.empty()
        with typing_placeholder:
            render_typing_indicator()

        # Step 1: Language + Location Detection - Global Intelligence
        lang_code = detect_user_language(prompt)
        location_query = extract_location_multilingual(prompt, lang_code) or prompt

        loc_data = None
        # Use last location for follow-ups like "भोलि?" or "tomorrow?"
        if not location_query or location_query.lower() == "none":
            if st.session_state.current_location:
                loc_data = st.session_state.current_location
            else:
                response = get_ai_response_multilingual("Ask user for location", {"error": "no_location"}, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": response})
                typing_placeholder.empty()
                st.rerun()

        # Step 2: Multi-Geocoder Fallback
        if not loc_data:
            results = geocode_nominatim(location_query)
            if not results: results = geocode_photon(location_query)

            if not results:
                response = f"📍 Could not find '{location_query}'. Try: 'City, Country' format."
                st.session_state.messages.append({"role": "assistant", "content": response})
                typing_placeholder.empty()
                st.rerun()
            elif len(results) > 1:
                options = "\n".join([f"{i+1}. {r['display']}" for i, r in enumerate(results[:3])])
                response = f"📍 Multiple locations found for '{location_query}'. Which one?\n{options}"
                st.session_state.messages.append({"role": "assistant", "content": response})
                typing_placeholder.empty()
                st.rerun()
            else:
                loc_data = results[0]
                st.session_state.current_location = loc_data # Save for memory

        # Step 3: Gather All Intel
        weather = get_weather(loc_data['lat'], loc_data['lon'])
        disasters = {"earthquake": get_earthquakes(), "eonet": get_eonet_events()}
        space = {"apod": get_nasa_apod(NASA_KEY), "iss": get_iss_location()}

        context = {
            "location": loc_data,
            "weather": weather,
            "flood_risk": assess_flood_risk(weather),
            "landslide_risk": assess_landslide_risk(weather, loc_data['display']),
            "disasters": disasters,
            "space": space
        }

        # Step 4: Get AI Response
        response = get_ai_response_multilingual(
    f"I could not find location '{location_query}'. Ask user to specify city and country clearly.", 
    {"error": "location_not_found", "query": location_query}, 
    st.session_state.messages
        )

        typing_placeholder.empty()
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# --- 6. FOOTER ---
render_footer()
