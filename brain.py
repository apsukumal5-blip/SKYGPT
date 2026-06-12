"""
SkyGPT World AI v3.1 - Polyglot Brain Module
CREATOR: Saroj Kumal
UPGRADE: 33+ Language Support + Auto Detection + Memory
"""
import streamlit as st
import google.generativeai as genai
import json
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

GEMINI_KEY = st.secrets.get("GEMINI_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    MODEL = genai.GenerativeModel('gemini-1.5-flash')
else:
    MODEL = None

# --- 1. LANGUAGE INTELLIGENCE ---
LANGUAGE_MAP = {
    'en': 'English', 'es': 'Spanish', 'hi': 'Hindi', 'ar': 'Arabic', 'bn': 'Bengali',
    'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese', 'de': 'German', 'fr': 'French',
    'zh-cn': 'Simplified Chinese', 'zh-tw': 'Traditional Chinese', 'ne': 'Nepali', 'ur': 'Urdu',
    'tr': 'Turkish', 'ko': 'Korean', 'it': 'Italian', 'id': 'Indonesian', 'vi': 'Vietnamese',
    'th': 'Thai', 'fa': 'Persian', 'pl': 'Polish', 'nl': 'Dutch', 'si': 'Sinhala',
    'my': 'Burmese', 'ms': 'Malay', 'sw': 'Swahili', 'el': 'Greek', 'cs': 'Czech',
    'ro': 'Romanian', 'hu': 'Hungarian', 'fi': 'Finnish', 'sv': 'Swedish',
    'no': 'Norwegian', 'da': 'Danish'
}

def detect_user_language(text):
    """Auto-detect user language. Supports 33+ languages."""
    try:
        lang_code = detect(text)
        if lang_code == 'zh-cn' or lang_code == 'zh': return 'zh-cn'
        if lang_code == 'zh-tw': return 'zh-tw'
        return lang_code if lang_code in LANGUAGE_MAP else 'en'
    except:
        return 'en'

def extract_location_multilingual(text, lang_code):
    """NLP Location Extraction that understands local names"""
    if not MODEL: return None
    lang_name = LANGUAGE_MAP.get(lang_code, 'English')

    prompt = f"""You are a global location expert. Extract the specific location from this query in {lang_name}.
    Understand villages, wards, mountains, rivers, airports in local language.
    Return ONLY location name. If "my village/city" or no location, return "None".

    Examples:
    Nepali "पोखरामा भोलि पानी पर्छ?" -> Pokhara
    Hindi "दिल्ली में बारिश होगी क्या?" -> Delhi
    Spanish "¿Lloverá mañana en Madrid?" -> Madrid
    Japanese "東京の天気は？" -> Tokyo
    Arabic "هل ستمطر في دبي؟" -> Dubai
    Nepali "एभरेस्ट बेस क्याम्पको मौसम" -> Everest Base Camp
    Nepali "वार्ड ५ डल्ली राजहरा" -> Dalli Rajhara, Ward 5

    Query: "{text}"
    Location:"""
    try:
        response = MODEL.generate_content(prompt, generation_config={"max_output_tokens": 30})
        loc = response.text.strip().replace('"', '')
        return None if loc.lower() in ["none", ""] else loc
    except: return None

def get_ai_response_multilingual(user_prompt, context_data, chat_history):
    """MASTER BRAIN: Memory + Multilingual + Translation"""
    if not MODEL: return "🧠 AI Brain offline. Check GEMINI_KEY in Secrets."

    lang_code = detect_user_language(user_prompt)
    lang_name = LANGUAGE_MAP.get(lang_code, 'English')
    memory = chat_history[-8:] if len(chat_history) > 8 else chat_history

    system_prompt = f"""
    You are SkyGPT World AI v3.1, created by Saroj Kumal. You are a native {lang_name} speaker.

    CRITICAL MULTILINGUAL RULES:
    1. DETECT & RESPOND: User is writing in {lang_name}. You MUST reply in {lang_name}.
    2. NEVER INVENT DATA: Use ONLY this context: {json.dumps(context_data, default=str, ensure_ascii=False)}
    3. TRANSLATE EXPLANATIONS ONLY: Keep technical values unchanged. Example:
       If context has "Temperature: 28°C Wind: 15 km/h", keep "28°C" and "15 km/h" as-is.
       But explain in {lang_name}: "तापक्रम २८°C छ" or "温度は28°Cです"
    4. LOCAL PLACE NAMES: Understand and use local names. If location is "पोखरा", use पोखरा not Pokhara.
    5. MEMORY: Remember location from history. If user says "भोलि?" after "Kathmandu weather", answer for Kathmandu.
    6. SAFETY FIRST: For High/Extreme risks, start with ⚠️ in {lang_name}.
    7. BE CONCISE: 3-4 lines max. Use native emojis: 🟢🟡🟠🔴
    8. UNICODE: Use proper {lang_name} script. Devanagari for Nepali/Hindi, Arabic script, Kanji, etc.

    CONTEXT DATA: {json.dumps(context_data, default=str, ensure_ascii=False)}
    CONVERSATION HISTORY: {json.dumps(memory, default=str, ensure_ascii=False)}
    """

    try:
        response = MODEL.generate_content(system_prompt + f"\n\nUSER WRITING IN {lang_name}: {user_prompt}",
                                        generation_config={"max_output_tokens": 400})
        return response.text
    except Exception as e:
        return f"🧠 Brain Error: {str(e)[:100]}"
