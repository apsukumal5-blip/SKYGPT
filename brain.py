"""
SkyGPT World AI v3.0 - Gemini Brain
CREATOR: Saroj Kumal
Handles: System Prompts, Memory, Multilingual, Context
"""
import streamlit as st
import google.generativeai as genai
import json

GEMINI_KEY = st.secrets.get("GEMINI_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    MODEL = genai.GenerativeModel('gemini-1.5-flash')
else:
    MODEL = None

def detect_language(text):
    """Simple lang detect: Nepali, Hindi, English"""
    if any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text):
        if any(word in text for word in ['छ', 'हो', 'छैन']): return "ne"
        return "hi"
    return "en"

def extract_location_with_gemini(text):
    """NLP Location Extraction for global places"""
    if not MODEL: return None
    prompt = f"""Extract the specific location from this query. Return ONLY location name.
    If "my village/city" or no location, return "None".
    Examples: "Rain in Tokyo?" -> Tokyo | "Everest Base Camp weather" -> Everest Base Camp
    Query: "{text}" | Location:"""
    try:
        response = MODEL.generate_content(prompt, generation_config={"max_output_tokens": 25})
        loc = response.text.strip().replace('"', '')
        return None if loc.lower() in ["none", ""] else loc
    except: return None

def get_ai_response(user_prompt, context_data, chat_history):
    """MASTER BRAIN: Memory + Multilingual + Context"""
    if not MODEL: return "🧠 AI Brain offline. Check GEMINI_KEY in Secrets."

    lang = detect_language(user_prompt)
    memory = chat_history[-8:] if len(chat_history) > 8 else chat_history

    system_prompt = f"""
    You are SkyGPT World AI v3.0, created by Saroj Kumal. Global Earth Intelligence Assistant.

    CRITICAL RULES:
    1. NEVER INVENT LIVE DATA. Use ONLY context: {json.dumps(context_data, default=str)}
    2. RESPOND IN USER'S LANGUAGE: {lang}. English=en, Nepali=ne, Hindi=hi.
    3. BE CONCISE: 3-4 lines max unless detailed answer requested.
    4. SAFETY FIRST: For High/Extreme risks, start with ⚠️ and give clear action.
    5. USE EMOJIS: 🟢🟡🟠🔴 for risk, ✅ for safe, 🌡️ for temp, 💨 for wind.
    6. FOLLOW-UP: Remember location from history. If user says "what about tomorrow", use last location.
    7. UNCERTAINTY: Say "Data anusar..." if incomplete.

    CONTEXT: {json.dumps(context_data, default=str)}
    HISTORY: {json.dumps(memory, default=str)}
    """

    try:
        response = MODEL.generate_content(system_prompt + f"\n\nUSER: {user_prompt}",
                                        generation_config={"max_output_tokens": 350})
        return response.text
    except Exception as e:
        return f"🧠 Brain Error: {str(e)[:100]}"
