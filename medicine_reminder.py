import streamlit as st
import pandas as pd
import time
import threading
from datetime import datetime
from twilio.rest import Client

# ══════════════════════════════════════════════════════════════════════════════
# FILL IN YOUR TWILIO DETAILS — ONLY THESE TWO LINES NEED CHANGING
TWILIO_SID   = st.secrets["TWILIO_SID"]
TWILIO_TOKEN = st.secrets["TWILIO_TOKEN"]
TWILIO_FROM  = "whatsapp:+14155238886"              # ← DO NOT CHANGE
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MediCare Reminder",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: linear-gradient(135deg, #f0f4ff 0%, #faf8ff 50%, #f0fff4 100%); }
.hero-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 60%, #059669 100%);
    border-radius: 20px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    color: white; box-shadow: 0 8px 32px rgba(37,99,235,0.25);
}
.hero-header h1 { font-size: 2rem; font-weight: 700; margin: 0; }
.hero-header p { font-size: 1rem; margin: 0.3rem 0 0; opacity: 0.85; }
.card {
    background: white; border-radius: 16px; padding: 1.4rem 1.6rem;
    margin-bottom: 1rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #e8edf5;
}
.card-title { font-size: 1rem; font-weight: 600; color: #1e3a5f; margin-bottom: 0.8rem; }
.stat-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
.stat-box {
    flex: 1; background: white; border-radius: 14px; padding: 1.1rem 1.3rem;
    text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    border: 1px solid #e8edf5;
}
.stat-box .stat-num { font-size: 2rem; font-weight: 700; line-height: 1; }
.stat-box .stat-lbl { font-size: 0.75rem; color: #6b7280; margin-top: 0.3rem; text-transform: uppercase; }
.stat-green .stat-num { color: #059669; }
.stat-blue  .stat-num { color: #2563eb; }
.stat-red   .stat-num { color: #dc2626; }
.pill-tag {
    display: inline-block; background: #eff6ff; color: #1d4ed8;
    border: 1px solid #bfdbfe; border-radius: 20px;
    padding: 0.25rem 0.75rem; font-size: 0.8rem; font-weight: 500; margin: 0.15rem;
}
.sandbox-box {
    background: #f0fdf4; border-left: 4px solid #059669;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    font-size: 0.9rem; color: #14532d;
}
.sandbox-box code {
    background: #dcfce7; padding: 0.2rem 0.6rem;
    border-radius: 6px; font-weight: 700; font-size: 1rem; color: #065f46;
}
.alert-box {
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border-left: 4px solid #f59e0b; border-radius: 10px;
    padding: 0.8rem 1.2rem; margin-bottom: 1rem;
    font-size: 0.9rem; color: #92400e; font-weight: 500;
}
section[data-testid="stSidebar"] { background: #1e3a5f !important; }
section[data-testid="stSidebar"] * { color: white !important; }
.stButton > button { border-radius: 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session State — everything lives here, no CSV files ───────────────────────
def init_state():
    defaults = {
        "medicines": [
            {"name": "Metformin",           "time": "08:00", "session": "Morning"},
            {"name": "Sulfonylureas",       "time": "08:00", "session": "Morning"},
            {"name": "DPP-4 Inhibitors",   "time": "13:00", "session": "Afternoon"},
            {"name": "SGLT2 Inhibitors",   "time": "13:00", "session": "Afternoon"},
            {"name": "Thiazilidinediones", "time": "19:30", "session": "Night"},
        ],
        "family_numbers": ["+919876543210"],
        "history":         [],
        "reminder_active": False,
        "user_name":       "Dave",
        "user_condition":  "Diabetic",
        "user_gp":         "Dr. Satish",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Twilio send function ───────────────────────────────────────────────────────
def send_whatsapp(message, numbers=None):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        targets = numbers or st.session_state.family_numbers
        if not targets:
            return False, "No contacts added. Go to Family Contacts page."
        for num in targets:
            wa = num if num.startswith("whatsapp:") else f"whatsapp:{num}"
            client.messages.create(to=wa, from_=TWILIO_FROM, body=message)
        return True, f"Sent to {len(targets)} number(s)"
    except Exception as e:
        return False, str(e)

# ── Background reminder thread ─────────────────────────────────────────────────
def reminder_loop():
    sent_today = set()
    while st.session_state.get("reminder_active", False):
        now   = datetime.now().strftime("%H:%M")
        today = datetime.now().strftime("%Y-%m-%d")
        key   = f"{today}_{now}"
        if key not in sent_today:
            for med in st.session_state.medicines:
                if med["time"] == now:
                    meds_now = list({m["name"] for m in st.session_state.medicines if m["time"] == now})
                    send_whatsapp(
                        f"💊 MEDICINE REMINDER\n"
                        f"Hi {st.session_state.user_name}! "
                        f"Time for your {med['session']} medicines.\n"
                        f"Medicines: {', '.join(meds_now)}\n"
                        f"Stay healthy! ❤️"
                    )
                    sent_today.add(key)
                    break
        time.sleep(30)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💊 MediCare")
    st.markdown("---")
    page = st.radio("Navigate", [
        "🏠 Home",
        "💊 Medicines",
        "⏰ Reminders",
        "👨‍👩‍👧 Family Contacts",
        "📋 History",
        "⚙️ Settings",
    ])
    st.markdown("---")
    taken  = sum(1 for h in st.session_state.history if h.get("status") == "Taken")
    missed = len(st.session_state.history) - taken
    st.markdown(f"**✅ Taken:** {taken}")
    st.markdown(f"**❌ Missed:** {missed}")
    st.markdown("---")
    st.markdown(f"**Reminders:** {'🟢 Active' if st.session_state.reminder_active else '🔴 Inactive'}")

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown(f"""
    <div class="hero-header">
        <h1>💊 MediCare Reminder</h1>
        <p>Hello {st.session_state.user_name}! Stay on top of your health journey.</p>
    </div>""", unsafe_allow_html=True)

    now_mins = datetime.now().hour * 60 + datetime.now().minute
    upcoming = sorted(
        [(int(m["time"].split(":")[0])*60 + int(m["time"].split(":")[1]), m)
         for m in st.session_state.medicines
         if int(m["time"].split(":")[0])*60 + int(m["time"].split(":")[1]) > now_mins],
        key=lambda x: x[0]
    )
    if upcoming:
        nxt      = upcoming[0][1]
        nxt_meds = list({m["name"] for m in st.session_state.medicines if m["time"] == nxt["time"]})
        st.markdown(f'<div class="alert-box">⏰ <strong>Next reminder:</strong> {nxt["session"]} at {nxt["time"]} — {", ".join(nxt_meds)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box">✅ All medicines done for today! Great job.</div>', unsafe_allow_html=True)

    total  = len(st.session_state.history)
    taken  = sum(1 for h in st.session_state.history if h.get("status") == "Taken")
    missed = total - taken
    rate   = int(taken / total * 100) if total > 0 else 0
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box stat-green"><div class="stat-num">{taken}</div><div class="stat-lbl">Taken</div></div>
        <div class="stat-box stat-red">  <div class="stat-num">{missed}</div><div class="stat-lbl">Missed</div></div>
        <div class="stat-box stat-blue"> <div class="stat-num">{rate}%</div><div class="stat-lbl">Adherence</div></div>
        <div class="stat-box">           <div class="stat-num">{len(st.session_state.medicines)}</div><div class="stat-lbl">Medicines</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📋 Record Today\'s Intake</div>', unsafe_allow_html=True)
    sessions = {}
    for med in st.session_state.medicines:
        sessions.setdefault(med["session"], []).append(med["name"])
    for session, meds in sessions.items():
        with st.expander(f"🕐 {session} — {', '.join(meds)}"):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Taken", key=f"t_{session}"):
                    st.session_state.history.append({
                        "Date & Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Session": session, "Medicines": ", ".join(meds),
                        "status": "Taken", "Notes": "Taken on time"
                    })
                    st.success("Recorded! ✅")
            with c2:
                if st.button("❌ Missed", key=f"m_{session}"):
                    st.session_state.history.append({
                        "Date & Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Session": session, "Medicines": ", ".join(meds),
                        "status": "Missed", "Notes": "Missed dose"
                    })
                    st.warning("Recorded as missed ⚠️")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="card"><div class="card-title">👤 User Info</div>
        <p><strong>Name:</strong> {st.session_state.user_name}</p>
        <p><strong>Condition:</strong> {st.session_state.user_condition}</p>
        <p><strong>GP:</strong> {st.session_state.user_gp}</p></div>""", unsafe_allow_html=True)
    with c2:
        nums      = st.session_state.family_numbers
        nums_html = "".join(f"<p>📱 {n}</p>" for n in nums) if nums else "<p>No contacts yet.</p>"
        st.markdown(f'<div class="card"><div class="card-title">📞 Family Contacts</div>{nums_html}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MEDICINES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💊 Medicines":
    st.markdown('<div class="hero-header"><h1>💊 Medicine Schedule</h1><p>Add, edit and manage your medicines</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📋 Current Medicines</div>', unsafe_allow_html=True)
    if st.session_state.medicines:
        st.dataframe(pd.DataFrame(st.session_state.medicines), use_container_width=True, hide_index=True)
    else:
        st.info("No medicines yet. Add one below!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">➕ Add New Medicine</div>', unsafe_allow_html=True)
    time_options = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
    c1, c2, c3 = st.columns(3)
    with c1: new_name    = st.text_input("Medicine Name", placeholder="e.g. Metformin")
    with c2: new_time    = st.selectbox("Time", time_options)
    with c3: new_session = st.selectbox("Session", ["Morning", "Afternoon", "Night"])
    if st.button("➕ Add Medicine", type="primary"):
        if new_name.strip():
            st.session_state.medicines.append({
                "name": new_name.strip(), "time": new_time, "session": new_session
            })
            st.success(f"✅ {new_name} added!"); st.rerun()
        else:
            st.error("Please enter a medicine name.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.medicines:
        st.markdown('<div class="card"><div class="card-title">✏️ Edit or Remove Medicine</div>', unsafe_allow_html=True)
        names = [m["name"] for m in st.session_state.medicines]
        sel   = st.selectbox("Select medicine to edit or remove", names)
        idx   = next(i for i, m in enumerate(st.session_state.medicines) if m["name"] == sel)
        med   = st.session_state.medicines[idx]
        c1, c2, c3 = st.columns(3)
        with c1: e_name = st.text_input("Name", value=med["name"], key="en")
        with c2:
            e_time = st.selectbox("Time", time_options,
                index=time_options.index(med["time"]) if med["time"] in time_options else 0, key="et")
        with c3:
            e_sess = st.selectbox("Session", ["Morning", "Afternoon", "Night"],
                index=["Morning", "Afternoon", "Night"].index(med["session"]), key="es")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Changes", type="primary"):
                st.session_state.medicines[idx] = {"name": e_name, "time": e_time, "session": e_sess}
                st.success("✅ Updated!"); st.rerun()
        with c2:
            if st.button("🗑️ Remove Medicine"):
                st.session_state.medicines.pop(idx)
                st.success(f"Removed {sel}"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# REMINDERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⏰ Reminders":
    st.markdown('<div class="hero-header"><h1>⏰ Reminders</h1><p>Start and manage WhatsApp reminders</p></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sandbox-box">
        <strong>📱 Every contact must do this ONCE before receiving messages:</strong><br/><br/>
        1. Open WhatsApp on their phone<br/>
        2. Send this exact message to <strong>+14155238886</strong>:<br/><br/>
        <code>join machinery-final</code><br/><br/>
        3. Wait for Twilio's confirmation reply — done! ✅
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🔔 Reminder Control</div>', unsafe_allow_html=True)
    st.markdown(f"**Status:** {'🟢 Active' if st.session_state.reminder_active else '🔴 Inactive'}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Start Reminders", type="primary", disabled=st.session_state.reminder_active):
            if not st.session_state.family_numbers:
                st.error("⚠️ Add contacts in Family Contacts first!")
            else:
                st.session_state.reminder_active = True
                threading.Thread(target=reminder_loop, daemon=True).start()
                st.success("✅ Reminders started!"); st.rerun()
    with c2:
        if st.button("⏹️ Stop Reminders", disabled=not st.session_state.reminder_active):
            st.session_state.reminder_active = False
            st.warning("Reminders stopped."); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📅 Current Schedule</div>', unsafe_allow_html=True)
    sessions = {}
    for med in st.session_state.medicines:
        sessions.setdefault(f"{med['session']} — {med['time']}", []).append(med["name"])
    for label, meds in sessions.items():
        pills = "".join(f'<span class="pill-tag">{m}</span>' for m in meds)
        st.markdown(f"<p>⏰ <strong>{label}</strong><br/>{pills}</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🧪 Send Test Message</div>', unsafe_allow_html=True)
    if st.button("📤 Send Test WhatsApp"):
        ok, msg = send_whatsapp(f"👋 Hello {st.session_state.user_name}! MediCare reminder is working perfectly. ✅")
        st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FAMILY CONTACTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👨‍👩‍👧 Family Contacts":
    st.markdown('<div class="hero-header"><h1>👨‍👩‍👧 Family Contacts</h1><p>Everyone who receives reminders</p></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sandbox-box">
        <strong>📱 Every person on this list must do this ONCE:</strong><br/><br/>
        1. Open WhatsApp on their phone<br/>
        2. Send this exact message to <strong>+14155238886</strong>:<br/><br/>
        <code>join machinery-final</code><br/><br/>
        3. Wait for Twilio's confirmation reply — then they are connected! ✅
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📱 Current Contacts</div>', unsafe_allow_html=True)
    if st.session_state.family_numbers:
        for i, num in enumerate(st.session_state.family_numbers):
            c1, c2 = st.columns([5, 1])
            with c1: st.markdown(f"📱 `{num}`")
            with c2:
                if st.button("🗑️", key=f"d_{i}"):
                    st.session_state.family_numbers.pop(i); st.rerun()
    else:
        st.info("No contacts yet. Add one below.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">➕ Add Family Member</div>', unsafe_allow_html=True)
    st.markdown("Include country code — **+919876543210** (India) or **+447911123456** (UK)")
    st.info("📱 Remind them: Send **join machinery-final** to **+14155238886** on WhatsApp first!")
    new_num = st.text_input("WhatsApp Number", placeholder="+919876543210")
    if st.button("➕ Add Number", type="primary"):
        if new_num.strip().startswith("+"):
            if new_num.strip() not in st.session_state.family_numbers:
                st.session_state.family_numbers.append(new_num.strip())
                st.success("✅ Added!"); st.rerun()
            else:
                st.warning("Already in the list!")
        else:
            st.error("Must start with + and country code. Example: +919876543210")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📢 Message All Contacts</div>', unsafe_allow_html=True)
    msg_text = st.text_area("Message", placeholder="Type your message here...")
    if st.button("📤 Send to All", type="primary"):
        if msg_text.strip():
            ok, res = send_whatsapp(msg_text.strip())
            st.success(f"✅ {res}") if ok else st.error(f"❌ {res}")
        else:
            st.error("Please type a message first.")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 History":
    st.markdown('<div class="hero-header"><h1>📋 Intake History</h1><p>Your complete medication record</p></div>', unsafe_allow_html=True)

    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        c1, c2 = st.columns(2)
        with c1: f_status = st.selectbox("Filter Status", ["All", "Taken", "Missed"])
        with c2:
            sess_list = ["All"] + (list(df["Session"].unique()) if "Session" in df.columns else [])
            f_session = st.selectbox("Filter Session", sess_list)
        filtered = df.copy()
        if f_status  != "All": filtered = filtered[filtered["status"]  == f_status]
        if f_session != "All" and "Session" in filtered.columns:
            filtered = filtered[filtered["Session"] == f_session]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Download as CSV",
                filtered.to_csv(index=False).encode("utf-8"),
                "medicine_history.csv", "text/csv", type="primary"
            )
        with c2:
            if st.button("🗑️ Clear All History"):
                st.session_state.history = []
                st.success("History cleared!"); st.rerun()
    else:
        st.info("No history yet. Record your intake on the Home page!")

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown('<div class="hero-header"><h1>⚙️ Settings</h1><p>Update your profile</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">👤 User Profile</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: name = st.text_input("Your Name",         value=st.session_state.user_name)
    with c2: cond = st.text_input("Medical Condition", value=st.session_state.user_condition)
    with c3: gp   = st.text_input("Doctor's Name",     value=st.session_state.user_gp)
    if st.button("💾 Save Profile", type="primary"):
        st.session_state.user_name      = name
        st.session_state.user_condition = cond
        st.session_state.user_gp        = gp
        st.success("✅ Profile saved!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="card-title">⚠️ Medical Disclaimer</div>
        <p style="font-size:0.85rem;color:#6b7280;">
        This app is a reminder and tracking tool only.
        It does not replace professional medical advice.
        Always consult your doctor for medical decisions.
        In an emergency call 108 (India) or 999 (UK) immediately.
        </p>
    </div>""", unsafe_allow_html=True)