import streamlit as st
from config import APP_NAME, APP_TAGLINE, APP_ICON, DAILY_GOAL_POINTS
from utils.helpers import inject_css, page_header, compute_streak
from database import db
from services import quran_api

st.set_page_config(page_title=f"{APP_NAME} — Dashboard", page_icon=APP_ICON, layout="wide")
db.init_db()
inject_css()

with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
        <span style="font-size:1.8rem;">{APP_ICON}</span>
        <div>
            <div style="font-weight:700;font-size:1.05rem;color:#f4f7f5;">{APP_NAME}</div>
            <div style="font-size:0.78rem;color:#7e9186;">{APP_TAGLINE}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr class='qsc-divider'/>", unsafe_allow_html=True)

top_l, top_r = st.columns([3, 2])
with top_l:
    page_header("Dashboard", "Welcome back — here's your study space for today.", "🏠")
with top_r:
    st.write("")
    quick_q = st.text_input("search", placeholder="Search or ask AI (e.g., 'Al-Fatiha tafsir')", label_visibility="collapsed")
    if quick_q:
        st.session_state["prefill_chat_question"] = quick_q
        st.info("Open **AI Companion** in the sidebar — your question is ready there. 🤖")

completion_dates = db.get_all_completion_dates()
streak = compute_streak(completion_dates)
total_points = db.get_total_points()
points_today = db.get_points_today()
goals_today = db.get_goals_for_date()
done_today = sum(1 for g in goals_today if g["is_done"])

s1, s2, s3, s4 = st.columns(4)
stats = [
    (s1, "🔥", streak, "Day Streak"),
    (s2, "⭐", total_points, "Total Points"),
    (s3, "✅", f"{done_today}/{len(goals_today)}", "Goals Today"),
    (s4, "➕", points_today, "Points Today"),
]
for col, emoji, value, label in stats:
    with col:
        st.markdown(f"""<div class="qsc-stat"><div class="value">{emoji} {value}</div><div class="label">{label}</div></div>""", unsafe_allow_html=True)

st.write("")

with st.spinner("Loading today's verse..."):
    verse = quran_api.get_verse_of_the_day()
    st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="qsc-card-header">
        <span class="qsc-label">Verse of the day</span>
        <span class="qsc-vod-tag">{verse.get('label','')}</span>
    </div>
    """, unsafe_allow_html=True)
    if verse.get("arabic"):
        st.markdown(f'<div class="arabic-text" style="font-size:1.7rem;">{verse["arabic"]}</div>', unsafe_allow_html=True)
    if verse.get("transliteration"):
        st.markdown(f'<p style="color:#b9c9c0;font-style:italic;margin-top:14px;">{verse["transliteration"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#f4f7f5;">{verse.get("english", "")}</p>', unsafe_allow_html=True)
    with st.expander("🇵🇰 Show Urdu translation"):
        st.markdown(f'<div class="urdu-text">{verse.get("urdu", "")}</div>', unsafe_allow_html=True)
    
    colA, colB = st.columns([1, 5])
    with colA:
        if st.button("➕ Add as today's goal"):
            db.add_goal("memorize_verse", f"Learn {verse.get('label')}", DAILY_GOAL_POINTS["memorize_verse"])
            st.success("Added to today's goals!")
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">Today\'s goals</span>', unsafe_allow_html=True)
st.write("")
with st.form("add_goal_form", clear_on_submit=True):
    gcol1, gcol2 = st.columns([4, 1])
    with gcol1:
        goal_desc = st.text_input("New goal", placeholder="e.g. Learn Surah Al-Asr", label_visibility="collapsed")
    with gcol2:
        submitted = st.form_submit_button("Add goal", use_container_width=True)
    if submitted and goal_desc.strip():
        db.add_goal("custom", goal_desc.strip(), DAILY_GOAL_POINTS["custom"])
        st.rerun()

if not goals_today:
    st.caption("No goals yet today — add one above.")
else:
    for g in goals_today:
        gc1, gc2, gc3 = st.columns([0.5, 5, 1])
        with gc1:
            checked = st.checkbox("", value=bool(g["is_done"]), key=f"goal_{g['id']}")
            if checked != bool(g["is_done"]):
                db.toggle_goal(g["id"], checked)
                st.rerun()
        with gc2:
            style = "text-decoration:line-through;color:#7e9186;" if g["is_done"] else "color:#f4f7f5;"
            st.markdown(f'<span style="{style}">{g["description"]}</span>', unsafe_allow_html=True)
        with gc3:
            st.markdown(f'<span class="qsc-tag">+{g["points"]} pts</span>', unsafe_allow_html=True)
    progress = done_today / max(1, len(goals_today))
    st.progress(progress, text=f"{done_today} of {len(goals_today)} goals complete today")
st.markdown("</div>", unsafe_allow_html=True)
