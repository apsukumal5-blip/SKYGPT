"""
PROJECT: SkyGPT World AI - UI Components v3.2
CREATOR: Saroj Kumal
STATUS: Production Stable - June 28/29 Launch
PYTHON: 3.11+ Compatible | Streamlit Cloud Compatible
FIXES: Native chat, data schema alignment, CSS stability, mobile, fallbacks, a11y
"""
import streamlit as st
from typing import List, Dict, Any, Optional

# v3.2: Remove streamlit_chat dependency - native components only

def render_header() -> None:
    """Render main header with stable CSS only. Mobile responsive."""
    st.markdown("""
    <style>
    /* v3.2 FIX: Removed.st-emotion-cache-16txtl3 unstable selector */
   .main-header {
        text-align: center;
        background: radial-gradient(circle at top, #1E3A8A, #030712);
        padding: clamp(1rem, 4vw, 2rem);
        border-radius: 20px;
        margin-bottom: 1rem;
        border: 1px solid #4A90E2;
    }
   .main-header h1 {
        margin: 0;
        font-size: clamp(1.8rem, 5vw, 2.5rem);
        color: #F9FAFB;
        line-height: 1.2;
    }
   .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: clamp(0.9rem, 2.5vw, 1.1rem);
        color: #E5E7EB;
    }
    /* v3.2 FIX: Use stable stChatMessage class, add contrast */
    [data-testid="stChatMessage"] {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 1rem;
    }
    /* v3.2 FIX: Typing indicator with safe spacing */
   .typing-indicator {
        display: flex;
        align-items: center;
        color: #60A5FA;
        font-style: italic;
        padding: 0.5rem 1rem;
        gap: 0.5rem;
    }
   .typing-dot {
        width: 8px;
        height: 8px;
        background: #60A5FA;
        border-radius: 50%;
        animation: bounce 1.4s infinite;
    }
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
        40% { transform: scale(1); opacity: 1; }
    }
    /* v3.2 FIX: Mobile padding safety - no unstable selectors */
    @media (max-width: 768px) {
       .block-container {
            padding: 1rem 0.5rem 5rem 0.5rem;
        }
    }
    /* v3.2 FIX: Accessibility - high contrast, readable sizes */
   .stMetric {
        background-color: #1F2937;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #374151;
    }
   .stMetric label {
        color: #D1D5DB!important;
        font-size: 0.875rem!important;
    }
   .stMetric [data-testid="stMetricValue"] {
        color: #F9FAFB!important;
    }
    </style>
    <div class="main-header">
        <h1>🌍 SkyGPT World AI</h1>
        <p>Ask Earth Anything | Created by Saroj Kumal</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(space_data: Dict[str, Any], quake_data: List[Dict[str, Any]]) -> None:
    """
    Render sidebar with graceful fallbacks.
    v3.2 FIX: ISS data schema, earthquake field, null safety
    """
    with st.sidebar:
        st.header("🚀 Live Space Data")

        # v3.2 FIX: ISS schema - data_sources v3.2 returns {"lat": float, "lon": float}
        iss = space_data.get('iss', {})
        if isinstance(iss, dict) and 'lat' in iss and 'lon' in iss and not iss.get('error'):
            try:
                lat_str = f"{float(iss['lat']):.4f}"
                lon_str = f"{float(iss['lon']):.4f}"
                st.metric("ISS Location", f"{lat_str}, {lon_str}")
            except (TypeError, ValueError):
                st.info("ISS location unavailable")
        elif iss.get('error'):
            st.caption(f"ISS data: {iss['error']}")
        else:
            st.info("ISS location loading...")

        st.divider()

        # v3.2 FIX: Earthquake schema - data_sources v3.2 uses 'magnitude' not 'mag'
        st.header("🌋 Global Alerts")
        if isinstance(quake_data, list) and len(quake_data) > 0:
            quake = quake_data[0]
            if isinstance(quake, dict):
                mag = quake.get('magnitude') or quake.get('mag') # Fallback for safety
                place = quake.get('place', 'Unknown location')
                if mag is not None:
                    try:
                        mag_f = float(mag)
                        if mag_f >= 5.0:
                            st.error(f"M{mag_f:.1f} Earthquake: {place}")
                        elif mag_f >= 4.0:
                            st.warning(f"M{mag_f:.1f} Earthquake: {place}")
                        else:
                            st.info(f"M{mag_f:.1f} Earthquake: {place}")
                    except (TypeError, ValueError):
                        st.caption("Earthquake data format error")
                else:
                    st.caption("No magnitude data")
            else:
                st.caption("Earthquake data unavailable")
        else:
            st.success("No major earthquakes reported today")

        st.divider()
        # v3.2 FIX: Version updated to v3.2
        st.caption("v3.2 | Saroj Kumal | Gemini + NASA + USGS")

def render_chat_history(messages: List[Dict[str, str]]) -> None:
    """
    Render chat using native st.chat_message.
    v3.2 FIX: Replaced streamlit_chat.message with native component
    """
    if not messages:
        st.info("Start a conversation by asking about any location!")
        return

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "assistant")
        content = msg.get("content", "")

        # v3.2 FIX: Empty content fallback
        if not content:
            content = "_No content_"

        # v3.2 FIX: Native chat_message with proper avatar
        with st.chat_message(name=role, avatar="👤" if role == "user" else "🤖"):
            st.markdown(content)

def render_typing_indicator() -> None:
    """Render typing indicator. v3.2: Safe HTML only."""
    st.markdown("""
    <div class="typing-indicator">
        <span>SkyGPT Analyzing</span>
        <div class="typing-dot"></div>
        <div class="typing-dot" style="animation-delay:0.2s"></div>
        <div class="typing-dot" style="animation-delay:0.4s"></div>
    </div>
    """, unsafe_allow_html=True)

def render_footer() -> None:
    """Render footer. v3.2: Version updated to v3.2"""
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #9CA3AF; font-size: 12px; line-height: 1.6; padding: 1rem 0;'>
        <b style='color: #E5E7EB;'>SkyGPT World AI v3.2</b> | Created by Saroj Kumal | Powered by Google Gemini<br>
        Data Sources: NASA, Open-Meteo, OpenStreetMap, USGS<br>
        <i>Ask Earth Anything</i>
    </div>
    """, unsafe_allow_html=True)
def render_footer():
    st.markdown("---")
    st.error("⚠️ **Disclaimer**: SkyGPT AI estimates only. NOT official warning. For emergencies, call 1149 Nepal / follow local govt. We are NOT liable for decisions based on this app.")
    col1, col2 = st.columns(2)
    with col1: st.markdown("[Privacy Policy](https://github.com/...)") 
    with col2: st.markdown("[Terms: Data deleted in 30 days](https://github.com/...)")
