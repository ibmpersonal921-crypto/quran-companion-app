import html
import io
import json
import re
import time
import requests
import speech_recognition as sr
import streamlit as st
from gtts import gTTS

RECITERS = {
    "ar.alafasy": "Mishary Rashid Alafasy",
    "ar.abdulbasitmurattal": "Abdul Basit Abdus Samad",
    "ar.abdurrahmaansudais": "Abdur-Rahman As-Sudais",
    "ar.husary": "Mahmoud Khalil Al-Husary",
    "ar.minshawi": "Mohamed Siddiq Al-Minshawi"
}

BASE_QURAN = "https://api.alquran.cloud/v1"
BASE_ISLAMIC = "https://api.islamic.app/v1"

def get_secret(key_name, default=""):
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return str(st.secrets[key_name])
    except Exception:
        pass
    return default

def http_get(url, params=None):
    headers = {"User-Agent": "QuranCompanionApp/1.0"}
    for _ in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.json()
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    return {}

@st.cache_data(ttl=86400*7)
def get_surahs():
    j = http_get(f"{BASE_QURAN}/surah")
    return [{"number": s["number"], "ar": s["name"], "en": s["englishName"], "meaning": s["englishNameTranslation"], "ayahs": s["numberOfAyahs"]} for s in j.get("data", [])]

@st.cache_data(ttl=86400*30)
def get_verses(surah_num):
    ar = http_get(f"{BASE_QURAN}/surah/{surah_num}/quran-uthmani").get("data", {}).get("ayahs", [])
    tr = http_get(f"{BASE_QURAN}/surah/{surah_num}/en.transliteration").get("data", {}).get("ayahs", [])
    en = http_get(f"{BASE_QURAN}/surah/{surah_num}/en.sahih").get("data", {}).get("ayahs", [])
    
    out = []
    for i in range(len(ar)):
        out.append({
            "n": ar[i]["numberInSurah"],
            "ar": ar[i]["text"],
            "tr": tr[i]["text"] if i < len(tr) else "",
            "en": en[i]["text"] if i < len(en) else ""
        })
    return out

@st.cache_data(ttl=86400*30)
def get_audio_urls(surah_num, reciter_key):
    data = http_get(f"{BASE_QURAN}/surah/{surah_num}/{reciter_key}").get("data", {}).get("ayahs", [])
    return {a["numberInSurah"]: a["audio"] for a in data if a.get("audio")}

def ask_llm(messages):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY is not set in Streamlit secrets."
    
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": messages,
        "temperature": 0.2
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=30)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return f"API Error: {r.status_code} - {r.text}"

def evaluate_speech(audio_bytes, target_arabic):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            recorded = recognizer.record(source)
        spoken = recognizer.recognize_google(recorded, language="ar-SA")
    except Exception:
        spoken = "Could not clearly capture Arabic speech."

    prompt = f"Expected Verse: {target_arabic}\nStudent Recited: {spoken}\nProvide feedback on pronunciation accuracy (Talaffuz) and Makhraj in English and Urdu."
    feedback = ask_llm([{"role": "system", "content": "You are a Quran Tajweed Teacher."}, {"role": "user", "content": prompt}])

    tts_stream = None
    try:
        tts = gTTS(text=feedback, lang='ur')
        tts_stream = io.BytesIO()
        tts.write_to_fp(tts_stream)
        tts_stream.seek(0)
    except Exception:
        pass

    return spoken, feedback, tts_stream
