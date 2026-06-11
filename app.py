import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime

st.set_page_config(page_title="SkyGPT World AI", page_icon="🌍", layout="wide")
CREATOR = "Saroj Kumal"
NASA_KEY = st.secrets.get("NASA_KEY", "DEMO_KEY")

st.markdown(f"<h1 style='text-align: center; margin-bottom:0;'>🌍 SkyGPT World AI</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; margin-top:0; color:grey;'>Ask Anything, Anywhere on Earth | by {CREATOR}</p>", unsafe_allow_html=True)

# --- WORLDWIDE QUESTION BOX ---
question = st.text_input(" ", placeholder="Ask: Can I fly drone in Lukla today? Will it rain in Tokyo? ISS over Nepal? Fire near Chitwan?", label_visibility="collapsed")

lat, lon, loc_name = 27.7172, 85.3240, "Kathmandu" # Default

# --- 1. QUESTION BUJHNE AI LOGIC - WORLDWIDE ---
if question:
    q = question.lower()

    # Geocoding: NASA ko Gazetteer use gareko - WorldWide kaam garcha
    try:
        geo_url = f"https://api.nasa.gov/planetary/earth/imagery?lon={lon}&lat={lat}&api_key={NASA_KEY}"
        # Location khojne - OpenStreetMap Nominatim free worldwide
        geo = requests.get(f"https://nominatim.openstreetmap.org/search?q={question}&format=json&limit=1",
                           headers={'User-Agent': 'SkyGPT-SarojKumal'}).json()
        if geo:
            lat, lon = float(geo[0]['lat']), float(geo[0]['lon'])
            loc_name = geo[0]['display_name'].split(',')[0]
    except: pass

# --- NASA 3D GLOBE - WORLDWIDE ---
nasa_html = f"""
<!DOCTYPE html><html><head>
<script src="https://files.worldwind.arc.nasa.gov/artifactory/web/0.11.0/worldwind.min.js"></script>
<style>body{{margin:0;}}</style></head><body>
<canvas id="canvasOne" style="width:100%; height:45vh;"></canvas>
<script>
    var wwd = new WorldWind.WorldWindow("canvasOne");
    wwd.addLayer(new WorldWind.BMNGOneImageLayer());
    wwd.addLayer(new WorldWind.BMNGLandsatLayer());
    wwd.addLayer(new WorldWind.ViewControlsLayer(wwd));
    wwd.goTo(new WorldWind.Position({lat}, {lon}, 30000.0));
    var layer = new WorldWind.RenderableLayer(); wwd.addLayer(layer);
    var placemark = new WorldWind.Placemark(new WorldWind.Position({lat}, {lon}, 100));
    placemark.label = "{loc_name}"; layer.addRenderable(placemark);
</script></body></html>
"""
components.html(nasa_html, height=400)

# --- 2. ANSWER ENGINE - HAREK QUESTION KO DETAIL ---
if question:
    st.divider()
    st.subheader(f"📡 SkyGPT Intel for: {question}")

    q = question.lower()

    # A. DRONE UDAUNE / PILOT DECISION - Sabai bhanda Important
    if any(word in q for word in ["drone", "fly", "udaune", "plane", "helicopter", "udna"]):
        st.success(f"**SkyGPT Flight Safety Check for {loc_name}**")
        try:
            # NOAA Weather Worldwide - Pilot haru ko data
            point = requests.get(f"https://api.weather.gov/points/{lat},{lon}", timeout=5).json()
            forecast = requests.get(point['properties']['forecast'], timeout=5).json()
            now = forecast['properties']['periods'][0]

            wind_speed = int(now['windSpeed'].split()[0])
            rain_chance = now.get('probabilityOfPrecipitation', {}).get('value', 0)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Wind Speed", now['windSpeed'])
            col2.metric("Rain Chance", f"{rain_chance}% 🌧️" if rain_chance else "0%")
            col3.metric("Forecast", now['shortForecast'])
            col4.metric("Visibility", "Good" if "Clear" in now['shortForecast'] else "Low")

            # PILOT DECISION - YEI HO #1 FEATURE
            if wind_speed > 25:
                st.error("❌ DO NOT FLY: Wind speed > 25 mph. Drone crash hune high risk.")
            elif rain_chance and rain_chance > 40:
                st.error(f"❌ DO NOT FLY: {rain_chance}% Rain chance. Electronics bigrancha.")
            elif "Fog" in now['shortForecast'] or "Snow" in now['shortForecast']:
                st.error("❌ DO NOT FLY: Low visibility. Fog/Snow ma drone harauncha.")
            else:
                st.success("✅ SAFE TO FLY: Aaja weather clear cha. Drone udaunu hos.")

            with st.expander("Full NOAA Pilot Report"):
                st.write(now['detailedForecast'])

        except:
            st.warning("US NOAA data yo location ma chaina. International area ho. General rule: Wind <25mph ra Rain chaina bhane udaune.")
            st.info("Try: Open-Meteo API backup - https://api.open-meteo.com/v1/forecast?latitude="+str(lat)+"&longitude="+str(lon)+"&current_weather=true")

    # B. RAIN / WEATHER DETAIL
    elif any(word in q for word in ["rain", "pani", "weather", "mausam", "temperature", "tapai", "garmi", "jarko"]):
        st.success(f"**Worldwide Weather Intel for {loc_name}**")
        try:
            # Open-Meteo: 100% Free, Worldwide, No Key
            weather = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,precipitation_probability,windspeed_10m").json()
            current = weather['current_weather']
            col1, col2, col3 = st.columns(3)
            col1.metric("Temperature", f"{current['temperature']}°C")
            col2.metric("Wind", f"{current['windspeed']} km/h")
            col3.metric("Condition", "Rain Likely" if current['weathercode'] > 50 else "Clear")

            # Aaja ko Rain Detail
            rain_hours = [i for i, v in enumerate(weather['hourly']['precipitation_probability'][:24]) if v > 40]
            if rain_hours:
                st.warning(f"🌧️ Aaja Rain: {len(rain_hours)} ghanta pani parne chance. Time: {rain_hours[0]}:00 - {rain_hours[-1]}:00")
            else:
                st.success("☀️ Aaja Rain Chaina. Gham lagcha.")
        except:
            st.error("Weather API failed. Check internet.")

    # C. DISASTER / FIRE / TSUNAMI
    elif any(word in q for word in ["fire", "aago", "tsunami", "flood", "baadh", "disaster", "khatra"]):
        st.success("**NASA EONET Global Disaster Tracker**")
        eonet = requests.get("https://eonet.gsfc.nasa.gov/api/v3/events?limit=5").json()
        for event in eonet['events']:
            st.error(f"**{event['title']}** - {event['categories'][0]['title']} - Source: NASA")

    # D. ISS / SPACE
    elif "iss" in q or "space station" in q:
        iss = requests.get("http://api.open-notify.org/iss-now.json").json()
        st.success(f"**ISS Live Over: {iss['iss_position']['latitude']}, {iss['iss_position']['longitude']}**")
        st.info("Speed: 27,600 km/h. 90 min ma prithvi ghumcha. Source: NASA")

    # E. DEFAULT: J PANI SODHNU BHAYO
    else:
        st.success(f"**Geo Intel for {loc_name}**")
        st.info(f"Latitude: {lat:.4f}, Longitude: {lon:.4f}. Ask 'weather', 'drone', 'rain', 'fire' for live NASA/NOAA data.")

st.divider()
st.markdown(f"<p style='text-align: center; color: grey; font-size:12px;'>SkyGPT = Sky + GPT. Global Mind ma Basne. Data: NASA.gov, NOAA.gov, Open-Meteo.com | Built by {CREATOR} | Apache 2.0</p>", unsafe_allow_html=True)
