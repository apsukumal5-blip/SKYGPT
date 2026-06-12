"""
PROJECT: SkyGPT World AI - Risk Engines v3.2.1
CREATOR: Saroj Kumal
STATUS: Production Stable - June 28/29 Launch
PYTHON: 3.11+ Compatible | Streamlit Cloud Compatible
FIXES: v3.2.1 - Removed rain_prob fallback, locked wind units to km/h
"""
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

# v3.2.1: Constants for thresholds - prevents magic numbers
FLOOD_THRESHOLDS = {
    "extreme": 200, # mm
    "high": 120, # mm
    "moderate": 60 # mm
}

LANDSLIDE_THRESHOLDS = {
    "extreme_himalayan": 150, # mm
    "high_himalayan": 80, # mm
    "moderate_general": 50 # mm
}

HIMALAYAN_REGIONS = {
    'nepal', 'himal', 'everest', 'annapurna', 'manang', 'mustang',
    'lukla', 'pokhara', 'darjeeling', 'sikkim', 'bhutan', 'tibet',
    'leh', 'ladakh', 'himachal', 'uttarakhand'
}

# v3.2.1: Standardized return schema
def _safe_risk_response(
    level: str = "Unknown",
    msg: str = "Risk assessment unavailable",
    score: int = 0
) -> Dict[str, Any]:
    """Standardized safe response. Never crashes."""
    return {
        "level": level,
        "msg": msg,
        "score": score,
        "source": "RiskEngine v3.2.1"
    }

def _get_daily_rain(weather_data: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    v3.2.1 FIX: C1 - REMOVED rain_prob fallback
    Scientific reason: rain_prob is percentage (0-100%), not mm.
    Comparing 80% > 200mm is invalid and dangerous.
    """
    if not isinstance(weather_data, dict):
        return None

    # v3.2.1: Handle error state from data_sources
    if weather_data.get('error'):
        logger.warning(f"weather_data_error: {weather_data.get('error')}")
        return None

    # v3.2.1: Only use actual rainfall amount in mm
    rain = weather_data.get('daily_rain_max')

    # v3.2.1 FIX: NO FALLBACK TO PROBABILITY - return None if mm unavailable
    # Old dangerous code removed:
    # if rain is None:
    # rain = weather_data.get('rain_prob') # THIS WAS WRONG

    try:
        return float(rain) if rain is not None else None
    except (TypeError, ValueError):
        logger.warning(f"invalid_rain_value: {rain}")
        return None

def assess_flood_risk(weather_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    FLOOD RISK ENGINE: Low Moderate High Extreme
    v3.2.1 FIXES:
    1. C1: No rain_prob fallback - returns Unknown if mm unavailable
    2. Scientific validity: Only uses actual mm values
    """
    rain = _get_daily_rain(weather_data)

    # v3.2.1: Graceful degradation - scientifically accurate
    if rain is None:
        return _safe_risk_response(
            level="Unknown",
            msg="⚪ Rainfall amount (mm) unavailable. Cannot assess flood risk. Check official meteorological forecasts for precipitation totals.",
            score=0
        )

    # v3.2.1: Explicit thresholds with scores for agent voting
    if rain > FLOOD_THRESHOLDS["extreme"]:
        return _safe_risk_response(
            level="Extreme",
            msg=f"🔴 Extreme: {rain:.0f}mm forecast. Catastrophic flooding likely. Evacuate immediately if advised by authorities.",
            score=90
        )
    elif rain > FLOOD_THRESHOLDS["high"]:
        return _safe_risk_response(
            level="High",
            msg=f"🟠 High: {rain:.0f}mm forecast. Flash flood risk. Move to higher ground and avoid rivers/streams.",
            score=70
        )
    elif rain > FLOOD_THRESHOLDS["moderate"]:
        return _safe_risk_response(
            level="Moderate",
            msg=f"🟡 Moderate: {rain:.0f}mm forecast. Urban flooding possible. Stay alert to official advisories.",
            score=40
        )
    else:
        return _safe_risk_response(
            level="Low",
            msg=f"🟢 Low: {rain:.0f}mm forecast. No immediate flood risk expected.",
            score=10
        )

def assess_landslide_risk(
    weather_data: Optional[Dict[str, Any]],
    location_name: Optional[str]
) -> Dict[str, Any]:
    """
    LANDSLIDE ENGINE: Himalayan Region Special Support
    v3.2.1 FIXES:
    1. Uses _get_daily_rain with C1 fix applied
    2. None-safety: location_name can be None
    """
    rain = _get_daily_rain(weather_data)

    if rain is None:
        return _safe_risk_response(
            level="Unknown",
            msg="⚪ Rainfall amount (mm) unavailable. Cannot assess landslide risk.",
            score=0
        )

    # v3.2.1 FIX: location_name None-safety
    is_mountain = False
    if isinstance(location_name, str) and location_name:
        try:
            loc_lower = location_name.lower()
            is_mountain = any(region in loc_lower for region in HIMALAYAN_REGIONS)
        except (AttributeError, TypeError):
            logger.warning(f"invalid_location_name_type: {type(location_name)}")
            is_mountain = False

    # v3.2.1: Himalayan special logic with scores
    if is_mountain and rain > LANDSLIDE_THRESHOLDS["extreme_himalayan"]:
        return _safe_risk_response(
            level="Extreme",
            msg=f"🔴 Extreme: {rain:.0f}mm in Himalayan region. Landslide imminent. Avoid all travel and evacuate unstable slopes immediately.",
            score=95
        )
    elif is_mountain and rain > LANDSLIDE_THRESHOLDS["high_himalayan"]:
        return _safe_risk_response(
            level="High",
            msg=f"🟠 High: {rain:.0f}mm in mountains. Landslide risk elevated. Postpone trekking and avoid steep slopes/ravines.",
            score=75
        )
    elif rain > LANDSLIDE_THRESHOLDS["moderate_general"]:
        return _safe_risk_response(
            level="Moderate",
            msg=f"🟡 Moderate: {rain:.0f}mm forecast. Monitor slopes if continuous rain persists. Be cautious near hillsides.",
            score=45
        )
    else:
        return _safe_risk_response(
            level="Low",
            msg=f"🟢 Low: {rain:.0f}mm forecast. No significant landslide risk based on current rainfall.",
            score=15
        )

def get_earthquake_advice(magnitude: Optional[Union[float, int, str]]) -> str:
    """
    EARTHQUAKE ADVICE ENGINE
    v3.2.1: No changes needed - already safe
    """
    try:
        if magnitude is None:
            return "ℹ️ Earthquake magnitude data unavailable. Follow standard safety protocols if shaking occurs."

        mag_f = float(magnitude)
    except (TypeError, ValueError):
        logger.warning(f"invalid_magnitude_type: {type(magnitude)}, value: {magnitude}")
        return "ℹ️ Invalid earthquake data received. If you felt shaking: Drop, Cover, Hold On."

    if mag_f >= 7.0:
        return "🚨 Drop, Cover, Hold On. Major quake detected. Check for tsunami warnings if coastal. Evacuate if instructed by authorities."
    elif mag_f >= 5.0:
        return "⚠️ Strong shaking possible. Stay away from windows and heavy objects. Check gas/water lines after shaking stops."
    elif mag_f >= 3.0:
        return "ℹ️ Minor to light quake. No damage expected but stay alert for aftershocks."
    else:
        return "ℹ️ Micro earthquake detected. Typically not felt. No action needed."

def assess_cyclone_risk(weather_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    CYCLONE ENGINE: v3.2.1
    v3.2.1 FIX: C2 - Explicit unit handling and validation
    Assumes wind_speed_10m from data_sources is in km/h
    """
    if not isinstance(weather_data, dict) or weather_data.get('error'):
        return _safe_risk_response(
            level="Unknown",
            msg="⚪ Wind data unavailable. Cannot assess cyclone risk. Check official meteorological services.",
            score=0
        )

    wind = weather_data.get('wind')
    try:
        wind_f = float(wind) if wind is not None else 0.0
    except (TypeError, ValueError):
        logger.error(f"invalid_wind_value: {wind}")
        return _safe_risk_response(
            level="Unknown",
            msg="⚪ Invalid wind data received. Cannot assess cyclone risk.",
            score=0
        )

    # v3.2.1 FIX: C2 - Explicit unit check and logging
    # Open-Meteo returns km/h by default. Log warning if suspicious values
    if wind_f > 300: # 300 km/h = 186 mph, unrealistic sustained wind
        logger.error(f"suspicious_wind_speed: {wind_f} - possible unit error")
        return _safe_risk_response(
            level="Unknown",
            msg="⚪ Wind speed data anomaly detected. Check official weather services.",
            score=0
        )

    # v3.2.1: Thresholds in km/h (sustained wind speed)
    if wind_f > 120:
        return _safe_risk_response(
            level="Extreme",
            msg=f"🔴 Extreme: Cyclonic winds {wind_f:.0f} km/h (sustained). Severe damage likely. Shelter immediately in reinforced structure.",
            score=95
        )
    elif wind_f > 80:
        return _safe_risk_response(
            level="High",
            msg=f"🟠 High: Strong winds {wind_f:.0f} km/h (sustained). Secure loose objects. Avoid all travel.",
            score=70
        )
    elif wind_f > 50:
        return _safe_risk_response(
            level="Moderate",
            msg=f"🟡 Moderate: Gusty winds {wind_f:.0f} km/h (sustained). Caution advised outdoors. Secure light objects.",
            score=40
        )
    else:
        return _safe_risk_response(
            level="Low",
            msg=f"🟢 Low: Wind speed {wind_f:.0f} km/h (sustained). Normal conditions.",
            score=10
)
