"""
SkyGPT World AI v4.1 - Polyglot Brain Module
CREATOR: Saroj Kumal
UPGRADE: Fixed token limit + Multi-word location + Empty data handling
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
    MODEL = genai.GenerativeModel('gemini-2.5-flash')
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
    'mausam', 'din', 'raat', 'sahar', 'bazar', 'ma', 'ko', 'ka', 'le', 'bata', 'dekhi', 'kati'
}

ROMANIZED_HINDI_KEYWORDS = {
    'hai', 'hoga', 'hogi', 'barish', 'kal', 'aaj', 'mausam', 'dilli', 'mumbai', 'kya',
    'kaisa', 'kaisi', 'mein', 'me', 'ka', 'ki', 'ke', 'se', 'tak', 'hawa', 'garmi'
}

# --- 3. LOCATION DICTIONARY FOR FAST MATCH ---
LOCATION_DICT = {
    # Nepal
    'kathmandu', 'pokhara', 'lalitpur', 'bhaktapur', 'dhulikhel', 'chitwan', 'meghauli',
    'butwal', 'dharan', 'biratnagar', 'nepal', 'everest', 'annapurna', 'lumbini', 'nagarkot',
    'chitwan meghauli', 'sauraha', 'bharatpur',
    # India
    'delhi', 'mumbai', 'bangalore', 'kolkata', 'chennai', 'hyderabad', 'dilli', 'bombay',
    # Global
    'tokyo', 'london', 'paris', 'new york', 'dubai', 'singapore', 'sydney', 'beijing'
}

# --- 4. LANGUAGE DETECTION v4.1 ---
@lru_cache(maxsize=128)
def detect_user_language(text):
    """v4.1: langdetect + custom dictionary + fallback. Handles Romanized Nepali/Hindi."""
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    # Rule 1: Check Romanized Nepali
    if len(words.intersection(ROMANIZED_NEPALI_KEYWORDS)) >= 2:
        return 'ne'
    if any(word in ROMANIZED_NEPALI_KEYWORDS for word in ['cha', 'xa', 'pani', 'kasto', 'kati']):
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

# --- 5. LOCATION EXTRACTION v4.1 ---
@lru_cache(maxsize=256)
def extract_location(text, lang_code):
    """v4.1: Regex + Dictionary + Multi-word + Gemini Fallback. Never truncates."""
    text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text_clean.split()

    # Step 1: Check 3-word locations first: "everest base camp"
    for i in range(len(words) - 2):
        three_word = f"{words[i]} {words[i+1]} {words[i+2]}"
        if three_word in LOCATION_DICT:
            return three_word.title()

    # Step 2: Check 2-word locations: "chitwan meghauli", "new york"
    for i in range(len(words) - 1):
        two_word = f"{words[i]} {words[i+1]}"
        if two_word in LOCATION_DICT:
            return two_word.title()

    # Step 3: Check single words
    for word in words:
        if word in LOCATION_DICT:
            return word.title()

    # Step 4: Regex for Capitalized words in original text
    capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
    if capitalized:
        stopwords = {'Weather', 'Rain', 'Today', 'Tomorrow', 'Will', 'Is', 'The', 'Ko', 'Ma', 'Kati'}
        candidates = [w for w in capitalized if w not in stopwords]
        if candidates:
            return ' '.join(candidates[:2]).title() # Take max 2 words

    # Step 5: Gemini Fallback
    if not MODEL:
        return None

    lang_name = LANGUAGE_MAP.get(lang_code, 'English')
    prompt = f"""Extract ONLY the primary location from this query. Can be 1-3 words. Never truncate.
    Rules: 1. "Chitwan meghauli maa" -> Chitwan Meghauli 2. "Kathmandu dhulikhel" -> Kathmandu 3. No fillers.
    Query: "{text}"
    Location:"""
    try:
        response = MODEL.generate_content(prompt, generation_config={"max_output_tokens": 15, "temperature": 0})
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

# --- 7. MASTER AI RESPONSE v4.1 ---
def get_ai_response(user_prompt, context_data, chat_history):
    """MASTER BRAIN v4.1: Fixed truncation + Multi-word location"""
    if not MODEL:
        return "🧠 AI Brain offline. Check GEMINI_KEY in Secrets."

    lang_code = detect_user_language(user_prompt)
    lang_name = LANGUAGE_MAP.get(lang_code, 'English')
    memory_context = build_memory_context(chat_history)

    # Handle follow-up queries
    if user_prompt.lower().strip() in ['tomorrow?', 'bholi?', 'voli?', 'kal?', 'भोलि?', 'कल?']:
        if "last_location" in memory_context:
            user_prompt = f"Weather tomorrow in {memory_context['last_location']}"
        else:
            return "📍 Location chaina. Kripaya sahar ko naam lekhnus."

    # Check if context is empty - v4.1 FIX
    if not context_data or all(v is None for v in context_data.values()):
        if lang_code == 'ne':
            return f"⚠️ Maaf garnus, tyo thau ko data bhayena. Sahar ko naam check garnus."
        return f"⚠️ Sorry, no data found for that location. Check spelling."

    memory = chat_history[-6:] if len(chat_history) > 6 else chat_history

    system_prompt = f"""
    You are SkyGPT World AI v4.1, created by Saroj Kumal. You are a native {lang_name} speaker.
    CRITICAL RULES v4.1:
    1. LANGUAGE: User wrote in {lang_name}. Reply ONLY in {lang_name}. Use Devanagari for Nepali.
    2. ROMANIZED SUPPORT: If user writes "kasto xa", reply "kasto cha" style. Match their tone.
    3. USE DATA: Base answer ONLY on this JSON: {json.dumps(context_data, default=str, ensure_ascii=False)}
    4. IF DATA MISSING: Say "Data bhayena" in {lang_name}. Never invent.
    5. CONCISE: 2-3 lines max. Start with 🟢🟡🟠🔴 based on risk.
    6. COMPLETE ANSWER: Never stop mid-sentence. Always finish the thought.
    7. MULTI-WORD: "Chitwan Meghauli" is one place. Keep it together.
    8. MEMORY: Last location: {memory_context.get('last_location', 'None')}
    CONTEXT: {json.dumps(context_data, default=str, ensure_ascii=False)}
    HISTORY: {json.dumps(memory, default=str, ensure_ascii=False)}
    """

    try:
        response = MODEL.generate_content(
            system_prompt + f"\n\nUSER WRITING IN {lang_name}: {user_prompt}",
            generation_config={"max_output_tokens": 500, "temperature": 0.2} # v4.1: 500 tokens
        )
        return response.text.strip()
    except Exception as e:
        error_msg = str(e)[:100]
        if '404' in error_msg:
            return f"🧠 Brain Error: Model not found. Check model name."
        return f"🧠 Brain Error: {error_msg}"

# --- 8. BACKWARD COMPATIBILITY ---
def get_ai_response_multilingual(user_prompt, context_data, chat_history):
    """Wrapper for backward compatibility with app.py"""
    return get_ai_response(user_prompt, context_data, chat_history)

def extract_location_multilingual(text, lang_code):
    """Wrapper for backward compatibility"""
    return extract_location(text, lang_code)
