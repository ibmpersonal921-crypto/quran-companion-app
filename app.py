import streamlit as st
import helpers
import streamlit.components.v1 as components

st.set_page_config(page_title="Quran Companion - Realtime Audio Call", page_icon="📖", layout="wide")

# Load CSS
try:
    with open("styles/emerald_theme.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.markdown("## 📖 Quran Companion")
    st.caption("Live AI Tajweed Teacher")
    st.markdown("---")
    nav = st.radio("Navigation", ["📞 Live Voice Call", "📖 Browse Quran", "🧠 AI Chat Companion"], label_visibility="collapsed")
    st.markdown("---")
    reciter_key = st.selectbox("Preferred Qari", list(helpers.RECITERS.keys()), format_func=lambda x: helpers.RECITERS[x])

api_key = helpers.get_secret("GEMINI_API_KEY")

# 📞 LIVE REALTIME VOICE CALL
if nav == "📞 Live Voice Call":
    st.markdown("<h1>📞 Real-Time Live Voice Call</h1>", unsafe_allow_html=True)
    st.caption("Full-duplex audio call with Gemini 2.0 Live API. Recite continuously out loud—the AI will listen in real time and interrupt via voice if you make a mistake.")

    target_verse = st.text_input("Verse to Practice:", "إِذَا جَآءَ نَصْرُ ٱللَّهِ وَٱلْفَتْحُ")

    st.markdown(f"""
    <div class="custom-card" style="text-align: center; margin-bottom: 20px;">
        <span style="color: #34D399; font-weight: bold;">Target Recitation Verse:</span>
        <div class="arabic-text" style="font-size: 32px; margin: 15px 0;">{target_verse}</div>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.error("⚠️ GEMINI_API_KEY is missing from Streamlit secrets.")
    else:
        live_audio_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .call-card {{
                    background: #07150E;
                    border: 2px solid #34D399;
                    border-radius: 20px;
                    padding: 30px;
                    text-align: center;
                    color: white;
                    font-family: system-ui, -apple-system, sans-serif;
                }}
                .btn {{
                    padding: 16px 36px;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 35px;
                    border: none;
                    cursor: pointer;
                    margin: 10px;
                }}
                .btn-start {{ background: #10B981; color: white; box-shadow: 0 0 15px rgba(16,185,129,0.4); }}
                .btn-stop {{ background: #EF4444; color: white; }}
                .badge {{
                    display: inline-block;
                    padding: 6px 18px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                    margin-bottom: 15px;
                }}
                .active {{ background: #065F46; color: #34D399; animation: pulse 1.5s infinite; }}
                .inactive {{ background: #374151; color: #9CA3AF; }}
                .error-badge {{ background: #7F1D1D; color: #FCA5A5; }}
                @keyframes pulse {{
                    0% {{ box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.4); }}
                    70% {{ box-shadow: 0 0 0 12px rgba(52, 211, 153, 0); }}
                    100% {{ box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }}
                }}
                #logBox {{
                    margin-top: 20px;
                    background: rgba(0,0,0,0.5);
                    border-radius: 10px;
                    padding: 15px;
                    font-size: 14px;
                    color: #A7F3D0;
                    min-height: 80px;
                    text-align: left;
                    word-break: break-word;
                }}
            </style>
        </head>
        <body>
            <div class="call-card">
                <div id="status" class="badge inactive">🔴 Offline</div>
                <h2>Live Voice Call Connected</h2>
                <p style="color: #9CA3AF;">Continuous bidirectional streaming active. Speak directly into your mic.</p>
                
                <button id="startBtn" class="btn btn-start" onclick="initiateCall()">📞 Start Live Call</button>
                <button id="stopBtn" class="btn btn-stop" onclick="endCall()" style="display:none;">🔴 End Call</button>

                <div id="logBox">
                    <b>Live Feed:</b>
                    <p id="statusMsg" style="color: #9CA3AF; margin-top: 5px;">Ready to initiate WebSocket stream.</p>
                </div>
            </div>

            <script>
                const API_KEY = "{api_key}";
                const TARGET_VERSE = "{target_verse}";
                let ws;
                let audioCtx;
                let micStream;
                let scriptProcessor;
                let nextPlayTime = 0;

                async function initiateCall() {{
                    document.getElementById('statusMsg').innerText = "Initializing Audio Hardware...";
                    
                    try {{
                        audioCtx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 16000 }});
                        await audioCtx.resume();
                        
                        micStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    }} catch (err) {{
                        setUIError("Microphone Access Error: " + err.message);
                        return;
                    }}

                    document.getElementById('statusMsg').innerText = "Connecting to Gemini 2.0 Live WebSocket...";
                    
                    const wsUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${{API_KEY}}`;
                    
                    try {{
                        ws = new WebSocket(wsUrl);

                        ws.onopen = () => {{
                            document.getElementById('startBtn').style.display = 'none';
                            document.getElementById('stopBtn').style.display = 'inline-block';
                            document.getElementById('status').className = 'badge active';
                            document.getElementById('status').innerText = '🟢 CALL LIVE';
                            document.getElementById('statusMsg').innerText = "Call Active. Start reciting out loud!";

                            // Send setup frame for Gemini 2.0 Flash Realtime
                            const setupConfig = {{
                                setup: {{
                                    model: "models/gemini-2.0-flash-exp",
                                    generationConfig: {{
                                        responseModalities: ["AUDIO"],
                                        speechConfig: {{
                                            voiceConfig: {{
                                                prebuiltVoiceConfig: {{ voiceName: "Aoede" }}
                                            }}
                                        }}
                                    }},
                                    systemInstruction: {{
                                        parts: [{{
                                            text: `You are an expert Quran Tajweed Teacher. The user is practicing: "${{TARGET_VERSE}}". Listen continuously to their voice in real-time. If they mispronounce a word, mess up a vowel, or make a Tajweed error, interrupt them instantly by voice to correct them.`
                                        }}]
                                    }}
                                }}
                            }};
                            ws.send(JSON.stringify(setupConfig));
                            streamMicData();
                        }};

                        ws.onmessage = async (event) => {{
                            try {{
                                let msg = event.data instanceof Blob ? JSON.parse(await event.data.text()) : JSON.parse(event.data);
                                if (msg.serverContent && msg.serverContent.modelTurn) {{
                                    const parts = msg.serverContent.modelTurn.parts;
                                    for (let p of parts) {{
                                        if (p.inlineData && p.inlineData.data) {{
                                            playIncomingAudio(p.inlineData.data);
                                            document.getElementById('statusMsg').innerText = "AI Teacher is speaking feedback...";
                                        }}
                                    }}
                                }}
                            }} catch (e) {{
                                console.error("Parse error:", e);
                            }}
                        }};

                        ws.onclose = (e) => {{
                            if (e.code !== 1000) {{
                                setUIError(`WebSocket Closed: Code ${{e.code}} (${{e.reason || 'Check API key access to gemini-2.0-flash-exp'}}).`);
                            }} else {{
                                endCall();
                            }}
                        }};

                        ws.onerror = (e) => {{
                            setUIError("WebSocket encountered a network error.");
                        }};

                    }} catch (e) {{
                        setUIError("Initialization failed: " + e.message);
                    }}
                }}

                function streamMicData() {{
                    const source = audioCtx.createMediaStreamSource(micStream);
                    scriptProcessor = audioCtx.createScriptProcessor(2048, 1, 1);
                    source.connect(scriptProcessor);
                    scriptProcessor.connect(audioCtx.destination);

                    scriptProcessor.onaudioprocess = (e) => {{
                        if (!ws || ws.readyState !== WebSocket.OPEN) return;
                        
                        const input = e.inputBuffer.getChannelData(0);
                        const pcm16 = new Int16Array(input.length);
                        for (let i = 0; i < input.length; i++) {{
                            pcm16[i] = Math.max(-1, Math.min(1, input[i])) * 0x7FFF;
                        }}
                        
                        let binary = '';
                        const bytes = new Uint8Array(pcm16.buffer);
                        for (let i = 0; i < bytes.byteLength; i++) {{
                            binary += String.fromCharCode(bytes[i]);
                        }}

                        ws.send(JSON.stringify({{
                            realtimeInput: {{
                                mediaChunks: [{{
                                    mimeType: "audio/pcm;rate=16000",
                                    data: btoa(binary)
                                }}]
                            }}
                        }}));
                    }};
                }}

                function playIncomingAudio(base64Pcm) {{
                    try {{
                        const str = atob(base64Pcm);
                        const bytes = new Uint8Array(str.length);
                        for (let i = 0; i < str.length; i++) bytes[i] = str.charCodeAt(i);
                        
                        const pcm16 = new Int16Array(bytes.buffer);
                        const outCtx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 24000 }});
                        const buffer = outCtx.createBuffer(1, pcm16.length, 24000);
                        const channel = buffer.getChannelData(0);
                        for (let i = 0; i < pcm16.length; i++) channel[i] = pcm16[i] / 32768.0;

                        const src = outCtx.createBufferSource();
                        src.buffer = buffer;
                        src.connect(outCtx.destination);
                        
                        const now = outCtx.currentTime;
                        nextPlayTime = Math.max(nextPlayTime, now);
                        src.start(nextPlayTime);
                        nextPlayTime += buffer.duration;
                    }} catch (err) {{
                        console.error("Playback error:", err);
                    }}
                }}

                function setUIError(msg) {{
                    endCall();
                    document.getElementById('status').className = 'badge error-badge';
                    document.getElementById('status').innerText = '⚠️ Call Error';
                    document.getElementById('statusMsg').innerText = msg;
                }}

                function endCall() {{
                    if (ws) ws.close();
                    if (micStream) micStream.getTracks().forEach(t => t.stop());
                    if (audioCtx) audioCtx.close();

                    document.getElementById('startBtn').style.display = 'inline-block';
                    document.getElementById('stopBtn').style.display = 'none';
                    document.getElementById('status').className = 'badge inactive';
                    document.getElementById('status').innerText = '🔴 Offline';
                }}
            </script>
        </body>
        </html>
        """
        # Critical Streamlit parameter: allow="microphone"
        components.html(live_audio_html, height=520, allow="microphone")

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
