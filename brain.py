""" 
SkyGPT World AI - Core Brain v9.5 Global Production
CREATOR: Saroj Kumal | STATUS: 10K+ users ready
FIX: Global Error Msgs, Gemini Worldwide Location, SMS-Optimized, Nominatim TOS
""" 
import streamlit as st 
import google.generativeai as genai 
import aiohttp 
import asyncio 
from aiolimiter import AsyncLimiter 
import re 
import hashlib 
import atexit 
import diskcache 
import logging 
import os 
from typing import Dict, Any, List, Optional 
from datetime import datetime 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') 
logger = logging.getLogger("SkyGPT") 

NOMINATIM_LIMITER = AsyncLimiter(1, 1)
NOMINATIM_HEADERS = {
    "User-Agent": "SkyGPT-WorldAI/9.5 (https://github.com/sarojkumal/skygpt; contact@skygpt.world)",
    "Accept-Language": "en" 
} 
GEMINI_TIMEOUT = 8.0 
CACHE_DIR = os.getenv('CACHE_DIR', '/tmp/skygpt_geocode') 
GEO_CACHE = diskcache.Cache(CACHE_DIR) 
_session: Optional[aiohttp.ClientSession] = None 

@st.cache_resource(show_spinner=False) 
def get_http_session() -> aiohttp.ClientSession:
    global _session 
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=10, connect=3, sock_read=5) 
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ttl_dns_cache=300, force_close=False, enable_cleanup_closed=True) 
        _session = aiohttp.ClientSession(connector=connector, timeout=timeout, headers=NOMINATIM_HEADERS) 
        def _cleanup():
            if _session and not _session.closed:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running(): loop.create_task(_session.close())
                    else: asyncio.run(_session.close())
                except Exception as e: logger.error(f"Session cleanup error: {e}")
        atexit.register(_cleanup) 
        logger.info("HTTP Session initialized") 
    return _session 

@st.cache_resource(show_spinner=False) 
def configure_gemini():
    try:
        api_key = st.secrets["GEMINI_API_KEY"] 
        genai.configure(api_key=api_key) 
        model = genai.GenerativeModel('gemini-1.5-flash') 
        logger.info("Gemini configured successfully") 
        return model 
    except KeyError:
        logger.error("GEMINI_API_KEY missing in Streamlit Secrets") 
        return None 
    except Exception as e:
        logger.error(f"Gemini config failed: {e}") 
        return None 

def sanitize_query(query: str) -> str:
    if not query: return "" 
    query = query[:200] 
    query = re.sub(r'[<>{}\[\]\\^`]', '', query) 
    redos_patterns = [r'(a+)+', r'([a-zA-Z0-9])\1{20,}', r'(.*a){10,}', r'(x+x+)+y'] 
    for pattern in redos_patterns:
        if re.search(pattern, query): raise ValueError("Invalid query pattern") 
    ssrf_patterns = [r'(localhost|127\.0\.0\.1|0\.0\.0\.0)', r'(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)', r'(169\.254\.|metadata\.google|metadata\.azure)', r'(file://|ftp://|dict://|gopher://)'] 
    for pattern in ssrf_patterns:
        if re.search(pattern, query, re.I): raise ValueError("Invalid location") 
    return query.strip() 

def detect_user_language(text: str) -> str:
    if not text: return "en" 
    nepali_chars = re.findall(r'[\u0900-\u097F]', text) 
    if len(nepali_chars) > 3: return "ne"
    # Add more: Hindi, Bengali, etc for 100+ lang support
    hindi_chars = re.findall(r'[\u0900-\u097F]', text)
    if len(hindi_chars) > 3: return "hi"
    return "en" 

async def extract_location_multilingual(text: str, lang_code: str = "en") -> str:
    """Gemini-powered worldwide location extraction. SMS-optimized."""
    if not text: return "" 
    model = configure_gemini() 
    if not model: return _extract_location_regex(text) 
    
    prompt = f"""Extract ONLY city/town/location from text. Return name only. If none, return 'None'.
Text: "{text}"
Examples: "Kathmandu ko mausam" -> Kathmandu, "Flood in Tokyo?" -> Tokyo, "Rio de Janeiro ma" -> Rio de Janeiro
Location:"""
    
    try:
        response = await asyncio.wait_for(model.generate_content_async(prompt), timeout=5.0) 
        location = re.sub(r'[^\w\s,.-]', '', response.text.strip()).replace("None", "").strip() 
        if len(location) > 2:
            logger.info(f"Gemini extracted: {location}") 
            return location 
        return _extract_location_regex(text)
    except Exception as e:
        logger.error(f"Gemini extract failed: {e}") 
        return _extract_location_regex(text) 

def _extract_location_regex(text: str) -> str:
    if not text: return "" 
    patterns = [r'\b(?:in|at|of|near|from)\s+([A-Z][A-Za-z\s,.-]{2,40})', r'([A-Z][A-Za-z\s,.-]{2,40})\s+(?:ko|ma|city)', r'^([A-Z][A-Za-z\s,.-]{3,40})$'] 
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE) 
        if match:
            loc = match.group(1).strip() 
            if loc.lower() not in ['the','weather','flood','risk','today','tomorrow']: return loc.title()
    return "" 

async def geocode_location_safe(query: str) -> Optional[Dict]:
    if not query or len(query) < 2: return None 
    try: query = sanitize_query(query) 
    except ValueError: return None 
    cache_key = f"geocode:{hashlib.sha256(query.lower().encode()).hexdigest()}" 
    if cache_key in GEO_CACHE: return GEO_CACHE[cache_key] 
    result = await _geocode_nominatim(query) or await _geocode_photon(query) 
    GEO_CACHE.set(cache_key, result, expire=2592000) 
    return result 

async def _geocode_nominatim(query: str) -> Optional[Dict]:
    url = "https://nominatim.openstreetmap.org/search" 
    params = {"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1} 
    session = get_http_session() 
    try:
        async with NOMINATIM_LIMITER:
            async with session.get(url, params=params) as resp:
                if resp.status != 200: return None 
                data = await resp.json() 
                if not data: return None 
                item = data[0] 
                return {"lat": float(item["lat"]), "lon": float(item["lon"]), "display": item["display_name"], "type": item.get("type", ""), "source": "nominatim"} 
    except Exception as e:
        logger.error(f"Nominatim error: {e}") 
        return None 

async def _geocode_photon(query: str) -> Optional[Dict]:
    url = "https://photon.komoot.io/api/" 
    params = {"q": query, "limit": 1} 
    session = get_http_session() 
    try:
        async with session.get(url, params=params) as resp:
            if resp.status != 200: return None 
            data = await resp.json() 
            features = data.get("features", []) 
            if not features: return None 
            f = features[0]; props = f["properties"]; coords = f["geometry"]["coordinates"] 
            return {"lat": coords[1], "lon": coords[0], "display": f"{props.get('name', '')}, {props.get('country', '')}", "type": props.get("type", ""), "source": "photon"} 
    except Exception as e:
        logger.error(f"Photon error: {e}") 
        return None 

def assess_landslide_risk_lhasa(lat: float, lon: float, rain_24h: float, slope: float = 15.0, soil_moisture: float = 0.3) -> Dict:
    try:
        lat = max(-90, min(90, lat)); lon = max(-180, min(180, lon)); rain_24h = max(0, rain_24h)
        slope_factor = min(slope / 30.0, 1.0); rain_factor = min(rain_24h / 150.0, 1.0); soil_factor = min(soil_moisture / 0.5, 1.0)
        if 26.0 < lat < 31.0 and 80.0 < lon < 93.0: himalayan_boost, region = 1.4, "Himalayan"
        elif 30.0 < lat < 40.0 and 70.0 < lon < 80.0: himalayan_boost, region = 1.2, "Hindu Kush"
        else: himalayan_boost, region = 1.0, "Global"
        probability = rain_factor * slope_factor * soil_factor * himalayan_boost * 0.7
        probability = min(max(probability, 0.0), 0.95)
        if probability > 0.7: level, msg = "HIGH", f"{probability*100:.0f}% landslide risk {region}. {rain_24h}mm rain. EVACUATE steep areas."
        elif probability > 0.4: level, msg = "MEDIUM", f"{probability*100:.0f}% landslide chance. Avoid slopes."
        else: level, msg = "LOW", f"{probability*100:.0f}% risk. Stable."
        return {"level": level, "msg": msg, "probability": round(probability, 2), "region": region}
    except Exception as e:
        logger.error(f"LHASA error: {e}")
        return {"level": "LOW", "msg": "Risk data unavailable.", "probability": 0.1, "region": "Unknown"}

async def get_ai_response_multilingual(prompt: str, context: Dict[str, Any], messages: List, sms_mode: bool = False) -> str:
    """SMS-optimized: <160 chars if sms_mode=True"""
    model = configure_gemini() 
    if not model:
        return "AI offline. Check API key. For emergencies, contact local authorities." if not sms_mode else "AI offline. Call local emergency." 
    
    if isinstance(context, dict) and "error" in context:
        lang = context.get("lang", "en") 
        if context["error"] == "no_location":
            return "Add location. Ex: 'Flood risk Tokyo?'" if lang == "en" else "Thau lekhnus. Ex: 'Tokyo ma badhi?'"
        if context["error"] == "location_not_found":
            return f"Location '{context['query']}' not found. Try 'City,Country'" if lang == "en" else f"'{context['query']}' bhetayena. 'Sahar,Desh' lekhnus"
    
    location = context.get("location", {}); weather = context.get("weather", {}); flood_risk = context.get("flood_risk", {}); landslide_risk = context.get("landslide_risk", {}); lang = context.get("lang", "en") 
    
    if sms_mode:
        # SMS: 160 char max
        return f"{landslide_risk.get('level','?')} RISK {location.get('display','?')[:20]}. Rain:{weather.get('rain_24h',0)}mm. {landslide_risk.get('msg','')[:60]}"
    
    system_prompt = f"""You are SkyGPT World AI v9.5 by Saroj Kumal. Global disaster expert.
LOCATION: {location.get('display', 'Unknown')}
COORDS: {location.get('lat', 0):.4f}, {location.get('lon', 0):.4f}
WEATHER: {weather.get('temp', 0)}°C, Wind {weather.get('wind', 0)}km/h, Rain24h: {weather.get('rain_24h', 0)}mm
FLOOD: {flood_risk.get('level', '?')} - {flood_risk.get('msg', '')}
LANDSLIDE: {landslide_risk.get('level', '?')} - {landslide_risk.get('msg', '')} | Prob: {landslide_risk.get('probability', 0)*100:.0f}%
User Q: {prompt}

RULES: Answer in {lang}. Use data. <150 words. Start with 🟢/🟡/🔴. 1 safety action. No AI mention. No disclaimer. If HIGH, start "⚠️ URGENT:"
""" 
    
    try:
        response = await asyncio.wait_for(model.generate_content_async(system_prompt), timeout=GEMINI_TIMEOUT) 
        return response.text 
    except asyncio.TimeoutError:
        return f"⚠️ Delayed. Data shows: {landslide_risk.get('level', 'Unknown')} risk. Check official sources." 
    except Exception as e:
        logger.error(f"Gemini error: {e}") 
        return "⚠️ AI error. For urgent info, check NOAA/IMD or local met dept."
