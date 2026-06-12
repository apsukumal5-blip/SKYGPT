"""
PROJECT: SkyGPT World AI v3.0 MASTER
CREATOR: Saroj Kumal
MISSION: World's Most Useful Earth Intelligence AI
"""
import streamlit as st
from brain import get_ai_response, extract_location_with_gemini
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
    st.session_state.messages = [{"role": "assistant", "content": "Namaste! I am SkyGPT World AI v3.0. Ask me about any location on Earth. Eg: 'Everest Base Camp weather' or 'Flood risk in Tokyo?'"}]
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

        # Step 1: Location Detection - Global Intelligence
        location_query = extract_location_with_gemini(prompt) or prompt

        # Use last location for follow-ups like "what about tomorrow"
        if not location_query or location_query.lower() == "none":
            if st.session_state.current_location:
                loc_data = st.session_state.current_location
            else:
                response = "📍 Which location? Please specify city and country. Eg: 'Kathmandu, Nepal'"
                st.session_state.messages.append({"role": "assistant", "content": response})
                typing_placeholder.empty()
                st.rerun()
        else:
            # Multi-Geocoder Fallback
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

        # Step 2: Gather All Intel
        weather = get_weather(loc_data['lat'], loc_data['lon'])
        disasters = {"earthquake": get_earthquakes(), "eonet": get_eonet_events()}
        space = {"apod": get_nasa_apod(NASA_KEY), "iss": get_iss_location()}

        context = {
            "location": loc_data, "weather": weather,
            "flood_risk": assess_flood_risk(weather),
            "landslide_risk": assess_landslide_risk(weather, loc_data['display']),
            "disasters": disasters, "space": space
        }

        # Step 3: Get AI Response
        response = get_ai_response(prompt, context, st.session_state.messages)

        typing_placeholder.empty()
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# --- 6. FOOTER ---
render_footer()
