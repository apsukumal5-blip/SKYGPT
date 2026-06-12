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
    MODEL = genai.GenerativeModel('gemini-2.5-flash')
else:
    MODEL = None

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
        if lang_code == 'zh-cn' or lang_code == 'zh':
            return 'zh-cn'
        if lang_code == 'zh-tw':
            return 'zh-tw'
        return lang_code if lang_code in LANGUAGE_MAP else 'en'
    except:
        return 'en'

def extract_location_multilingual(text, lang_code):
    """NLP Location Extraction v3.2 - Handles Romanized + Mixed Language"""
    if not MODEL:
        return None
    lang_name = LANGUAGE_MAP.get(lang_code, 'English')
    prompt = f"""You are an expert in extracting locations from mixed language queries. 
    User language: {lang_name}
    TASK: Extract ONLY the location name. Remove all question words, weather words, time words.
    CRITICAL RULES:
    1. Romanized Nepali/Hindi: "Kathmandu KO voli" -> Kathmandu
    2. Remove: ma, ko, ka, ko, le, bata, dekhi, samma, kasto, cha, xa, huncha, hola, will, is, the, weather, rain, tomorrow, today
    3. Keep: Everest Base Camp, Ward 5 Dalli Rajhara, New York, Tokyo
    4. If no location: return "None"
    Examples:
    "Kathmandu KO voli KO weather kasto xa" -> Kathmandu
    "Pokhara ma paani parcha?" -> Pokhara
    "भोलि पोखरा कस्तो छ" -> Pokhara
    Query: "{text}"
    Location:"""
    try:
        response = MODEL.generate_content(prompt, generation_config={"max_output_tokens": 25, "temperature": 0})
        loc = response.text.strip().replace('"', '').replace('.', '')
        return None if loc.lower() in ["none", ""] else loc
    except:
        return None

def get_ai_response_multilingual(user_prompt, context_data, chat_history):
    """MASTER BRAIN: Memory + Multilingual + Translation"""
    if not MODEL:
        return "🧠 AI Brain offline. Check GEMINI_KEY in Secrets."
    
    lang_code = detect_user_language(user_prompt)
    lang_name = LANGUAGE_MAP.get(lang_code, 'English')
    memory = chat_history[-8:] if len(chat_history) > 8 else chat_history
    
    system_prompt = f"""
    You are SkyGPT World AI v3.1, created by Saroj Kumal. You are a native {lang_name} speaker.
    CRITICAL MULTILINGUAL RULES:
    1. DETECT & RESPOND: User is writing in {lang_name}. You MUST reply in {lang_name}.
    2. NEVER INVENT DATA: Use ONLY this context: {json.dumps(context_data, default=str, ensure_ascii=False)}
    3. TRANSLATE EXPLANATIONS ONLY: Keep technical values unchanged.
    4. LOCAL PLACE NAMES: Use local names.
    5. MEMORY: Remember location from history.
    6. SAFETY FIRST: For High/Extreme risks, start with ⚠️ in {lang_name}.
    7. BE CONCISE: 3-4 lines max. Use native emojis: 🟢🟡🟠🔴
    8. UNICODE: Use proper {lang_name} script.
    CONTEXT DATA: {json.dumps(context_data, default=str, ensure_ascii=False)}
    CONVERSATION HISTORY: {json.dumps(memory, default=str, ensure_ascii=False)}
    """
    
    try:
        response = MODEL.generate_content(system_prompt + f"\n\nUSER WRITING IN {lang_name}: {user_prompt}",
                                        generation_config={"max_output_tokens": 400})
        return response.text
    except Exception as e:
        return f"🧠 Brain Error: {str(e)[:100]}"
