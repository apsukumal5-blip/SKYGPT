"""
SkyGPT World AI - Gemini Brain Module
CREATOR: Saroj Kumal
Handles: System Prompts, Memory, Multilingual
"""
import streamlit as st
import google.generativeai as genai
import json

# --- 1. SECURITY: GEMINI SETUP ---
GEMINI_KEY = st.secrets.get("GEMINI_KEY")
if not GEMINI_KEY:
    st.error("⚠️ GEMINI_KEY missing in Streamlit Secrets")
    st.stop()

genai.configure(api_key=GEMINI_KEY)
MODEL = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. GEMINI BRAIN: MEMORY + MULTILINGUAL ---
def get_skygpt_response(user_prompt, context_data, chat_history):
    """Core Brain with Conversation Memory + System/User Separation"""

    # Limit chat history to last 6 messages = 3 turns to save tokens
    memory = chat_history[-6:] if len(chat_history) > 6 else chat_history

    system_prompt = f"""
    You are SkyGPT World AI, created by Saroj Kumal. You are a professional Earth Intelligence Assistant.

    CRITICAL RULES:
    1. NEVER INVENT LIVE DATA. Use ONLY this context: {json.dumps(context_data)}
    2. RESPOND IN USER'S LANGUAGE: English, Nepali, Hindi. Detect from user prompt.
    3. BE CONCISE: 2-3 lines max unless asked for detail.
    4. SAFETY FIRST: For High/Extreme risks, start with ⚠️ and give clear action.
    5. UNCERTAINTY: If data missing, say "Data anusar..." or "Available data shows..."
    6. PROFESSIONAL: Use ✅ ❌ 🟢 🟡 🟠 🔴 emojis for clarity.
    7. NO KATHMANDU ASSUMPTION: If location unknown, data will say so.

    CONTEXT DATA FOR THIS QUERY: {json.dumps(context_data, ensure_ascii=False)}
    CONVERSATION HISTORY: {json.dumps(memory, ensure_ascii=False)}
    """

    try:
        # Separate system and user prompt for better control
        full_prompt = f"{system_prompt}\n\nUSER QUESTION: {user_prompt}"
        response = MODEL.generate_content(full_prompt, generation_config={"max_output_tokens": 300})
        return response.text
    except Exception as e:
        return f"🧠 AI Brain Error: {str(e)[:100]}. Please try again."
