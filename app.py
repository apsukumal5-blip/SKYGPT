import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="SkyGPT", page_icon="🛰️", layout="wide")

# --- CONFIG - TAPAILE KO NAAM MATRA ---
CREATOR = "Saroj Kumal"

# --- UI - CLEAN, ARU KEHI CHAINA ---
st.markdown(f"<h2 style='text-align: center; margin-bottom:0;'>🛰️ SkyGPT</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; margin-top:0; color:grey;'>by {CREATOR}</p>", unsafe_allow_html=True)

# --- LOCATION SEARCH ---
col1, col2, col3 = st.columns([2,1,2])
with col2:
    location = st.text_input(" ", "Mt Everest", label_visibility="collapsed", placeholder="Search: Mt Everest, Lukla, Pentagon...")

# --- COORDINATE DATABASE ---
coords = {
    "mt everest": [27.9881, 86.9250], "everest": [27.9881, 86.9250],
    "everest base camp": [28.0026, 86.8528], "ebc": [28.0026, 86.8528],
    "lukla": [27.6869, 86.7314], "lukla airport": [27.6869, 86.7314],
    "kathmandu": [27.7172, 85.3240], "pokhara": [28.2096, 83.9856],
    "annapurna": [28.5956, 83.8203], "k2": [35.8808, 76.5155],
    "pentagon": [38.8719, -77.0563], "tokyo": [35.6762, 139.6503],
    "area 51": [37.2431, -115.7930], "denwa": [27.5866, 84.0558]
}
lat, lon = coords.get(location.lower(), [27.9881, 86.9250])

# --- NASA WEBWORLDWIND 3D GLOBE ---
# Yei ho tapaile diyeko 3 ta HTML: BasicExample + GoToLocation + Placemarks ko mix
# Bootstrap, jQuery sabai hataidiye. 100% NASA Core matra.
nasa_html = f"""
<!DOCTYPE html><html><head>
<meta charset="utf-8">
<script src="https://files.worldwind.arc.nasa.gov/artifactory/web/0.11.0/worldwind.min.js"></script>
<style>body{{margin:0; background:black;}}</style>
</head><body>
<canvas id="canvasOne" style="width:100%; height:90vh;"></canvas>
<script>
    // 1. BasicExample.html ko Globe
    var wwd = new WorldWind.WorldWindow("canvasOne");
    wwd.addLayer(new WorldWind.BMNGOneImageLayer());
    wwd.addLayer(new WorldWind.BMNGLandsatLayer());
    wwd.addLayer(new WorldWind.BingAerialWithLabelsLayer());
    wwd.addLayer(new WorldWind.CompassLayer());
    wwd.addLayer(new WorldWind.ViewControlsLayer(wwd));

    // 2. GoToLocation.html ko Search Feature
    wwd.goTo(new WorldWind.Position({lat}, {lon}, 25000.0));

    // 3. PlacemarksAndPicking.html ko Pin Feature
    var placemarkLayer = new WorldWind.RenderableLayer("Placemarks");
    wwd.addLayer(placemarkLayer);
    
    var placemarkAttributes = new WorldWind.PlacemarkAttributes(null);
    placemarkAttributes.imageScale = 1;
    placemarkAttributes.imageColor = WorldWind.Color.RED;
    placemarkAttributes.labelAttributes.color = WorldWind.Color.YELLOW;
    placemarkAttributes.labelAttributes.offset = new WorldWind.Offset(
        WorldWind.OFFSET_FRACTION, 0.5,
        WorldWind.OFFSET_FRACTION, 1.5);
    
    var placemark = new WorldWind.Placemark(new WorldWind.Position({lat}, {lon}, 100));
    placemark.label = "{location}";
    placemark.altitudeMode = WorldWind.RELATIVE_TO_GROUND;
    placemark.attributes = placemarkAttributes;
    
    placemarkLayer.addRenderable(placemark);
</script></body></html>
"""

components.html(nasa_html, height=750)
