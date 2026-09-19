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
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is not set in Streamlit secrets."

    system_instruction = None
    contents = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "system":
            system_instruction = {"parts": [{"text": content}]}
        else:
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

    payload = {"contents": contents}
    if system_instruction:
        payload["systemInstruction"] = system_instruction

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return f"Gemini API Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Error connecting to Gemini API: {str(e)}"
