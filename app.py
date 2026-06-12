import streamlit as st
import streamlit.components.v1 as components
import requests
import google.generativeai as genai

# १. Page Config
st.set_page_config(page_title="SkyGPT World AI", page_icon="🌍", layout="wide")

# CSS - Professional Space Branding
st.markdown("""
    <style>
    .stApp { background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url('https://images.unsplash.com/photo-1451187580459-43490279c0fa'); 
             background-size: cover; color: #ffffff; }
    h1 { color: #ffffff; text-shadow: 2px 2px 4px #000000; }
    .stInfo { background-color: rgba(255, 255, 255, 0.1); color: #ffffff; border: 1px solid #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# २. Setup (Gemini API)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

@st.cache_data(ttl=600)
def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    response = requests.get(url, timeout=5)
    return response.json() if response.status_code == 200 else None

def get_ai_brain_answer(question, data):
    model = genai.GenerativeModel('gemini-1.5-flash')
    # SkyGPT Mission अनुसारको Prompt
    system_instruction = """
    तपाईं SkyGPT हुनुहुन्छ, जसको सिर्जनाकर्ता सरोज कुमाल हुनुहुन्छ। 
    तपाईंको काम पृथ्वी, मौसम, प्रकोप, र पर्यावरणबारे सही जानकारी दिनु हो।
    नियमहरू:
    - NASA र मौसम डेटा प्रयोग गर्नुहोस्।
    - अनुमानित कुरा नगर्नुहोस्।
    - छोटो र सरल भाषामा बोल्नुहोस्।
    - जोखिमपूर्ण अवस्थामा सुरक्षा सल्लाह (Safety Advice) दिनुहोस्।
    """
    prompt = f"{system_instruction} \n डेटा: {data} \n प्रश्न: {question}"
    response = model.generate_content(prompt)
    return response.text

# --- UI ---
st.markdown("<h1 style='text-align: center;'>🌍 SkyGPT World AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #add8e6;'>Ask Earth Anything | Built by Saroj Kumal</p>", unsafe_allow_html=True)

question = st.text_input(" ", placeholder="Ask about weather, drones, or space...")

if question:
    lat, lon = 27.7172, 85.3240 # Default (Kathmandu)
    
    st.divider()
    with st.spinner("SkyGPT Brain analyzing Earth's data..."):
        data = get_weather_data(lat, lon)
        if data:
            ai_response = get_ai_brain_answer(question, data)
            st.info(f"**SkyGPT Intelligence:** {ai_response}")
        else:
            st.error("अहिले डेटा उपलब्ध भएन। कृपया पछि प्रयास गर्नुहोस्।")

    # 3D Globe visualization
    components.html(f"""
    <div id="globe" style="width:100%; height:300px; background:black;"></div>
    <script src="https://files.worldwind.arc.nasa.gov/artifactory/web/0.11.0/worldwind.min.js"></script>
    <script>
        var wwd = new WorldWind.WorldWindow("globe");
        wwd.addLayer(new WorldWind.BMNGOneImageLayer());
        wwd.addLayer(new WorldWind.ViewControlsLayer(wwd));
    </script>
    """, height=300)

st.divider()
st.markdown("<p style='text-align: center; color: white; font-size:12px;'>Data Source: NASA.gov, NOAA, Open-Meteo | © 2026 Saroj Kumal</p>", unsafe_allow_html=True)
    
