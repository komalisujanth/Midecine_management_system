import streamlit as st
import pandas as pd
import time
import threading
import hashlib
from datetime import datetime
from twilio.rest import Client
from supabase import create_client, Client as SupabaseClient

# ══════════════════════════════════════════════════════════════════════════════
# CREDENTIALS — all stored in Streamlit Secrets, nothing hardcoded here
# ══════════════════════════════════════════════════════════════════════════════
TWILIO_SID   = st.secrets["TWILIO_SID"]
TWILIO_TOKEN = st.secrets["TWILIO_TOKEN"]
TWILIO_FROM  = "whatsapp:+14155238886"
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #e8edf5;
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

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def db_get_user(email):
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None
    except: return None

def db_create_user(name, email, phone, age, sex, password, condition, gp):
    try:
        supabase.table("users").insert({
            "name": name, "email": email, "phone": phone,
            "age": age, "sex": sex, "password": hash_password(password),
            "condition": condition, "gp": gp
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}"); return False

def db_update_user(email, data):
    try:
        supabase.table("users").update(data).eq("email", email).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}"); return False

def db_get_medicines(email):
    try:
        res = supabase.table("medicines").select("*").eq("mail", email).execute()
        return res.data or []
    except: return []

def db_add_medicine(email, name, time_val, session):
    try:
        supabase.table("medicines").insert({
            "mail": email, "name": name, "time": time_val, "session": session
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}"); return False

def db_update_medicine(med_id, name, time_val, session):
    try:
        supabase.table("medicines").update({
            "name": name, "time": time_val, "session": session
        }).eq("id", med_id).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}"); return False

def db_delete_medicine(med_id):
    try:
        supabase.table("medicines").delete().eq("id", med_id).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}"); return False

def db_get_family_numbers(email):
    try:
        res = supabase.table("users").select("phone").eq("email", email).execute()
        if res.data and res.data[0].get("phone"):
            return [n.strip() for n in res.data[0]["phone"].split(",") if n.strip()]
        return []
    except: return []

def db_save_family_numbers(email, numbers):
    try:
        supabase.table("users").update({"phone": ",".join(numbers)}).eq("email", email).execute()
        return True
    except: return False

def db_add_history(email, session, medicines, status, notes):
    try:
        supabase.table("history").insert({
            "mail": email,
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session": session, "medicines": medicines,
            "status": status, "notes": notes
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}"); return False

def db_get_history(email):
    try:
        res = supabase.table("history").select("*").eq("mail", email).execute()
        return res.data or []
    except: return []

def db_clear_history(email):
    try:
        supabase.table("history").delete().eq("mail", email).execute()
        return True
    except: return False

def send_whatsapp(message, numbers=None):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        targets = numbers or st.session_state.get("family_numbers", [])
        if not targets:
            return False, "No contacts added. Go to Family Contacts page."
        for num in targets:
            wa = num if num.startswith("whatsapp:") else f"whatsapp:{num}"
            client.messages.create(to=wa, from_=TWILIO_FROM, body=message)
        return True, f"Sent to {len(targets)} number(s)"
    except Exception as e:
        return False, str(e)

def reminder_loop():
    sent_today = set()
    while st.session_state.get("reminder_active", False):
        now   = datetime.now().strftime("%H:%M")
        today = datetime.now().strftime("%Y-%m-%d")
        key   = f"{today}_{now}"
        if key not in sent_today:
            medicines = st.session_state.get("medicines", [])
            for med in medicines:
                if med["time"] == now:
                    meds_now  = list({m["name"] for m in medicines if m["time"] == now})
                    user_name = st.session_state.get("user", {}).get("name", "")
                    send_whatsapp(
                        f"💊 MEDICINE REMINDER\n"
                        f"Hi {user_name}! Time for your {med['session']} medicines.\n"
                        f"Medicines: {', '.join(meds_now)}\nStay healthy! ❤️"
                    )
                    sent_today.add(key); break
        time.sleep(30)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for key, val in {
    "logged_in": False, "user": {}, "medicines": [],
    "family_numbers": [], "reminder_active": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ══════════════════════════════════════════════════════════════════════════════
# AUTH — LOGIN / REGISTER
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <h1 style="font-size:2.5rem; font-weight:800; color:#1e3a5f;">💊 MediCare</h1>
        <p style="color:#6b7280; font-size:1rem;">Your personal medicine reminder</p>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        with tab1:
            st.markdown("### Welcome back!")
            login_email = st.text_input("Email", placeholder="your@email.com", key="le")
            login_pass  = st.text_input("Password", type="password", placeholder="your password", key="lp")
            if st.button("Login →", type="primary", use_container_width=True):
                if login_email and login_pass:
                    user = db_get_user(login_email.strip().lower())
                    if user and user["password"] == hash_password(login_pass):
                        st.session_state.logged_in      = True
                        st.session_state.user           = user
                        st.session_state.medicines      = db_get_medicines(login_email.strip().lower())
                        st.session_state.family_numbers = db_get_family_numbers(login_email.strip().lower())
                        st.success(f"Welcome back, {user['name']}! 👋")
                        time.sleep(1); st.rerun()
                    else:
                        st.error("❌ Wrong email or password.")
                else:
                    st.error("Please enter email and password.")

        with tab2:
            st.markdown("### Create your account")
            c1, c2 = st.columns(2)
            with c1:
                reg_name  = st.text_input("Full Name",           placeholder="Dave",             key="rn")
                reg_email = st.text_input("Email",               placeholder="dave@email.com",   key="re")
                reg_phone = st.text_input("WhatsApp Number",     placeholder="+919876543210",    key="rp")
                reg_age   = st.number_input("Age", min_value=1, max_value=120, value=30,         key="ra")
            with c2:
                reg_sex   = st.selectbox("Sex", ["Male","Female","Other"],                       key="rs")
                reg_cond  = st.text_input("Medical Condition",   placeholder="e.g. Diabetic",   key="rc")
                reg_gp    = st.text_input("Doctor's Name",       placeholder="Dr. Satish",       key="rg")
                reg_pass  = st.text_input("Password",            type="password",                key="rpw")
                reg_pass2 = st.text_input("Confirm Password",    type="password",                key="rpw2")

            if st.button("Create Account →", type="primary", use_container_width=True):
                if not all([reg_name, reg_email, reg_phone, reg_cond, reg_gp, reg_pass]):
                    st.error("Please fill in all fields.")
                elif reg_pass != reg_pass2:
                    st.error("Passwords don't match!")
                elif not reg_phone.startswith("+"):
                    st.error("Phone must start with + and country code. Example: +919876543210")
                elif db_get_user(reg_email.strip().lower()):
                    st.error("An account with this email already exists.")
                else:
                    ok = db_create_user(reg_name, reg_email.strip().lower(), reg_phone,
                                        reg_age, reg_sex, reg_pass, reg_cond, reg_gp)
                    if ok:
                        st.success("✅ Account created! Please log in.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
user = st.session_state.user

with st.sidebar:
    st.markdown("## 💊 MediCare")
    st.markdown(f"👤 **{user.get('name','')}**")
    st.markdown("---")
    page = st.radio("Navigate", [
        "🏠 Home", "💊 Medicines", "⏰ Reminders",
        "👨‍👩‍👧 Family Contacts", "📋 History", "⚙️ Profile",
    ])
    st.markdown("---")
    history = db_get_history(user["email"])
    taken   = sum(1 for h in history if h.get("status") == "Taken")
    missed  = len(history) - taken
    st.markdown(f"**✅ Taken:** {taken}\n\n**❌ Missed:** {missed}")
    st.markdown("---")
    st.markdown(f"**Reminders:** {'🟢 Active' if st.session_state.reminder_active else '🔴 Inactive'}")
    st.markdown("---")
    if st.button("🚪 Logout"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ── HOME ───────────────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.markdown(f'<div class="hero-header"><h1>💊 MediCare Reminder</h1><p>Hello {user.get("name","")}! Stay on top of your health journey.</p></div>', unsafe_allow_html=True)

    medicines = db_get_medicines(user["email"])
    now_mins  = datetime.now().hour * 60 + datetime.now().minute
    upcoming  = sorted(
        [(int(m["time"].split(":")[0])*60 + int(m["time"].split(":")[1]), m)
         for m in medicines
         if int(m["time"].split(":")[0])*60 + int(m["time"].split(":")[1]) > now_mins],
        key=lambda x: x[0]
    )
    if upcoming:
        nxt      = upcoming[0][1]
        nxt_meds = list({m["name"] for m in medicines if m["time"] == nxt["time"]})
        st.markdown(f'<div class="alert-box">⏰ <strong>Next:</strong> {nxt["session"]} at {nxt["time"]} — {", ".join(nxt_meds)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box">✅ All medicines done for today!</div>', unsafe_allow_html=True)

    history = db_get_history(user["email"])
    total   = len(history)
    taken   = sum(1 for h in history if h.get("status") == "Taken")
    missed  = total - taken
    rate    = int(taken / total * 100) if total > 0 else 0
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box stat-green"><div class="stat-num">{taken}</div><div class="stat-lbl">Taken</div></div>
        <div class="stat-box stat-red">  <div class="stat-num">{missed}</div><div class="stat-lbl">Missed</div></div>
        <div class="stat-box stat-blue"> <div class="stat-num">{rate}%</div><div class="stat-lbl">Adherence</div></div>
        <div class="stat-box">           <div class="stat-num">{len(medicines)}</div><div class="stat-lbl">Medicines</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📋 Record Today\'s Intake</div>', unsafe_allow_html=True)
    if medicines:
        sessions = {}
        for med in medicines: sessions.setdefault(med["session"], []).append(med["name"])
        for session, meds in sessions.items():
            with st.expander(f"🕐 {session} — {', '.join(meds)}"):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Taken", key=f"t_{session}"):
                        db_add_history(user["email"], session, ", ".join(meds), "Taken", "Taken on time")
                        st.success("Recorded! ✅"); st.rerun()
                with c2:
                    if st.button("❌ Missed", key=f"m_{session}"):
                        db_add_history(user["email"], session, ", ".join(meds), "Missed", "Missed dose")
                        st.warning("Recorded as missed ⚠️"); st.rerun()
    else:
        st.info("No medicines yet. Go to 💊 Medicines to add some!")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="card"><div class="card-title">👤 My Info</div><p><strong>Name:</strong> {user.get("name","")}</p><p><strong>Condition:</strong> {user.get("condition","")}</p><p><strong>GP:</strong> {user.get("gp","")}</p><p><strong>Age:</strong> {user.get("age","")}</p></div>', unsafe_allow_html=True)
    with c2:
        nums      = st.session_state.family_numbers
        nums_html = "".join(f"<p>📱 {n}</p>" for n in nums) if nums else "<p>No contacts yet.</p>"
        st.markdown(f'<div class="card"><div class="card-title">📞 Family Contacts</div>{nums_html}</div>', unsafe_allow_html=True)

# ── MEDICINES ──────────────────────────────────────────────────────────────────
elif page == "💊 Medicines":
    st.markdown('<div class="hero-header"><h1>💊 Medicine Schedule</h1><p>Add, edit and manage your medicines</p></div>', unsafe_allow_html=True)

    medicines    = db_get_medicines(user["email"])
    time_options = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]

    st.markdown('<div class="card"><div class="card-title">📋 Your Medicines</div>', unsafe_allow_html=True)
    if medicines:
        for med in medicines:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
            with c1: st.markdown(f"💊 **{med['name']}**")
            with c2: st.markdown(f"🕐 {med['time']}")
            with c3: st.markdown(f"☀️ {med['session']}")
            with c4:
                if st.button("✏️", key=f"edit_{med['id']}"):
                    st.session_state[f"editing_{med['id']}"] = True
            with c5:
                if st.button("🗑️", key=f"del_{med['id']}"):
                    db_delete_medicine(med["id"])
                    st.success(f"Removed {med['name']}"); st.rerun()

            if st.session_state.get(f"editing_{med['id']}", False):
                with st.expander(f"✏️ Editing {med['name']}", expanded=True):
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1: e_name = st.text_input("Name", value=med["name"], key=f"en_{med['id']}")
                    with ec2:
                        e_time = st.selectbox("Time", time_options,
                            index=time_options.index(med["time"]) if med["time"] in time_options else 0,
                            key=f"et_{med['id']}")
                    with ec3:
                        e_sess = st.selectbox("Session", ["Morning","Afternoon","Night"],
                            index=["Morning","Afternoon","Night"].index(med["session"]),
                            key=f"es_{med['id']}")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        if st.button("💾 Save", key=f"save_{med['id']}", type="primary"):
                            db_update_medicine(med["id"], e_name, e_time, e_sess)
                            del st.session_state[f"editing_{med['id']}"]
                            st.success("✅ Updated!"); st.rerun()
                    with sc2:
                        if st.button("Cancel", key=f"cancel_{med['id']}"):
                            del st.session_state[f"editing_{med['id']}"]
                            st.rerun()
    else:
        st.info("No medicines yet. Add one below!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">➕ Add New Medicine</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: new_name    = st.text_input("Medicine Name", placeholder="e.g. Metformin")
    with c2: new_time    = st.selectbox("Time", time_options)
    with c3: new_session = st.selectbox("Session", ["Morning", "Afternoon", "Night"])
    if st.button("➕ Add Medicine", type="primary"):
        if new_name.strip():
            db_add_medicine(user["email"], new_name.strip(), new_time, new_session)
            st.success(f"✅ {new_name} added!"); st.rerun()
        else:
            st.error("Please enter a medicine name.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── REMINDERS ─────────────────────────────────────────────────────────────────
elif page == "⏰ Reminders":
    st.markdown('<div class="hero-header"><h1>⏰ Reminders</h1><p>Start and manage WhatsApp reminders</p></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sandbox-box">
        <strong>📱 Every contact must do this ONCE:</strong><br/><br/>
        1. Open WhatsApp → Send <code>join machinery-final</code> to <strong>+14155238886</strong><br/>
        2. Wait for Twilio confirmation reply ✅
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🔔 Reminder Control</div>', unsafe_allow_html=True)
    st.markdown(f"**Status:** {'🟢 Active' if st.session_state.reminder_active else '🔴 Inactive'}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Start Reminders", type="primary", disabled=st.session_state.reminder_active):
            if not st.session_state.family_numbers:
                st.error("⚠️ Add contacts in Family Contacts first!")
            else:
                st.session_state.medicines       = db_get_medicines(user["email"])
                st.session_state.reminder_active = True
                threading.Thread(target=reminder_loop, daemon=True).start()
                st.success("✅ Reminders started!"); st.rerun()
    with c2:
        if st.button("⏹️ Stop Reminders", disabled=not st.session_state.reminder_active):
            st.session_state.reminder_active = False
            st.warning("Reminders stopped."); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    medicines = db_get_medicines(user["email"])
    st.markdown('<div class="card"><div class="card-title">📅 Current Schedule</div>', unsafe_allow_html=True)
    if medicines:
        sessions = {}
        for med in medicines: sessions.setdefault(f"{med['session']} — {med['time']}", []).append(med["name"])
        for label, meds in sessions.items():
            pills = "".join(f'<span class="pill-tag">{m}</span>' for m in meds)
            st.markdown(f"<p>⏰ <strong>{label}</strong><br/>{pills}</p>", unsafe_allow_html=True)
    else:
        st.info("No medicines added yet.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🧪 Test Message</div>', unsafe_allow_html=True)
    if st.button("📤 Send Test WhatsApp"):
        ok, msg = send_whatsapp(f"👋 Hello {user.get('name','')}! MediCare reminder is working. ✅")
        st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
    st.markdown('</div>', unsafe_allow_html=True)

# ── FAMILY CONTACTS ────────────────────────────────────────────────────────────
elif page == "👨‍👩‍👧 Family Contacts":
    st.markdown('<div class="hero-header"><h1>👨‍👩‍👧 Family Contacts</h1><p>Everyone who receives reminders</p></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sandbox-box">
        <strong>📱 Every person must do this ONCE:</strong><br/><br/>
        1. Open WhatsApp → Send <code>join machinery-final</code> to <strong>+14155238886</strong><br/>
        2. Wait for confirmation reply ✅
    </div>""", unsafe_allow_html=True)

    numbers = db_get_family_numbers(user["email"])
    st.session_state.family_numbers = numbers

    st.markdown('<div class="card"><div class="card-title">📱 Current Contacts</div>', unsafe_allow_html=True)
    if numbers:
        for i, num in enumerate(numbers):
            c1, c2 = st.columns([5, 1])
            with c1: st.markdown(f"📱 `{num}`")
            with c2:
                if st.button("🗑️", key=f"d_{i}"):
                    numbers.pop(i)
                    db_save_family_numbers(user["email"], numbers)
                    st.session_state.family_numbers = numbers
                    st.rerun()
    else:
        st.info("No contacts yet.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">➕ Add Family Member</div>', unsafe_allow_html=True)
    st.markdown("Include country code — **+919876543210** (India) or **+447911123456** (UK)")
    st.info("📱 Remind them: Send **join machinery-final** to **+14155238886** on WhatsApp first!")
    new_num = st.text_input("WhatsApp Number", placeholder="+919876543210")
    if st.button("➕ Add Number", type="primary"):
        if new_num.strip().startswith("+"):
            if new_num.strip() not in numbers:
                numbers.append(new_num.strip())
                db_save_family_numbers(user["email"], numbers)
                st.session_state.family_numbers = numbers
                st.success("✅ Added!"); st.rerun()
            else: st.warning("Already in the list!")
        else: st.error("Must start with + and country code. Example: +919876543210")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📢 Message All Contacts</div>', unsafe_allow_html=True)
    msg_text = st.text_area("Message", placeholder="Type your message here...")
    if st.button("📤 Send to All", type="primary"):
        if msg_text.strip():
            ok, res = send_whatsapp(msg_text.strip(), numbers)
            st.success(f"✅ {res}") if ok else st.error(f"❌ {res}")
        else: st.error("Please type a message first.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── HISTORY ────────────────────────────────────────────────────────────────────
elif page == "📋 History":
    st.markdown('<div class="hero-header"><h1>📋 Intake History</h1><p>Your complete medication record</p></div>', unsafe_allow_html=True)

    history = db_get_history(user["email"])
    if history:
        df           = pd.DataFrame(history)
        display_cols = ["date_time","session","medicines","status","notes"]
        df           = df[[c for c in display_cols if c in df.columns]]

        c1, c2 = st.columns(2)
        with c1: f_status = st.selectbox("Filter Status", ["All","Taken","Missed"])
        with c2:
            sess_list = ["All"] + (list(df["session"].unique()) if "session" in df.columns else [])
            f_session = st.selectbox("Filter Session", sess_list)

        filtered = df.copy()
        if f_status  != "All": filtered = filtered[filtered["status"]  == f_status]
        if f_session != "All" and "session" in filtered.columns:
            filtered = filtered[filtered["session"] == f_session]

        st.dataframe(filtered, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇️ Download CSV",
                filtered.to_csv(index=False).encode("utf-8"),
                "medicine_history.csv", "text/csv", type="primary")
        with c2:
            if st.button("🗑️ Clear All History"):
                db_clear_history(user["email"])
                st.success("Cleared!"); st.rerun()
    else:
        st.info("No history yet. Record your intake on the Home page!")

# ── PROFILE ────────────────────────────────────────────────────────────────────
elif page == "⚙️ Profile":
    st.markdown('<div class="hero-header"><h1>⚙️ My Profile</h1><p>Update your personal details</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">👤 Personal Information</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        p_name  = st.text_input("Full Name",       value=user.get("name",""))
        p_email = st.text_input("Email",           value=user.get("email",""), disabled=True)
        p_phone = st.text_input("WhatsApp Number", value=user.get("phone",""))
        p_age   = st.number_input("Age", min_value=1, max_value=120, value=int(user.get("age") or 30))
    with c2:
        p_sex  = st.selectbox("Sex", ["Male","Female","Other"],
            index=["Male","Female","Other"].index(user.get("sex","Male")) if user.get("sex") in ["Male","Female","Other"] else 0)
        p_cond = st.text_input("Medical Condition", value=user.get("condition",""))
        p_gp   = st.text_input("Doctor's Name",     value=user.get("gp",""))

    if st.button("💾 Save Profile", type="primary"):
        db_update_user(user["email"], {
            "name": p_name, "phone": p_phone, "age": p_age,
            "sex": p_sex, "condition": p_cond, "gp": p_gp
        })
        st.session_state.user.update({
            "name": p_name, "phone": p_phone, "age": p_age,
            "sex": p_sex, "condition": p_cond, "gp": p_gp
        })
        st.success("✅ Profile updated!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🔑 Change Password</div>', unsafe_allow_html=True)
    old_pass  = st.text_input("Current Password",     type="password")
    new_pass  = st.text_input("New Password",         type="password")
    new_pass2 = st.text_input("Confirm New Password", type="password")
    if st.button("🔑 Update Password", type="primary"):
        if user["password"] != hash_password(old_pass):
            st.error("❌ Current password is wrong.")
        elif new_pass != new_pass2:
            st.error("❌ New passwords don't match.")
        elif len(new_pass) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            db_update_user(user["email"], {"password": hash_password(new_pass)})
            st.session_state.user["password"] = hash_password(new_pass)
            st.success("✅ Password updated!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card"><div class="card-title">⚠️ Medical Disclaimer</div>
    <p style="font-size:0.85rem;color:#6b7280;">
    This app is a reminder and tracking tool only. It does not replace professional medical advice.
    Always consult your doctor. In an emergency call 108 (India) or 999 (UK) immediately.
    </p></div>""", unsafe_allow_html=True)