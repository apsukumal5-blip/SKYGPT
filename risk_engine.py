"""
SkyGPT World AI v3.0 - Risk Engines
CREATOR: Saroj Kumal
Handles: Flood, Landslide, Cyclone, Earthquake Risk Logic
"""
def assess_flood_risk(weather_data):
    """FLOOD RISK ENGINE: Low Moderate High Extreme"""
    if 'error' in weather_data: return {"level": "Unknown", "msg": "Weather data unavailable"}
    rain = weather_data['daily']['precipitation_sum'][0]
    if rain > 200: return {"level": "Extreme", "msg": "🔴 Extreme: >200mm forecast. Catastrophic flooding likely. Evacuate immediately."}
    elif rain > 120: return {"level": "High", "msg": "🟠 High: >120mm forecast. Flash flood risk. Move to higher ground."}
    elif rain > 60: return {"level": "Moderate", "msg": "🟡 Moderate: 60-120mm forecast. Urban flooding possible. Stay alert."}
    else: return {"level": "Low", "msg": "🟢 Low: <60mm forecast. No immediate flood risk."}

def assess_landslide_risk(weather_data, location_name):
    """LANDSLIDE ENGINE: Himalayan Region Special Support"""
    if 'error' in weather_data: return {"level": "Unknown", "msg": "Weather data unavailable"}
    rain = weather_data['daily']['precipitation_sum'][0]
    himalayan = ['nepal', 'himal', 'everest', 'annapurna', 'manang', 'mustang', 'lukla', 'pokhara', 'darjeeling', 'sikkim']
    is_mountain = any(k in location_name.lower() for k in himalayan)
    if is_mountain and rain > 150: return {"level": "Extreme", "msg": "🔴 Extreme: >150mm in Himalayan region. Landslide imminent. Avoid all travel."}
    elif is_mountain and rain > 80: return {"level": "High", "msg": "🟠 High: Heavy rain in mountains. Landslide risk. Postpone trekking."}
    elif rain > 50: return {"level": "Moderate", "msg": "🟡 Moderate: Monitor slopes if continuous rain."}
    else: return {"level": "Low", "msg": "🟢 Low: No significant landslide risk."}

def get_earthquake_advice(magnitude):
    if magnitude >= 7.0: return "🚨 Drop, Cover, Hold On. Major quake. Check for tsunami warnings. Evacuate if near coast."
    elif magnitude >= 5.0: return "⚠️ Strong shaking expected. Stay away from windows. Check gas lines after."
    else: return "ℹ️ Minor quake. No damage expected but stay alert for aftershocks."
