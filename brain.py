"""
SkyGPT World AI v4.0 - Polyglot Brain Module
CREATOR: Saroj Kumal
UPGRADE: Romanized Nepali/Hindi + Regex Extractor + Memory + Cache + 33 Languages
"""
import streamlit as st
import google.generativeai as genai
import json
import re
from langdetect import detect, DetectorFactory
from functools import lru_cache
DetectorFactory.seed = 0

# --- 1. CONFIG ---
GEMINI_KEY = st.secrets.get("GEMINI_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    MODEL = genai.GenerativeModel('gemini-2.5-flash') # Updated 2026 model
else:
    MODEL = None

# --- 2. LANGUAGE MAP + KEYWORDS ---
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

ROMANIZED_NEPALI_KEYWORDS = {
    'cha', 'xa', 'xaina', 'pani', 'parcha', 'parxa', 'aaja', 'voli', 'bholi', 'kathmandu',
    'pokhara', 'gaun', 'hawa', 'kasto', 'huncha', 'hola', 'tapai', 'timi', 'hamro', 'mero',
    'mausam', 'din', 'raat', 'sahar', 'bazar', 'ma', 'ko', 'ka', 'le', 'bata', 'dekhi'
}

ROMANIZED_HINDI_KEYWORDS = {
    'hai', 'hoga', 'hogi', 'barish', 'kal', 'aaj', 'mausam', 'dilli', 'mumbai', 'kya',
    'kaisa', 'kaisi', 'mein', 'me', 'ka', 'ki', 'ke', 'se', 'tak', 'hawa', 'garmi'
}

# --- 3. LOCATION DICTIONARY FOR FAST MATCH ---
LOCATION_DICT = {
    # Nepal
    'kathmandu', 'pokhara', 'lalitpur', 'bhaktapur', 'dhulikhel', 'chitwan', 'butwal',
    'dharan', 'biratnagar', 'nepal', 'everest', 'annapurna', 'lumbini', 'nagarkot',
    # India
    'delhi', 'mumbai', 'bangalore', 'kolkata', 'chennai', 'hyderabad', 'dilli', 'bombay',
    # Global
    'tokyo', 'london', 'paris', 'new york', 'dubai', 'singapore', 'sydney', 'beijing'
}

# --- 4. LANGUAGE DETECTION v4.0 ---
@lru_cache(maxsize=128)
def detect_user_language(text):
    """v4.0: langdetect + custom dictionary + fallback. Handles Romanized Nepali/Hindi."""
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    # Rule 1: Check Romanized Nepali
    if len(words.intersection(ROMANIZED_NEPALI_KEYWORDS)) >= 2:
        return 'ne'
    if any(word in ROMANIZED_NEPALI_KEYWORDS for word in ['cha', 'xa', 'pani', 'kasto']):
        return 'ne'

    # Rule 2: Check Romanized Hindi
    if len(words.intersection(ROMANIZED_HINDI_KEYWORDS)) >= 2:
        return 'hi'
    if any(word in ROMANIZED_HINDI_KEYWORDS for word in ['hai', 'hoga', 'barish', 'kya']):
        return 'hi'

    # Rule 3: Use langdetect for native scripts
    try:
        lang_code = detect(text)
        if lang_code == 'zh-cn' or lang_code == 'zh':
            return 'zh-cn'
        if lang_code == 'zh-tw':
            return 'zh-tw'
        return lang_code if lang_code in LANGUAGE_MAP else 'en'
    except:
        return 'en'

# --- 5. LOCATION EXTRACTION v4.0 ---
@lru_cache(maxsize=256)
def extract_location(text, lang_code):
    """v4.0: Regex + Dictionary + Gemini Fallback. Never truncates names."""

    # Step 1: Regex - Extract capitalized words + known locations
    text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text_clean.split()

    # Find known locations from dictionary first
    for word in words:
        if word in LOCATION_DICT:
            return word.title()

    # Find multi-word locations: "New York", "Everest Base Camp"
    for i in range(len(words) - 1):
        two_word = f"{words[i]} {words[i+1]}"
        if two_word in LOCATION_DICT:
            return two_word.title()

    # Step 2: Regex for Capitalized words in original text
    capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
    if capitalized:
        # Filter out common words
        stopwords = {'Weather', 'Rain', 'Today', 'Tomorrow', 'Will', 'Is', 'The', 'Ko', 'Ma'}
        candidates = [w for w in capitalized if w not in stopwords]
        if candidates:
            return candidates[0] # Return first valid location

    # Step 3: Gemini Fallback for complex cases
    if not MODEL:
        return None

    lang_name = LANGUAGE_MAP.get(lang_code, 'English')
    prompt = f"""Extract ONLY the primary city/country name from this query. Never truncate.
    Rules: 1. "Kathmandu dhulikhel" -> Kathmandu 2. "Nepal KO weather" -> Nepal 3. No fillers.
    Query: "{text}"
    Location:"""
    try:
        response = MODEL.generate_content(prompt, generation_config={"max_output_tokens": 10, "temperature": 0})
        loc = response.text.strip().replace('"', '').replace('.', '').replace(',', '')
        return None if loc.lower() in ["none", ""] else loc.title()
    except:
        return None

# --- 6. MEMORY CONTEXT BUILDER ---
def build_memory_context(chat_history):
    """Extracts last location and intent from last 4 messages for follow-ups."""
    if not chat_history or len(chat_history) < 2:
        return {}

    memory = {}
    # Check last 4 messages for location
    for msg in reversed(chat_history[-4:]):
        if msg["role"] == "assistant" and "location" in msg.get("context", {}):
            memory["last_location"] = msg["context"]["location"]["display"]
            break
        if msg["role"] == "user":
            loc = extract_location(msg["content"], detect_user_language(msg["content"]))
            if loc:
                memory["last_location"] = loc
                break
    return memory

# --- 7. MASTER AI RESPONSE v4.0 ---
def get_ai_response(user_prompt, context_data, chat_history):
    """MASTER BRAIN v4.0: Multilingual + Memory + Romanized Support"""
    if not MODEL:
        return "🧠 AI Brain offline. Check GEMINI_KEY in Secrets."

    lang_code = detect_user_language(user_prompt)
    lang_name = LANGUAGE_MAP.get(lang_code, 'English')
    memory_context = build_memory_context(chat_history)

    # Handle follow-up queries like "tomorrow?" "bholi?"
    if user_prompt.lower().strip() in ['tomorrow?', 'bholi?', 'voli?', 'kal?', 'भोलि?', 'कल?']:
        if "last_location" in memory_context:
            user_prompt = f"Weather tomorrow in {memory_context['last_location']}"
        else:
            return get_ai_response_multilingual("Ask user for location for tomorrow forecast", {"error": "no_location"}, chat_history)

    # Truncate history for performance
    memory = chat_history[-6:] if len(chat_history) > 6 else chat_history

    system_prompt = f"""
    You are SkyGPT World AI v4.0, created by Saroj Kumal. You are a native {lang_name} speaker.
    CRITICAL RULES v4.0:
    1. LANGUAGE: User wrote in {lang_name}. Reply ONLY in {lang_name}. Match script: Devanagari for Nepali, Arabic for Arabic.
    2. ROMANIZED SUPPORT: If user writes "kasto xa", reply "kasto cha". If "kya hoga", reply "hoga".
    3. NEVER INVENT DATA: Use ONLY this JSON context: {json.dumps(context_data, default=str, ensure_ascii=False)}
    4. MEMORY: Last known location: {memory_context.get('last_location', 'None')}. Use it for follow-ups.
    5. CONCISE: 3-4 lines max. Start with location emoji + status: 🟢🟡🟠🔴
    6. SAFETY: For High/Extreme risk, start with ⚠️ in {lang_name}.
    7. NO TRANSLATION: Keep "28°C", "15 km/h", "5.2 magnitude" as-is. Only translate explanations.
    8. LOCATION NAMES: Use local names. "काठमाडौं" not "Kathmandu" if user wrote Nepali.
    CONTEXT: {json.dumps(context_data, default=str, ensure_ascii=False)}
    HISTORY: {json.dumps(memory, default=str, ensure_ascii=False)}
    """

    try:
        response = MODEL.generate_content(
            system_prompt + f"\n\nUSER WRITING IN {lang_name}: {user_prompt}",
            generation_config={"max_output_tokens": 300, "temperature": 0.3}
        )
        return response.text
    except Exception as e:
        error_msg = str(e)[:100]
        if '404' in error_msg:
            return f"🧠 Brain Error: Model not found. Check model name in brain.py"
        return f"🧠 Brain Error: {error_msg}"

# --- 8. BACKWARD COMPATIBILITY ---
def get_ai_response_multilingual(user_prompt, context_data, chat_history):
    """Wrapper for backward compatibility with app.py"""
    return get_ai_response(user_prompt, context_data, chat_history)
