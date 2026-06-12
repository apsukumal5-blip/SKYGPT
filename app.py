import streamlit as st
import streamlit.components.v1 as components
import requests
import google.generativeai as genai

# १. Page Config
st.set_page_config(page_title="SkyGPT World AI", page_icon="🌍", layout="wide")

# प्रोफेसनल लुक्स र ब्याकग्राउन्डको लागि CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1451187580459-43490279c0fa'); 
             background-size: cover; color: white; }
    h1, h2, h3 { color: #ffffff; text-shadow: 2px 2px 4px #000000; }
    .css-1544g2n { color: white; }
    </style>
    """, unsafe_allow_html=True)

# २. Keys Setup
NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

CREATOR = "Saroj Kumal"

# Brain Function
def get_ai_brain_answer(question, data):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"तपाईं SkyGPT हुनुहुन्छ। यो डाटा: {data} को आधारमा प्रयोगकर्ताको प्रश्न '{question}' को उत्तर छोटो र स्पष्ट भाषामा दिनुहोस्।"
    return model.generate_content(prompt).text

# UI Header
st.markdown("<h1 style='text-align: center;'>🌍 SkyGPT World AI</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #add8e6;'>Ask Anything, Anywhere on Earth | Created by {CREATOR}</p>", unsafe_allow_html=True)

question = st.text_input(" ", placeholder="Ask: Lukla weather? ISS location? Disasters near me?")

if question:
    # Basic Geocoding Logic
    lat, lon = 27.7172, 85.3240 # Default Kathmandu
    
    st.divider()
    st.subheader(f"📡 SkyGPT Analysis for: {question}")
    
    with st.spinner("SkyGPT Brain searching global data..."):
        # यहाँ तपाईंको पुरानो Weather/NASA Logic राख्नुहोस्
        # उदाहरणको लागि एउटा डेटा कल:
        weather_api = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        data = requests.get(weather_api).json()
        
        # एआई ब्रेनको विश्लेषण
        ai_response = get_ai_brain_answer(question, data)
        st.info(f"**SkyGPT Intelligence:** {ai_response}")

    # 3D Globe
    nasa_html = f"""
    <div style="background:black; padding:10px;">
    <script src="https://files.worldwind.arc.nasa.gov/artifactory/web/0.11.0/worldwind.min.js"></script>
    <canvas id="canvasOne" style="width:100%; height:40vh;"></canvas>
    </div>"""
    components.html(nasa_html, height=400)

st.divider()
st.markdown(f"""
    <p style='text-align: center; color: white; font-size:12px;'>
    SkyGPT | Data Source: <b>NASA.gov</b>, NOAA.gov, Open-Meteo.com | Gemini AI Powered
    <br>© 2026 {CREATOR} | All Rights Reserved
    </p>""", unsafe_allow_html=True)
    
