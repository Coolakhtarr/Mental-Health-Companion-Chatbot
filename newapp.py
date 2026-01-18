import streamlit as st
import google.generativeai as genai
import time
import html
import pandas as pd
import altair as alt
from datetime import datetime

# -----------------------------------------------
# CONFIG
# -----------------------------------------------
st.set_page_config(page_title="MindEase Chat", page_icon="🌙", layout="wide", initial_sidebar_state="expanded")

# -----------------------------------------------
# CUSTOM CSS
# -----------------------------------------------
st.markdown("""
<style>
body {
    background-color: #0f0f1a;
    color: #e0e0e0;
    font-family: 'Inter', sans-serif;
}

/* Chat layout */
.clouds {
    display: flex;
    flex-direction: column;
    gap: 40px;
}

/* Chat bubbles */
.cloud-row { width: 100%; }
.cloud-card { display: flex; align-items: flex-start; }
.cloud {
    padding: 12px 16px;
    border-radius: 12px;
    max-width: 75%;
    box-shadow: 0 2px 10px rgba(0,0,0,0.4);
}
.cloud.assistant {
    background: #1e1b2e;
    border: 1px solid #3f3c61;
}
.cloud.user {
    background: #3f3c61;
    border: 1px solid #6d6aa8;
    align-self: flex-end;
}
.c-meta { font-size: 0.8rem; color: #aaa; margin-bottom: 5px; }
.c-body { color: #f3f3f3; line-height: 1.4; }

/* Sidebar layout tweaks */
[data-testid="stSidebar"] {
    width: 420px !important;
    min-width: 420px !important;
}
section.main > div {
    margin-left: 0 !important;
}

/* Mood card */
.mood-card {
    padding: 12px;
    border-radius: 12px;
    background: rgba(76,29,149,0.24);
    border: 1px solid rgba(139,92,246,0.35);
    margin-bottom: 16px;
}
.mood-card .label { color:#e9d5ff; font-weight:700; }
.mood-card .value { font-size:1.4rem; font-weight:800; color:#faf5ff; }
.mood-card .sub { font-size:0.85rem; color:#c4b5fd; }

.sidebar .stSlider label { color: #ddd !important; }

/* Sidebar compactness */
[data-testid="stSidebar"] .block-container { padding-top: 8px; padding-bottom: 8px; }
[data-testid="stSidebar"] .stMetric { margin-bottom: 4px; }
[data-testid="stSidebar"] .stMarkdown { margin-bottom: 6px; }
[data-testid="stSidebar"] .stAltairChart { margin-bottom: 8px; }
[data-testid="stSidebar"] .stSlider { margin-top: -6px; }
[data-testid="stSidebar"] .stButton>button { padding: 4px 8px; font-size: 0.9rem; }

/* Extra gap between messages so bubbles never touch */
.cloud-row + .cloud-row { margin-top: 18px; }
.cloud-row.user + .cloud-row.assistant { margin-top: 32px; }

/* Sidebar text compactness */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small { font-size: 0.92rem !important; line-height: 1.25; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { margin: 6px 0 4px; font-size: 1.0rem; }
[data-testid="stSidebar"] .stAlert { padding: 8px 10px; font-size: 0.90rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------
# SESSION STATE
# -----------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = None
if "latencies" not in st.session_state:
    st.session_state.latencies = []
if "mood_history" not in st.session_state:
    st.session_state.mood_history = []
if "session_started_at" not in st.session_state:
    st.session_state.session_started_at = time.time()

# -----------------------------------------------
# SIDEBAR
# -----------------------------------------------
st.sidebar.header("⚙️ Settings")
api_key = None
# Prefer API key from secrets.toml if available; otherwise allow manual entry as fallback.
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    st.sidebar.caption("Using API key from secrets.toml")
except KeyError:
    api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Optional here if not set in .streamlit/secrets.toml")

if api_key and st.session_state.chat is None:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.sidebar.error(f"API setup error: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Conversation Stats")
_messages = st.session_state.messages
_lat = st.session_state.latencies
_total = len(_messages)
_user = sum(1 for m in _messages if m.get("role") == "user")
_assistant = sum(1 for m in _messages if m.get("role") == "assistant")
_turns = len(_lat)
_avg_latency = (sum(_lat) / _turns) if _turns else 0.0
_last_latency = _lat[-1] if _turns else 0.0
_best_latency = min(_lat) if _turns else 0.0
_worst_latency = max(_lat) if _turns else 0.0
_elapsed = max(1e-6, time.time() - st.session_state.session_started_at)
_msgs_per_min = _total / (_elapsed / 60.0)

def _wc(msg):
    return len(msg.get("content", "").split())

_avg_user_words = (sum(_wc(m) for m in _messages if m.get("role") == "user") / _user) if _user else 0.0
_avg_assistant_words = (sum(_wc(m) for m in _messages if m.get("role") == "assistant") / _assistant) if _assistant else 0.0
_moods = st.session_state.mood_history
_mood_count = len(_moods)
_avg_mood = (sum(x["mood"] for x in _moods) / _mood_count) if _mood_count else 0.0

# Numeric KPIs
kpi_cols = st.sidebar.columns(2)
with kpi_cols[0]:
    st.metric("Total msgs", _total)
    st.metric("Turns", _turns)
    st.metric("Msgs/min", f"{_msgs_per_min:.2f}")
with kpi_cols[1]:
    st.metric("Avg rt (ms)", f"{_avg_latency:.0f}")
    st.metric("Last rt (ms)", f"{_last_latency:.0f}")
    st.metric("Fast/Slow (ms)", f"{_best_latency:.0f}/{_worst_latency:.0f}")

st.sidebar.caption(f"User/Assistant: {_user}/{_assistant} • Avg words U/A: {_avg_user_words:.1f}/{_avg_assistant_words:.1f}")

# Graphs
st.sidebar.markdown("### 📈 Graphs")
# Latency over turns
if _turns:
    df_lat = pd.DataFrame({
        "Turn": range(1, len(_lat) + 1),
        "Latency (ms)": _lat
    })
    ch_latency_line = alt.Chart(df_lat).mark_line(point=True).encode(
        x=alt.X("Turn:Q", title="Turn"),
        y=alt.Y("Latency (ms):Q", title="Latency (ms)"),
        color=alt.value("#8b5cf6")
).properties(height=100)
    st.sidebar.altair_chart(ch_latency_line, use_container_width=True)

    ch_latency_hist = alt.Chart(df_lat).mark_bar(color="#a78bfa").encode(
        x=alt.X("Latency (ms):Q", bin=alt.Bin(maxbins=20), title="Latency bins (ms)"),
        y=alt.Y("count():Q", title="Count")
    ).properties(height=100)
    st.sidebar.altair_chart(ch_latency_hist, use_container_width=True)

# User vs Assistant counts
if _total:
    df_counts = pd.DataFrame({
        "Role": ["User", "Assistant"],
        "Count": [_user, _assistant]
    })
    ch_counts = alt.Chart(df_counts).mark_bar().encode(
        x=alt.X("Role:N", title="Role"),
        y=alt.Y("Count:Q", title="Messages"),
        color=alt.Color("Role:N", scale=alt.Scale(range=["#60a5fa", "#8b5cf6"]))
).properties(height=100)
    st.sidebar.altair_chart(ch_counts, use_container_width=True)

# Messages per minute timeseries
if _total:
    rows = [{"ts": m.get("ts"), "role": m.get("role")} for m in _messages if m.get("ts")]
    if rows:
        df_msgs = pd.DataFrame(rows)
        df_msgs["dt"] = pd.to_datetime(df_msgs["ts"], unit="s")
        df_msgs["minute"] = df_msgs["dt"].dt.floor("T")
        df_rate = df_msgs.groupby(["minute", "role"]).size().reset_index(name="count")
        ch_rate = alt.Chart(df_rate).mark_line(point=True).encode(
            x=alt.X("minute:T", title="Time (per min)"),
            y=alt.Y("count:Q", title="Msgs/min"),
            color=alt.Color("role:N", title="Role", scale=alt.Scale(range=["#60a5fa", "#8b5cf6"]))
).properties(height=110)
        st.sidebar.altair_chart(ch_rate, use_container_width=True)

# Mood controls and trend
st.sidebar.markdown("### 🧠 Mood")
with st.sidebar:
    mood_val = st.slider("How are you feeling?", 0, 10, 5, key="mood_slider")
    cols = st.columns(2)
    if cols[0].button("Save mood", key="mood_save"):
        st.session_state.mood_history.append({"t": time.time(), "mood": mood_val})
        st.success("Mood saved")
    if _mood_count:
        df_mood = pd.DataFrame(st.session_state.mood_history)
        df_mood["dt"] = pd.to_datetime(df_mood["t"], unit="s")
        ch_mood = alt.Chart(df_mood).mark_line(point=True, color="#34d399").encode(
            x=alt.X("dt:T", title="Time"),
            y=alt.Y("mood:Q", title="Mood", scale=alt.Scale(domain=[0, 10]))
).properties(height=100)
        st.altair_chart(ch_mood, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("🧘 Mental health support tool.\n\nIndia Helpline: **1098** or **9152987821 (AASRA)**")

# (Left floating panel removed in favor of enlarged Streamlit sidebar with charts)

# -----------------------------------------------
# WELCOME + QUICK START
# -----------------------------------------------
queued_input = None
if len(st.session_state.messages) == 0:
    st.markdown("## Welcome to MindEase 🌙")
    st.markdown("I'm here to support you. Choose a quick prompt below or type your own message.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Breathing exercise", key="quick_breathe"):
            queued_input = "Can you guide me through a short breathing exercise?"
        if st.button("Feeling anxious", key="quick_anxious"):
            queued_input = "I'm feeling anxious. Can you help me calm down?"
    with c2:
        if st.button("Feeling low", key="quick_low"):
            queued_input = "I'm feeling low today. Can we talk about it?"
        if st.button("Daily check-in", key="quick_checkin"):
            queued_input = "Let's do a quick mood check-in."

# -----------------------------------------------
# CHAT DISPLAY
# -----------------------------------------------
st.markdown("<div class='clouds'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    align = "right" if role == "user" else "left"
    role_class = "user" if role == "user" else "assistant"
    name = "You" if role == "user" else "Companion"
    ts = msg.get("ts", "")
    ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
    safe_text = html.escape(msg.get("content", "")).replace("\n", "<br>")
    st.markdown(f"""
<div class=\"cloud-row {align} {role_class}\">
        <div class="cloud-card" style="justify-content:{'flex-end' if role=='user' else 'flex-start'};">
            <div class="cloud {role_class}">
                <div class="c-meta">{name} • {ts_str}</div>
                <div class="c-body">{safe_text}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------
# CHAT INPUT
# -----------------------------------------------
user_input = st.chat_input("Type your message here…")
if not user_input and 'queued_input' in locals() and queued_input:
    user_input = queued_input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "ts": time.time()})

    # Crisis keyword detection
    CRISIS_KEYWORDS = ["suicide", "self-harm", "kill myself", "end my life", "hopeless", "despair"]
    if any(kw in user_input.lower() for kw in CRISIS_KEYWORDS):
        st.error("⚠️ If you are in crisis, please seek immediate help.\n\nIndia Helpline: **1098** or **9152987821 (AASRA)**")

    if st.session_state.chat is None:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⚠️ Please enter a valid Gemini API key in the sidebar to start chatting.",
            "ts": time.time()
        })
    else:
        try:
            t0 = time.time()
            response = st.session_state.chat.send_message(user_input)
            t1 = time.time()
            st.session_state.latencies.append((t1 - t0) * 1000)
            assistant_text = response.text if hasattr(response, "text") else str(response)
        except Exception as e:
            assistant_text = f"I had trouble contacting the model: {e}"
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "ts": time.time()
        })
    st.rerun()


