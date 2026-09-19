import streamlit as st
import helpers
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Quran Study Companion", page_icon="📖", layout="wide")

# Load CSS Theme
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
if "completed" not in st.session_state:
    st.session_state.completed = set()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Navigation
with st.sidebar:
    st.markdown("## 📖 Quran Companion")
    st.caption("Read · Listen · Reflect")
    st.markdown("---")
    nav = st.radio("Nav", ["🏠 Home", "📖 Browse Quran", "🧠 AI Companion", "🎙️ Recitation Coach"], label_visibility="collapsed")
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Points", f"{st.session_state.points} XP")
    c2.metric("Streak", f"{st.session_state.streak} Days")
    st.markdown("---")
    reciter_key = st.selectbox("Preferred Qari", list(helpers.RECITERS.keys()), format_func=lambda x: helpers.RECITERS[x])

# 🏠 HOME DASHBOARD
if nav == "🏠 Home":
    st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #34D399; font-weight: 600;">Verse of the day</span>
            <span style="color: #F6E05E; font-size: 14px;">Surah An-Nasr, 1–3</span>
        </div>
        <div class="arabic-text">
            بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ<br>
            إِذَا جَآءَ نَصْرُ ٱللَّهِ وَٱلْفَتْحُ <span class="ayah-no">﴿١﴾</span> وَرَأَيْتَ ٱلنَّاسَ يَدْخُلُونَ فِى دِينِ ٱللَّهِ أَفْوَاجًـا <span class="ayah-no">﴿٢﴾</span><br>
            فَسَبِّحْ بِحَمْدِ رَبِّكَ وَٱسْتَغْفِرْهُ ۚ إِنَّهُۥ كَانَ تَوَّابًـا <span class="ayah-no">﴿٣﴾</span>
        </div>
        <div class="transliteration">Iza jaa-a nas rullahi walfath...</div>
        <div class="translation">When the victory of Allah has come and the conquest...</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎯 Daily Goals")
    goals = [
        ("g1", "Learn Verse of the Day (+20 XP)"),
        ("g2", "Recite 1 Page with Voice Coach (+30 XP)"),
        ("g3", "Ask AI Companion a Question (+10 XP)")
    ]
    st.progress(len(st.session_state.completed) / len(goals))
    for gid, label in goals:
        done = gid in st.session_state.completed
        if st.checkbox(label, value=done, key=gid):
            if gid not in st.session_state.completed:
                st.session_state.completed.add(gid)
                st.session_state.points += 20
                st.rerun()

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

# 🧠 AI COMPANION
elif nav == "🧠 AI Companion":
    st.markdown("<h1>AI Quran & Hadith Companion</h1>", unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask any question about Tafseer, Hadith, or Islam..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Generating answer..."):
                messages = [{"role": "system", "content": "You are a helpful Quran and Islamic Studies companion."}]
                messages.extend(st.session_state.chat_history)
                reply = helpers.ask_llm(messages)
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# 🎙️ RECITATION COACH
elif nav == "🎙️ Recitation Coach":
    st.markdown("<h1>Live AI Recitation Coach</h1>", unsafe_allow_html=True)
    target_verse = "إِذَا جَآءَ نَصْرُ ٱللَّهِ وَٱلْفَتْحُ"
    
    st.markdown(f"""
    <div class="custom-card" style="text-align: center;">
        <span style="color: #34D399;">Target Practice Verse:</span>
        <div class="arabic-text">{target_verse}</div>
    </div>
    """, unsafe_allow_html=True)
    
    rec = mic_recorder(start_prompt="🔴 Start Recitation", stop_prompt="⏹️ Stop & Evaluate", key="mic")
    if rec:
        st.audio(rec["bytes"], format="audio/webm")
        with st.spinner("Analyzing speech..."):
            spoken, feedback, urdu_audio = helpers.evaluate_speech(rec["bytes"], target_verse)
            st.markdown(f"**Recognized Speech:** `{spoken}`")
            st.markdown("### 📋 AI Feedback")
            st.write(feedback)
            if urdu_audio:
                st.markdown("### 🔊 Urdu Teacher Audio")
                st.audio(urdu_audio, format="audio/mp3")
