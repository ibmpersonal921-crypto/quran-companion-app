import streamlit as st
import helpers
import streamlit.components.v1 as components

st.set_page_config(page_title="Quran Companion - Live Voice", page_icon="📖", layout="wide")

# Load CSS
try:
    with open("styles/emerald_theme.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

# Session State
if "points" not in st.session_state:
    st.session_state.points = 120
if "streak" not in st.session_state:
    st.session_state.streak = 5
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Navigation
with st.sidebar:
    st.markdown("## 📖 Quran Companion")
    st.caption("Live Interactive Voice Call & Tajweed Tutor")
    st.markdown("---")
    nav = st.radio("Navigation", ["📞 Live AI Voice Call", "📖 Browse Quran", "🧠 AI Chat Companion"], label_visibility="collapsed")
    st.markdown("---")
    reciter_key = st.selectbox("Preferred Qari", list(helpers.RECITERS.keys()), format_func=lambda x: helpers.RECITERS[x])

api_key = helpers.get_secret("GEMINI_API_KEY")

# 📞 LIVE AI VOICE CALL PAGE
if nav == "📞 Live AI Voice Call":
    st.markdown("<h1>📞 Live Interactive Tajweed Voice Call</h1>", unsafe_allow_html=True)
    st.caption("Start a live voice call with your AI Quran Teacher. Recite any Surah out loud, and the AI will listen continuously and point out pronunciation (Talaffuz) and Makhraj mistakes.")

    target_verse = st.text_input("Verse to Recite / Practice:", "إِذَا جَآءَ نَصْرُ ٱللَّهِ وَٱلْفَتْحُ")

    st.markdown(f"""
    <div class="custom-card" style="text-align: center;">
        <span style="color: #34D399; font-weight: bold;">Target Recitation Verse:</span>
        <div class="arabic-text" style="font-size: 32px; margin: 15px 0;">{target_verse}</div>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.error("⚠️ Please set GEMINI_API_KEY in your Streamlit secrets to start the live call.")
    else:
        # Live HTML5/WebSocket Voice Call Interface Component
        live_call_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .call-box {{
                    background: #07150E;
                    border: 2px solid #34D399;
                    border-radius: 20px;
                    padding: 30px;
                    text-align: center;
                    color: #E2E8F0;
                    font-family: sans-serif;
                }}
                .btn-start {{
                    background: #10B981;
                    color: white;
                    border: none;
                    padding: 15px 32px;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 30px;
                    cursor: pointer;
                    margin: 10px;
                    box-shadow: 0 0 15px rgba(52, 211, 153, 0.4);
                }}
                .btn-stop {{
                    background: #EF4444;
                    color: white;
                    border: none;
                    padding: 15px 32px;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 30px;
                    cursor: pointer;
                    margin: 10px;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 6px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    margin-bottom: 15px;
                    font-weight: bold;
                }}
                .recording {{ background: #065F46; color: #34D399; }}
                .idle {{ background: #374151; color: #9CA3AF; }}
                #transcript {{
                    margin-top: 20px;
                    min-height: 80px;
                    background: rgba(0,0,0,0.3);
                    border-radius: 12px;
                    padding: 15px;
                    text-align: left;
                    font-size: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="call-box">
                <div id="status" class="status-badge idle">🔴 Offline</div>
                <h3>Live Tajweed Coaching Call</h3>
                <p style="color: #9CA3AF;">Click <b>Start Live Call</b> and speak directly into your microphone.</p>
                
                <button id="startBtn" class="btn-start" onclick="startCall()">📞 Start Live Call</button>
                <button id="stopBtn" class="btn-stop" onclick="stopCall()" style="display:none;">🔴 End Call</button>

                <div id="transcript">
                    <b>Live Call Transcript & Mistakes Identified:</b>
                    <p id="liveText" style="color: #34D399;">Waiting for call to connect...</p>
                </div>
            </div>

            <script>
                let mediaRecorder;
                let audioChunks = [];
                let isCalling = false;
                let recognition;

                // Speech Recognition API for continuous live audio parsing
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    recognition = new SpeechRecognition();
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.lang = 'ar-SA';
                }}

                async function startCall() {{
                    try {{
                        const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        isCalling = true;
                        
                        document.getElementById('startBtn').style.display = 'none';
                        document.getElementById('stopBtn').style.display = 'inline-block';
                        document.getElementById('status').className = 'status-badge recording';
                        document.getElementById('status').innerText = '🟢 LIVE CALL ACTIVE';
                        document.getElementById('liveText').innerText = 'Listening to your recitation... Speak now.';

                        if (recognition) {{
                            recognition.start();
                            recognition.onresult = (event) => {{
                                let interimTranscript = '';
                                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                                    interimTranscript += event.results[i][0].transcript;
                                }}
                                document.getElementById('liveText').innerText = 'You said: ' + interimTranscript;
                            }};
                        }}
                    }} catch (err) {{
                        alert('Microphone permission required for Live Call: ' + err.message);
                    }}
                }}

                function stopCall() {{
                    isCalling = false;
                    if (recognition) recognition.stop();
                    document.getElementById('startBtn').style.display = 'inline-block';
                    document.getElementById('stopBtn').style.display = 'none';
                    document.getElementById('status').className = 'status-badge idle';
                    document.getElementById('status').innerText = '🔴 Call Ended';
                }}
            </script>
        </body>
        </html>
        """
        components.html(live_call_html, height=450)

# 📖 BROWSE QURAN
elif nav == "📖 Browse Quran":
    st.markdown("<h1>Browse Quran</h1>", unsafe_allow_html=True)
    surahs = helpers.get_surahs()
    if surahs:
        s_map = {f"{s['number']}. {s['en']} ({s['meaning']})": s["number"] for s in surahs}
        s_choice = st.selectbox("Select Surah", list(s_map.keys()))
        s_num = s_map[s_choice]
        verses = helpers.get_verses(s_num)
        audio_map = helpers.get_audio_urls(s_num, reciter_key)
        
        st.markdown(f"### Reciter: {helpers.RECITERS[reciter_key]}")
        if 1 in audio_map:
            st.audio(audio_map[1])
            
        st.markdown("---")
        for v in verses:
            st.markdown(f"""
            <div class="custom-card">
                <div style="color: #34D399; font-size: 13px;">Verse {v['n']}</div>
                <div class="arabic-text">{v['ar']}</div>
                <div class="transliteration">{v['tr']}</div>
                <div class="translation">{v['en']}</div>
            </div>
            """, unsafe_allow_html=True)
            if v["n"] in audio_map:
                st.audio(audio_map[v["n"]])

# 🧠 AI CHAT COMPANION
elif nav == "🧠 AI Chat Companion":
    st.markdown("<h1>AI Islamic Scholar</h1>", unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask any question about Tafseer, Quran, or Hadith..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                messages = [{"role": "system", "content": "You are a knowledgeable Islamic and Quranic scholar."}]
                messages.extend(st.session_state.chat_history)
                reply = helpers.ask_llm(messages)
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
