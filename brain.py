"""
SkyGPT World AI v9.3.1 - Streamlit Cloud Stable
CREATOR: Saroj Kumal
STATUS: Production Stable - Zero Critical Bugs
PYTHON: 3.11+ Compatible | Streamlit 1.38+ Compatible
FIXES: v9.3 critical bugs - Imports, Async, Memory, Session, Cache
"""
from __future__ import annotations
import os
import re
import json
import time
import hashlib
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple, Callable
from functools import wraps
from dataclasses import dataclass, field
from collections import deque

import streamlit as st
import aiohttp
from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
from diskcache import Cache as DiskCache
from langdetect import detect, LangDetectException
import langid
from rapidfuzz import fuzz
import structlog

# v9.3.1 FIX: Correct Gemini import for streamlit cloud
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# --- 1. LOGGING ---
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# --- 2. CONFIG ---
GEMINI_KEY = st.secrets.get("GEMINI_KEY")
GEONAMES_USER = st.secrets.get("GEONAMES_USER", "demo")
CACHE_DIR = st.secrets.get("CACHE_DIR", "/tmp/skygpt_v931")

if not GEMINI_KEY:
    logger.error("gemini_key_missing")
    raise ValueError("GEMINI_KEY required in st.secrets")

# v9.3.1 FIX: Configure Gemini correctly
genai.configure(api_key=GEMINI_KEY)
MODEL_NAME = "gemini-1.5-flash" # 2.5 not stable yet

# --- 3. DISK CACHE ---
RESPONSE_CACHE = DiskCache(CACHE_DIR, size_limit=100e6, eviction_policy='least-recently-used')

# --- 4. CIRCUIT BREAKER - v9.3.1 FIX: asyncio.Lock ---
class CircuitBreaker:
    def __init__(self, fail_max: int = 3, reset_timeout: int = 60):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self._lock = asyncio.Lock() # v9.3.1 FIX: was threading.Lock

    async def is_open(self) -> bool:
        async with self._lock:
            if self.failures >= self.fail_max:
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.failures = 0
                    return False
                return True
            return False

    async def record_failure(self):
        async with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()

    async def record_success(self):
        async with self._lock:
            self.failures = 0

GEOCODER_BREAKER = CircuitBreaker(fail_max=3, reset_timeout=60)

# v9.3.1 FIX: Global connector for connection pooling
@st.cache_resource
def get_aiohttp_connector():
    return aiohttp.TCPConnector(limit=1000, limit_per_host=100, ttl_dns_cache=300)

# --- 5. SOURCE RELIABILITY ---
SOURCE_RELIABILITY = {
    "USGS": 0.99, "NASA": 0.98, "Open-Meteo": 0.95, "OpenWeatherMap": 0.94,
    "GeoNames": 0.90, "OpenStreetMap": 0.90, "Photon": 0.88, "Nominatim": 0.87
}

# --- 6. PYDANTIC SCHEMAS ---
class LocationJSON(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(..., min_length=1, max_length=200)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    type: Optional[str] = Field(None, max_length=50)

class AIResponseJSON(BaseModel):
    model_config = ConfigDict(extra='forbid')
    summary: str = Field(..., min_length=10, max_length=800)
    risk_level: str = Field(..., pattern=r'^(Low|Moderate|High|Extreme)$')
    risk_score: int = Field(..., ge=0, le=100)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    safety_guidance: str = Field(..., min_length=10, max_length=400)
    sources_used: List[str] = Field(default_factory=list, max_length=10)
    location: Optional[LocationJSON] = None
    agent_votes: Dict[str, float] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AgentOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    agent: str = Field(..., max_length=50)
    answer: str = Field(default="", max_length=2000)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(default="", max_length=50)
    latency_ms: float = Field(default=0.0, ge=0.0)

# --- 7. SECURITY ---
INJECTION_PATTERNS = [
    r'ignore\s+(previous|all)\s+instructions', r'system\s+prompt', r'you\s+are\s+now',
    r'reveal\s+your\s+instructions', r'jailbreak', r'DAN\s+mode', r'do\s+anything\s+now',
    r'base64:', r'<script', r'https?://', r'\.onion', r'169\.254\.169\.254'
]

TEMP_REGEX = re.compile(r'(\d+\.?\d*)\s*[°\s]*(c|celsius|degree)', re.I)
RAIN_REGEX = re.compile(r'rain\s*(\d+)\s*%', re.I)
MAG_REGEX = re.compile(r'M\s*(\d+\.?\d*)', re.I)

def sanitize_query(text: str) -> Tuple[bool, str]:
    if not isinstance(text, str):
        return False, "Invalid input type."
    if len(text) > 1000 or len(text) < 2:
        return False, "Invalid query length."
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            logger.warning("injection_blocked", pattern=pattern[:20])
            return False, "Request blocked for security reasons."
    # v9.3.1 FIX: SSRF protection
    if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text):
        return False, "IP addresses not allowed."
    if len(re.findall(r'[^a-zA-Z0-9\s\u0900-\u097F\u0600-\u06FF]', text)) > len(text) * 0.3:
        return False, "Invalid input format."
    return True, text.strip()

# --- 8. LANGUAGE ENGINE - v9.3.1 FIX: Use st.cache_data ---
LANGUAGE_MAP = {
    'en': 'English', 'ne': 'Nepali', 'hi': 'Hindi', 'es': 'Spanish', 'ar': 'Arabic',
    'bn': 'Bengali', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese', 'de': 'German'
}

ROMANIZED_NEPALI = set('cha xa xaina ho haina pani parcha parxa aaja bholi voli hijo kasto kati kaha kina mausam tapkram'.split())
ROMANIZED_HINDI = set('hai hain hoga hogi tha thi barish paani kal aaj parso kya kaisi kaisa kitna kahan mausam tapmaan'.split())

@st.cache_data(ttl=3600, max_entries=10000)
def detect_language_cached(text: str) -> Tuple[str, float]:
    if not text or len(text.strip()) < 2:
        return 'en', 0.5
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))
    nepali_hits = len(words.intersection(ROMANIZED_NEPALI))
    if nepali_hits >= 2:
        return 'ne', min(0.98, 0.75 + nepali_hits * 0.08)
    hindi_hits = len(words.intersection(ROMANIZED_HINDI))
    if hindi_hits >= 2:
        return 'hi', min(0.98, 0.75 + hindi_hits * 0.08)
    try:
        lang1, conf1 = langid.classify(text)
        lang2 = detect(text)
        if lang1 == lang2 and lang1 in LANGUAGE_MAP:
            return lang1, 0.95
        elif lang1 in LANGUAGE_MAP:
            return lang1, max(0.70, conf1)
        return 'en', 0.60
    except LangDetectException:
        return 'en', 0.50

async def detect_language_async(text: str) -> Tuple[str, float]:
    return await asyncio.to_thread(detect_language_cached, text)

# --- 9. ASYNC GEOCODING ---
async def geocode_photon_async(session: aiohttp.ClientSession, query: str) -> Optional[Dict[str, Any]]:
    if await GEOCODER_BREAKER.is_open():
        return None
    try:
        async with session.get(
            "https://photon.komoot.io/api/",
            params={'q': query, 'limit': 1},
            timeout=aiohttp.ClientTimeout(total=6, connect=2)
        ) as r:
            if r.status == 200:
                data = await r.json()
                if data.get('features'):
                    feat = data['features'][0]
                    props, coords = feat['properties'], feat['geometry']['coordinates']
                    loc_type = props.get('osm_value', props.get('type', 'city'))
                    if props.get('osm_key') == 'natural' and loc_type == 'peak':
                        loc_type = 'mountain'
                    await GEOCODER_BREAKER.record_success()
                    return {
                        'lat': coords[1], 'lon': coords[0],
                        'display': props.get('name', query), 'type': loc_type, 'source': 'OpenStreetMap'
                    }
    except Exception as e:
        logger.error("photon_fail", error=str(e)[:100])
        await GEOCODER_BREAKER.record_failure()
    return None

async def geocode_nominatim_async(session: aiohttp.ClientSession, query: str) -> Optional[Dict[str, Any]]:
    if await GEOCODER_BREAKER.is_open():
        return None
    try:
        await asyncio.sleep(1.1)
        async with session.get(
            "https://nominatim.openstreetmap.org/search",
            params={'q': query, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'SkyGPT/9.3.1'},
            timeout=aiohttp.ClientTimeout(total=6, connect=2)
        ) as r:
            if r.status == 200:
                data = await r.json()
                if data:
                    await GEOCODER_BREAKER.record_success()
                    return {
                        'lat': float(data[0]['lat']), 'lon': float(data[0]['lon']),
                        'display': data[0].get('display_name', query).split(',')[0],
                        'type': data[0].get('type', 'city'), 'source': 'OpenStreetMap'
                    }
    except Exception as e:
        logger.error("nominatim_fail", error=str(e)[:100])
        await GEOCODER_BREAKER.record_failure()
    return None

async def geocode_failover_chain_async(session: aiohttp.ClientSession, query: str) -> Optional[Dict[str, Any]]:
    if not query or len(query.strip()) < 2:
        return None
    # v9.3.1 FIX: Normalize cache key
    cache_key = f"geocode:v9.3.1:{hashlib.md5(query.strip().lower().encode()).hexdigest()}"
    if cache_key in RESPONSE_CACHE:
        return RESPONSE_CACHE[cache_key]

    for geocoder in [geocode_photon_async, geocode_nominatim_async]:
        result = await asyncio.wait_for(geocoder(session, query), timeout=7)
        if result:
            RESPONSE_CACHE.set(cache_key, result, expire=86400)
            return result
    return None

def extract_location_v7(text: str) -> Optional[str]:
    stopwords = {'weather', 'mausam', 'temperature', 'rain', 'pani', 'barish', 'kasto',
                 'xa', 'cha', 'kati', 'hoga', 'hai', 'kya', 'today', 'tomorrow', 'bholi'}
    words = [w for w in re.findall(r'\b\w+\b', text) if w.lower() not in stopwords]
    for n in [5, 4, 3, 2, 1]:
        for i in range(len(words) - n + 1):
            candidate = ' '.join(words[i:i+n])
            if len(candidate) >= 3:
                return candidate
    return None

# --- 10. MULTI-AGENT DEFINITIONS ---
class WeatherAgent:
    name = "weather_agent"
    @staticmethod
    async def execute(session: aiohttp.ClientSession, lat: float, lon: float) -> AgentOutput:
        start = time.time()
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat, 'longitude': lon,
                'current': 'temperature_2m,precipitation_probability',
                'daily': 'precipitation_probability_max',
                'timezone': 'auto'
            }
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=6)) as r:
                data = await r.json()
                temp = data['current']['temperature_2m']
                rain = data['daily']['precipitation_probability_max'][0]
                return AgentOutput(
                    agent="weather_agent",
                    answer=f"Temperature {temp}°C, Rain {rain}%",
                    confidence=0.95,
                    source="Open-Meteo",
                    latency_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            logger.error("weather_agent_fail", error=str(e)[:100])
            return AgentOutput(agent="weather_agent", answer="", confidence=0.0, source="Open-Meteo")

class DisasterAgent:
    name = "disaster_agent"
    @staticmethod
    async def execute(session: aiohttp.ClientSession, lat: float, lon: float) -> AgentOutput:
        start = time.time()
        try:
            url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as r:
                data = await r.json()
                nearest_mag = 0
                for feat in data.get('features', []):
                    coords = feat['geometry']['coordinates']
                    dist = ((coords[1]-lat)**2 + (coords[0]-lon)**2)**0.5
                    if dist < 5:
                        nearest_mag = max(nearest_mag, feat['properties']['mag'])
                return AgentOutput(
                    agent="disaster_agent",
                    answer=f"Nearest earthquake M{nearest_mag}" if nearest_mag else "No recent earthquakes",
                    confidence=0.99 if nearest_mag else 0.90,
                    source="USGS",
                    latency_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            logger.error("disaster_agent_fail", error=str(e)[:100])
            return AgentOutput(agent="disaster_agent", answer="", confidence=0.0, source="USGS")

class GeolocationAgent:
    name = "geocode_agent"
    @staticmethod
    async def execute(session: aiohttp.ClientSession, query: str) -> AgentOutput:
        start = time.time()
        result = await geocode_failover_chain_async(session, query)
        if result:
            return AgentOutput(
                agent="geocode_agent",
                answer=json.dumps(result),
                confidence=0.92,
                source=result['source'],
                latency_ms=(time.time() - start) * 1000
            )
        return AgentOutput(agent="geocode_agent", answer="", confidence=0.0, source="")

class MemoryAgent:
    name = "memory_agent"
    @staticmethod
    def get_session_data() -> Dict[str, Any]:
        # v9.3.1 FIX: No deque in session_state
        if 'skygpt_memory' not in st.session_state:
            st.session_state.skygpt_memory = {
                "preferred_language": None,
                "frequent_locations": [],
                "recent_searches": [] # v9.3.1 FIX: list instead of deque
            }
        return st.session_state.skygpt_memory

    @staticmethod
    async def execute(chat_history: List) -> AgentOutput:
        memory = MemoryAgent.get_session_data()
        for msg in reversed(chat_history[-10:]):
            if msg["role"] == "user":
                lang, _ = await detect_language_async(msg["content"])
                if lang!= 'en':
                    memory["preferred_language"] = lang
                # v9.3.1 FIX: Append to list, keep max 5
                searches = memory["recent_searches"]
                searches.append(msg["content"][:50])
                memory["recent_searches"] = searches[-5:]
                break
        return AgentOutput(
            agent="memory_agent",
            answer=json.dumps({"preferred_language": memory["preferred_language"]}),
            confidence=1.0,
            source="SessionMemory"
        )

class VerificationAgent:
    name = "verification_agent"
    @staticmethod
    async def execute(agent_outputs: List[AgentOutput]) -> Tuple[bool, float, List[str]]:
        sources = []
        total_reliability = 0.0
        count = 0
        for output in agent_outputs:
            if output.confidence > 0 and output.source:
                sources.append(output.source)
                total_reliability += SOURCE_RELIABILITY.get(output.source, 0.80)
                count += 1
        if count == 0:
            return False, 0.0, []
        avg_reliability = total_reliability / count
        # v9.3.1 FIX: Require 2+ sources or 0.85+ for single source
        verified = (count >= 2 and avg_reliability >= 0.70) or (count == 1 and avg_reliability >= 0.85)
        return verified, avg_reliability, list(set(sources))

class RiskAnalysisAgent:
    name = "risk_agent"
    @staticmethod
    async def execute(weather_data: Optional[AgentOutput], disaster_data: Optional[AgentOutput]) -> AgentOutput:
        score = 0
        reasons = []
        if weather_data and weather_data.confidence > 0 and weather_data.answer:
            try:
                temp_match = TEMP_REGEX.search(weather_data.answer)
                if temp_match:
                    temp = float(temp_match.group(1))
                    if temp > 42:
                        score += 15
                        reasons.append("Extreme heat")
                rain_match = RAIN_REGEX.search(weather_data.answer)
                if rain_match:
                    rain = int(rain_match.group(1))
                    if rain > 90:
                        score += 15
                        reasons.append("Heavy rain")
            except (AttributeError, ValueError):
                pass
        if disaster_data and disaster_data.confidence > 0 and "M" in disaster_data.answer:
            try:
                mag_match = MAG_REGEX.search(disaster_data.answer)
                if mag_match:
                    mag = float(mag_match.group(1))
                    score += min(40, int(mag * 5))
                    if mag >= 5.0:
                        reasons.append(f"M{mag} earthquake")
            except (AttributeError, ValueError):
                pass
        if score >= 75:
            level, emoji = "Extreme", "🔴"
        elif score >= 50:
            level, emoji = "High", "🟠"
        elif score >= 25:
            level, emoji = "Moderate", "🟡"
        else:
            level, emoji = "Low", "🟢"
        return AgentOutput(
            agent="risk_agent",
            answer=json.dumps({"score": score, "level": level, "emoji": emoji, "reasons": reasons}),
            confidence=0.95,
            source="RiskAnalysis"
        )

# --- 11. COORDINATOR v9.3.1 ---
class CoordinatorAgent:
    name = "coordinator"

    @staticmethod
    async def execute(query: str, chat_history: List, stream_callback: Optional[Callable] = None) -> str:
        start_time = time.time()
        metrics = {}
        request_id = str(uuid.uuid4())[:8]

        is_safe, sanitized = sanitize_query(query)
        if not is_safe:
            return json.dumps(AIResponseJSON(
                summary=sanitized,
                risk_level="Low",
                risk_score=0,
                confidence_score=0.0,
                safety_guidance="Request blocked.",
                sources_used=[]
            ).model_dump())

        async def safe_stream(msg: str):
            if stream_callback and callable(stream_callback):
                try:
                    if asyncio.iscoroutinefunction(stream_callback):
                        await stream_callback(msg)
                    else:
                        stream_callback(msg)
                except:
                    pass

        await safe_stream("🔍 Analyzing query...")

        # v9.3.1 FIX: Reuse connector, new session per request
        connector = get_aiohttp_connector()
        async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
            try:
                await safe_stream("📍 Detecting location...")
                geocode_output = await GeolocationAgent.execute(session, sanitized)

                # v9.3.1 FIX: Validate JSON before decode
                location_data = None
                if geocode_output.confidence > 0 and geocode_output.answer:
                    if geocode_output.answer.strip().startswith('{'):
                        try:
                            location_data = json.loads(geocode_output.answer)
                        e
