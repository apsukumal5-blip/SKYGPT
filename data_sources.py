"""
PROJECT: SkyGPT World AI - Data Sources Module v3.2
CREATOR: Saroj Kumal
STATUS: Production Stable - June 28/29 Launch
PYTHON: 3.11+ Compatible | Streamlit Cloud Compatible
FIXES: Exception handling, URL injection, timeouts, validation, logging
"""
import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import re

# --- 1. LOGGING SETUP ---
logger = logging.getLogger(__name__)

# --- 2. CONSTANTS - v3.2: No demo keys in production ---
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
PHOTON_URL = "https://photon.komoot.io/api/"
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
ISS_URL = "http://api.open-notify.org/iss-now.json"

# v3.2 FIX: Proper User-Agent per Nominatim policy
HEADERS = {
    "User-Agent": "SkyGPT-WorldAI/3.2 (+https://github.com/skygpt; contact@skygpt.ai)"
}

# v3.2 FIX: Global timeout for all requests
REQUEST_TIMEOUT = 6

# --- 3. GEOCODING FUNCTIONS ---

def geocode_nominatim(query: str) -> List[Dict[str, Any]]:
    """
    Geocode using Nominatim OpenStreetMap.
    v3.2 FIXES:
    ISSUE: Bare except, no timeout, no User-Agent, string interpolation risk
    IMPACT: App freeze on slow DNS, 403 banned by Nominatim, crash on invalid JSON
    FIX: Specific exceptions, params dict, headers, timeout, JSON validation
    """
    if not query or len(query.strip()) < 2:
        logger.warning(f"nominatim_invalid_query: {query}")
        return []

    # v3.2 FIX: Use params dict to prevent injection
    params = {
        'q': query.strip(),
        'format': 'json',
        'limit': 5,
        'addressdetails': 1
    }

    try:
        # v3.2 FIX: Headers + timeout required by Nominatim
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        # v3.2 FIX: Validate JSON before access
        data = response.json()
        if not isinstance(data, list):
            logger.error(f"nominatim_invalid_response_type: {type(data)}")
            return []

        results = []
        for item in data[:5]:
            # v3.2 FIX: None-safe access with.get()
            if not isinstance(item, dict):
                continue
            lat = item.get('lat')
            lon = item.get('lon')
            display = item.get('display_name', query)

            # v3.2 FIX: Validate coordinates before return
            try:
                lat_f, lon_f = float(lat), float(lon)
                if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                    results.append({
                        'lat': lat_f,
                        'lon': lon_f,
                        'display': display.split(',')[0] if ',' in display else display,
                        'type': item.get('type', 'city'),
                        'source': 'Nominatim'
                    })
            except (TypeError, ValueError):
                logger.warning(f"nominatim_invalid_coords: {lat}, {lon}")
                continue

        logger.info(f"nominatim_success: {len(results)} results for {query[:30]}")
        return results

    except requests.exceptions.Timeout:
        logger.error(f"nominatim_timeout: {query[:30]}")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"nominatim_http_error: {e.response.status_code} | {query[:30]}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"nominatim_request_fail: {str(e)[:100]}")
        return []
    except ValueError as e: # JSON decode error
        logger.error(f"nominatim_json_error: {str(e)[:100]}")
        return []

def geocode_photon(query: str) -> List[Dict[str, Any]]:
    """
    Geocode using Photon Komoot. Fallback for Nominatim.
    v3.2 FIXES:
    ISSUE: Same as Nominatim - bare except, no timeout, no validation
    IMPACT: Crash on API down, invalid coords returned
    FIX: Specific exceptions, coordinate validation, type hints
    """
    if not query or len(query.strip()) < 2:
        return []

    params = {'q': query.strip(), 'limit': 5}

    try:
        response = requests.get(
            PHOTON_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        # v3.2 FIX: Validate GeoJSON structure
        if not isinstance(data, dict) or 'features' not in data:
            logger.error("photon_invalid_geojson")
            return []

        features = data.get('features', [])
        if not isinstance(features, list):
            return []

        results = []
        for feat in features[:5]:
            if not isinstance(feat, dict):
                continue

            props = feat.get('properties', {})
            geom = feat.get('geometry', {})
            coords = geom.get('coordinates', [])

            if not isinstance(coords, list) or len(coords) < 2:
                continue

            try:
                lon, lat = float(coords[0]), float(coords[1])
                if -180 <= lon <= 180 and -90 <= lat <= 90:
                    loc_type = props.get('osm_value', props.get('type', 'city'))
                    if props.get('osm_key') == 'natural' and loc_type == 'peak':
                        loc_type = 'mountain'

                    results.append({
                        'lat': lat,
                        'lon': lon,
                        'display': props.get('name', query),
                        'type': loc_type,
                        'source': 'Photon'
                    })
            except (TypeError, ValueError, IndexError):
                logger.warning(f"photon_invalid_coords: {coords}")
                continue

        logger.info(f"photon_success: {len(results)} results")
        return results

    except requests.exceptions.Timeout:
        logger.error("photon_timeout")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"photon_request_fail: {str(e)[:100]}")
        return []
    except ValueError:
        logger.error("photon_json_error")
        return []

# --- 4. WEATHER DATA ---

def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get weather from Open-Meteo.
    v3.2 FIXES:
    ISSUE: No coordinate validation, bare except, no timeout
    IMPACT: API call with lat=999 crashes, app freeze, no error context
    FIX: Validate coords first, specific exceptions, default return
    """
    # v3.2 FIX: Validate coordinates before API call
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        logger.error(f"weather_invalid_coords_type: {lat}, {lon}")
        return {"error": "invalid_coordinates", "temp": None, "rain": None}

    if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
        logger.error(f"weather_coords_out_of_range: {lat_f}, {lon_f}")
        return {"error": "coordinates_out_of_range", "temp": None, "rain": None}

    params = {
        'latitude': lat_f,
        'longitude': lon_f,
        'current': 'temperature_2m,precipitation_probability,wind_speed_10m',
        'daily': 'precipitation_probability_max,temperature_2m_max,temperature_2m_min',
        'timezone': 'auto'
    }

    try:
        response = requests.get(
            OPENMETEO_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        # v3.2 FIX: None-safe nested access
        current = data.get('current', {})
        daily = data.get('daily', {})

        result = {
            'temp': current.get('temperature_2m'),
            'rain_prob': current.get('precipitation_probability'),
            'wind': current.get('wind_speed_10m'),
            'daily_rain_max': daily.get('precipitation_probability_max', [None])[0],
            'temp_max': daily.get('temperature_2m_max', [None])[0],
            'temp_min': daily.get('temperature_2m_min', [None])[0],
            'source': 'Open-Meteo',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"weather_success: {lat_f:.2f},{lon_f:.2f}")
        return result

    except requests.exceptions.Timeout:
        logger.error(f"weather_timeout: {lat_f},{lon_f}")
        return {"error": "timeout", "temp": None, "rain": None, "source": "Open-Meteo"}
    except requests.exceptions.HTTPError as e:
        logger.error(f"weather_http_error: {e.response.status_code}")
        return {"error": f"http_{e.response.status_code}", "temp": None, "source": "Open-Meteo"}
    except requests.exceptions.RequestException as e:
        logger.error(f"weather_request_fail: {str(e)[:100]}")
        return {"error": "request_failed", "temp": None, "source": "Open-Meteo"}
    except (ValueError, KeyError, IndexError) as e:
        logger.error(f"weather_parse_error: {str(e)[:100]}")
        return {"error": "parse_failed", "temp": None, "source": "Open-Meteo"}

# --- 5. DISASTER DATA ---

def get_earthquakes() -> List[Dict[str, Any]]:
    """
    Get recent earthquakes from USGS.
    v3.2 FIXES:
    ISSUE: Bare except, no None handling, no timeout
    IMPACT: Crash if USGS returns null fields, app freeze
    FIX: Specific exceptions,.get() with defaults, timeout
    """
    try:
        response = requests.get(
            USGS_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        # v3.2 FIX: Validate structure
        features = data.get('features', [])
        if not isinstance(features, list):
            logger.error("usgs_invalid_features_type")
            return []

        results = []
        for feat in features[:20]: # Limit to 20 most recent
            if not isinstance(feat, dict):
                continue

            props = feat.get('properties', {})
            geom = feat.get('geometry', {})
            coords = geom.get('coordinates', [None, None, None])

            # v3.2 FIX: None-safe access
            if not isinstance(coords, list) or len(coords) < 2:
                continue

            try:
                results.append({
                    'magnitude': float(props.get('mag', 0)),
                    'place': props.get('place', 'Unknown'),
                    'time': props.get('time', 0),
                    'lat': float(coords[1]) if coords[1] is not None else None,
                    'lon': float(coords[0]) if coords[0] is not None else None,
                    'depth': float(coords[2]) if len(coords) > 2 and coords[2] is not None else None,
                    'url': props.get('url', ''),
                    'source': 'USGS'
                })
            except (TypeError, ValueError, IndexError):
                logger.warning(f"usgs_invalid_earthquake_data: {props.get('place')}")
                continue

        logger.info(f"usgs_success: {len(results)} earthquakes")
        return results

    except requests.exceptions.Timeout:
        logger.error("usgs_timeout")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"usgs_request_fail: {str(e)[:100]}")
        return []
    except ValueError:
        logger.error("usgs_json_error")
        return []

def get_eonet_events() -> List[Dict[str, Any]]:
    """
    Get EONET natural events from NASA.
    v3.2 FIXES:
    ISSUE: Bare except, no timeout, no validation
    IMPACT: Crash on API change, freeze on slow network
    FIX: Specific exceptions, structure validation
    """
    params = {'status': 'open', 'limit': 20}

    try:
        response = requests.get(
            EONET_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        events = data.get('events', [])
        if not isinstance(events, list):
            logger.error("eonet_invalid_events_type")
            return []

        results = []
        for event in events:
            if not isinstance(event, dict):
                continue

            # v3.2 FIX: None-safe access
            categories = event.get('categories', [])
            cat_title = categories[0].get('title', 'Unknown') if categories and isinstance(categories[0], dict) else 'Unknown'

            geometry = event.get('geometry', [])
            if geometry and isinstance(geometry, list) and len(geometry) > 0:
                last_geom = geometry[-1]
                coords = last_geom.get('coordinates', [None, None])
            else:
                coords = [None, None]

            try:
                results.append({
                    'id': event.get('id', ''),
                    'title': event.get('title', 'Unknown Event'),
                    'category': cat_title,
                    'lat': float(coords[1]) if coords[1] is not None else None,
                    'lon': float(coords[0]) if coords[0] is not None else None,
                    'date': event.get('geometry', [{}])[-1].get('date', '') if event.get('geometry') else '',
                    'source': 'NASA EONET'
                })
            except (TypeError, ValueError, IndexError):
                logger.warning(f"eonet_invalid_event: {event.get('id')}")
                continue

        logger.info(f"eonet_success: {len(results)} events")
        return results

    except requests.exceptions.Timeout:
        logger.error("eonet_timeout")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"eonet_request_fail: {str(e)[:100]}")
        return []
    except ValueError:
        logger.error("eonet_json_error")
        return []

# --- 6. SPACE DATA ---

def get_nasa_apod(nasa_key: str) -> Dict[str, Any]:
    """
    Get NASA Astronomy Picture of the Day.
    v3.2 FIXES:
    ISSUE: DEMO_KEY hardcoded, bare except, no timeout
    IMPACT: Rate limit 30/hour, crash on API error
    FIX: Require real key, specific exceptions, fallback data
    """
    if not nasa_key or nasa_key == "DEMO_KEY":
        logger.warning("apod_demo_key_used")
        return {
            "title": "Demo Mode",
            "url": "",
            "explanation": "NASA_KEY not configured. Using demo limits.",
            "source": "NASA APOD"
        }

    params = {'api_key': nasa_key}

    try:
        response = requests.get(
            NASA_APOD_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        # v3.2 FIX: Validate response
        return {
            'title': data.get('title', 'Unknown'),
            'url': data.get('url', ''),
            'hdurl': data.get('hdurl', ''),
            'explanation': data.get('explanation', '')[:500], # Truncate
            'date': data.get('date', ''),
            'media_type': data.get('media_type', 'image'),
            'source': 'NASA APOD'
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.error("apod_rate_limit_exceeded")
            return {"error": "rate_limit", "source": "NASA APOD"}
        logger.error(f"apod_http_error: {e.response.status_code}")
        return {"error": "api_error", "source": "NASA APOD"}
    except requests.exceptions.Timeout:
        logger.error("apod_timeout")
        return {"error": "timeout", "source": "NASA APOD"}
    except requests.exceptions.RequestException as e:
        logger.error(f"apod_request_fail: {str(e)[:100]}")
        return {"error": "request_failed", "source": "NASA APOD"}
    except ValueError:
        logger.error("apod_json_error")
        return {"error": "parse_failed", "source": "NASA APOD"}

def get_iss_location() -> Dict[str, Any]:
    """
    Get ISS current location.
    v3.2 FIXES:
    ISSUE: Bare except, no timeout, http not https
    IMPACT: Crash on API down, insecure request
    FIX: Specific exceptions, timeout, validate coords
    """
    try:
        # v3.2 NOTE: open-notify only supports http, but we add timeout
        response = requests.get(
            ISS_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        iss_pos = data.get('iss_position', {})
        lat = iss_pos.get('latitude')
        lon = iss_pos.get('longitude')

        # v3.2 FIX: Validate coordinates
        try:
            lat_f, lon_f = float(lat), float(lon)
            if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                return {
                    'lat': lat_f,
                    'lon': lon_f,
                    'timestamp': data.get('timestamp', 0),
                    'source': 'Open-Notify'
                }
        except (TypeError, ValueError):
            logger.error(f"iss_invalid_coords: {lat}, {lon}")

        return {"error": "invalid_coordinates", "source": "Open-Notify"}

    except requests.exceptions.Timeout:
        logger.error("iss_timeout")
        return {"error": "timeout", "source": "Open-Notify"}
    except requests.exceptions.RequestException as e:
        logger.error(f"iss_request_fail: {str(e)[:100]}")
        return {"error": "request_failed", "source": "Open-Notify"}
    except ValueError:
        logger.error("iss_json_error")
        return {"error": "parse_failed", "source": "Open-Notify"}

# --- 7. UTILITY FUNCTIONS - v3.2: Type hints added ---

def validate_coordinates(lat: Any, lon: Any) -> Tuple[bool, Optional[float], Optional[float]]:
    """
    Validate and convert coordinates.
    v3.2 ADDITION: Centralized validation
    Returns: (is_valid, lat_float, lon_float)
    """
    try:
        lat_f, lon_f = float(lat), float(lon)
        if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
            return True, lat_f, lon_f
        return False, None, None
    except (TypeError, ValueError):
        return False, None, None
