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

# Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.markdown("## 📖 Quran Companion")
    st.caption("Live AI Tajweed Teacher")
    st.markdown("---")
    nav = st.radio("Navigation", ["📞 Live Voice Call (Real-time Audio)", "📖 Browse Quran", "🧠 AI Chat Companion"], label_visibility="collapsed")
    st.markdown("---")
    reciter_key = st.selectbox("Preferred Qari", list(helpers.RECITERS.keys()), format_func=lambda x: helpers.RECITERS[x])

api_key = helpers.get_secret("GEMINI_API_KEY")

# 📞 LIVE REALTIME VOICE CALL
if nav == "📞 Live Voice Call (Real-time Audio)":
    st.markdown("<h1>📞 Real-time Voice Call with AI Tajweed Teacher</h1>", unsafe_allow_html=True)
    st.caption("Start a duplex audio call. Recite out loud—the AI will listen continuously and speak back immediately to correct any Tajweed or pronunciation mistake.")

    target_verse = st.text_input("Verse to Recite:", "إِذَا جَآءَ نَصْرُ ٱللَّهِ وَٱلْفَتْحُ")

    st.markdown(f"""
    <div class="custom-card" style="text-align: center; margin-bottom: 20px;">
        <span style="color: #34D399; font-weight: bold;">Target Recitation Verse:</span>
        <div class="arabic-text" style="font-size: 32px; margin: 15px 0;">{target_verse}</div>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.error("⚠️ GEMINI_API_KEY is missing from Streamlit secrets.")
    else:
        # Gemini WebSocket Realtime Audio HTML/JS Component
        live_audio_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .call-container {{
                    background: #07150E;
                    border: 2px solid #34D399;
                    border-radius: 20px;
                    padding: 30px;
                    text-align: center;
                    color: white;
                    font-family: Arial, sans-serif;
                }}
                .btn {{
                    padding: 16px 36px;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 35px;
                    border: none;
                    cursor: pointer;
                    margin: 10px;
                    transition: 0.2s;
                }}
                .btn-start {{ background: #10B981; color: white; box-shadow: 0 0 15px rgba(16,185,129,0.4); }}
                .btn-stop {{ background: #EF4444; color: white; }}
                .status-badge {{
                    display: inline-block;
                    padding: 6px 18px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                    margin-bottom: 15px;
                }}
                .active {{ background: #065F46; color: #34D399; animation: pulse 1.5s infinite; }}
                .inactive {{ background: #374151; color: #9CA3AF; }}
                .error-state {{ background: #7F1D1D; color: #FCA5A5; }}
                @keyframes pulse {{
                    0% {{ box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.4); }}
                    70% {{ box-shadow: 0 0 0 12px rgba(52, 211, 153, 0); }}
                    100% {{ box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }}
                }}
                #logBox {{
                    margin-top: 20px;
                    background: rgba(0,0,0,0.4);
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
            <div class="call-container">
                <div id="status" class="status-badge inactive">🔴 Call Disconnected</div>
                <h2>Interactive Tajweed Coaching Call</h2>
                <p style="color: #9CA3AF;">The AI acts as your live Quran teacher. Speak directly into your microphone—it will interrupt and correct you by voice if you make a mistake.</p>
                
                <button id="startBtn" class="btn btn-start" onclick="connectLiveCall()">📞 Start Voice Call</button>
                <button id="stopBtn" class="btn btn-stop" onclick="disconnectLiveCall()" style="display:none;">🔴 End Call</button>

                <div id="logBox">
                    <b>Live Call Feed:</b>
                    <p id="statusText" style="color: #9CA3AF; margin-top: 5px;">Click 'Start Voice Call' to initiate live streaming...</p>
                </div>
            </div>

            <script>
                const API_KEY = "{api_key}";
                const TARGET_VERSE = "{target_verse}";
                let ws;
                let audioCtx;
                let micStream;
                let scriptProcessor;

                async function connectLiveCall() {{
                    document.getElementById('statusText').innerText = "Requesting microphone access...";
                    
                    try {{
                        micStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    }} catch (err) {{
                        showError("Microphone access denied or unavailable: " + err.message);
                        return;
                    }}

                    document.getElementById('statusText').innerText = "Connecting to Gemini Multimodal Live API...";
                    
                    const wsUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${{API_KEY}}`;
                    
                    try {{
                        ws = new WebSocket(wsUrl);
                        
                        ws.onopen = () => {{
                            document.getElementById('startBtn').style.display = 'none';
                            document.getElementById('stopBtn').style.display = 'inline-block';
                            document.getElementById('status').className = 'status-badge active';
                            document.getElementById('status').innerText = '🟢 LIVE CALL CONNECTED';
                            document.getElementById('statusText').innerText = "Call active. Start reciting out loud!";
                            
                            const setupMsg = {{
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
                                            text: `You are an expert, strict, real-time Quran Tajweed Teacher. The user is practicing the verse: "${{TARGET_VERSE}}". Listen continuously to their recitation in Arabic. The instant they mispronounce a word, make a Tajweed error, or skip a letter, interrupt them immediately in voice and explain the correct pronunciation and Makhraj clearly and briefly.`
                                        }}]
                                    }}
                                }}
                            }};
                            ws.send(JSON.stringify(setupMsg));
                            startMicStreaming();
                        }};

                        ws.onmessage = async (event) => {{
                            try {{
                                let data;
                                if (event.data instanceof Blob) {{
                                    data = JSON.parse(await event.data.text());
                                }} else {{
                                    data = JSON.parse(event.data);
                                }}

                                if (data.serverContent && data.serverContent.modelTurn) {{
                                    const parts = data.serverContent.modelTurn.parts;
                                    for (let part of parts) {{
                                        if (part.inlineData && part.inlineData.data) {{
                                            playAudioChunk(part.inlineData.data);
                                            document.getElementById('statusText').innerText = "AI Teacher is speaking feedback...";
                                        }}
                                    }}
                                }}
                            }} catch (e) {{
                                console.error("Error parsing message", e);
                            }}
                        }};

                        ws.onclose = (event) => {{
                            if (event.code !== 1000) {{
                                showError(`WebSocket closed unexpectedly (Code: ${{event.code}}, Reason: ${{event.reason || 'Authentication or API Key restriction'}}).`);
                            }} else {{
                                disconnectLiveCall();
                            }}
                        }};

                        ws.onerror = (err) => {{
                            showError("WebSocket encountered a connection error.");
                        }};

                    }} catch (e) {{
                        showError("Error starting call: " + e.message);
                    }}
                }}

                async function startMicStreaming() {{
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 16000 }});
                    const source = audioCtx.createMediaStreamSource(micStream);
                    
                    scriptProcessor = audioCtx.createScriptProcessor(2048, 1, 1);
                    source.connect(scriptProcessor);
                    scriptProcessor.connect(audioCtx.destination);

                    scriptProcessor.onaudioprocess = (e) => {{
                        if (!ws || ws.readyState !== WebSocket.OPEN) return;
                        
                        const inputData = e.inputBuffer.getChannelData(0);
                        const pcm16 = new Int16Array(inputData.length);
                        for (let i = 0; i < inputData.length; i++) {{
                            pcm16[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
                        }}
                        
                        let binary = '';
                        const bytes = new Uint8Array(pcm16.buffer);
                        for (let i = 0; i < bytes.byteLength; i++) {{
                            binary += String.fromCharCode(bytes[i]);
                        }}
                        const base64Audio = btoa(binary);

                        const audioMsg = {{
                            realtimeInput: {{
                                mediaChunks: [{{
                                    mimeType: "audio/pcm;rate=16000",
                                    data: base64Audio
                                }}]
                            }}
                        }};
                        ws.send(JSON.stringify(audioMsg));
                    }};
                }}

                function playAudioChunk(base64PCM) {{
                    try {{
                        const binaryStr = atob(base64PCM);
                        const len = binaryStr.length;
                        const bytes = new Uint8Array(len);
                        for (let i = 0; i < len; i++) {{
                            bytes[i] = binaryStr.charCodeAt(i);
                        }}
                        const int16Array = new Int16Array(bytes.buffer);
                        
                        const outCtx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 24000 }});
                        const buffer = outCtx.createBuffer(1, int16Array.length, 24000);
                        const channelData = buffer.getChannelData(0);
                        for (let i = 0; i < int16Array.length; i++) {{
                            channelData[i] = int16Array[i] / 32768.0;
                        }}

                        const src = outCtx.createBufferSource();
                        src.buffer = buffer;
                        src.connect(outCtx.destination);
                        src.start();
                    }} catch (e) {{
                        console.error("Audio playback error:", e);
                    }}
                }}

                function showError(msg) {{
                    if (ws) ws.close();
                    if (micStream) micStream.getTracks().forEach(track => track.stop());
                    if (audioCtx) audioCtx.close();
                    
                    document.getElementById('startBtn').style.display = 'inline-block';
                    document.getElementById('stopBtn').style.display = 'none';
                    document.getElementById('status').className = 'status-badge error-state';
                    document.getElementById('status').innerText = '⚠️ Connection Error';
                    document.getElementById('statusText').innerText = msg;
                }}

                function disconnectLiveCall() {{
                    if (ws) ws.close();
                    if (micStream) micStream.getTracks().forEach(track => track.stop());
                    if (audioCtx) audioCtx.close();
                    
                    document.getElementById('startBtn').style.display = 'inline-block';
                    document.getElementById('stopBtn').style.display = 'none';
                    document.getElementById('status').className = 'status-badge inactive';
                    document.getElementById('status').innerText = '🔴 Call Disconnected';
                    document.getElementById('statusText').innerText = 'Call ended. Click Start to try again.';
                }}
            </script>
        </body>
        </html>
        """
        components.html(live_audio_html, height=520)

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
