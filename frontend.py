import streamlit as st
import uuid
import time
import requests
from datetime import datetime
import streamlit.components.v1 as components
from backend import start_request, resume_with_edit
from db import (
    init_json_db,
    create_user,
    verify_user,
    get_user_history,
    save_session,
    load_session,
    clear_session
)

# ---------------------------------------
# INITIAL SETUP
# ---------------------------------------
st.set_page_config(page_title="SmartMail Studio", layout="wide")
init_json_db()

# ---------------------------------------
# SESSION STATE DEFAULTS
# ---------------------------------------
defaults = {
    "thread_id": str(uuid.uuid4()),
    "draft": "",
    "final_email": "",
    "logged_in": False,
    "username": "",
    "subject": "",
    "show_register": False,
    "page": "dashboard",
    "email_sent": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v



def get_greeting():
     hour = datetime.now().hour

     if 5 <= hour < 12:
      return "Good Morning"
     elif 12 <= hour < 17:
           return "Good Afternoon"
     elif 17 <= hour < 22:
            return "Good Evening"
     else:
               return "Good Night"
# ================== LOCATION BLOCK ==================
def get_location():
    try:
        ip_data = requests.get("https://api.ipify.org?format=json").json()
        ip = ip_data.get("ip")

        geo = requests.get(f"http://ip-api.com/json/{ip}").json()

        city = geo.get("city")
        country = geo.get("country")

        if city and country:
            return f"{city}, {country}"
        return "Unknown location"

    except:
        return "Location unavailable"
# ================== END LOCATION ==================
# ---------------------------------------
# GLOBAL STYLING
# ---------------------------------------
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #4A6CF7, #6FA8FF);
}

/* CARD */
.card {
    background: #111827;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0px 15px 40px rgba(0,0,0,0.4);
}

/* INPUT FIX */
.stTextInput > div > div {
    background: transparent !important;
    border: none !important;
}

.stTextInput input {
    border-radius: 10px;
    padding: 12px;
    background-color: #1f2937 !important;
    color: white !important;
    border: 1px solid #374151 !important;
}

label {
    color: #d1d5db !important;
}

/* BUTTON */
.stButton button {
    background: linear-gradient(135deg, #4A6CF7, #3b5bdb);
    color: white;
    border-radius: 10px;
    padding: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------
# 🔥 LIVE CLOCK (TOP RIGHT - NO REFRESH)
# ---------------------------------------
components.html("""
<script>
const existing = window.parent.document.getElementById("global-clock");
if (!existing) {

    const clock = window.parent.document.createElement("div");
    clock.id = "global-clock";

    clock.style.position = "fixed";
    clock.style.top = "70px";
    clock.style.right = "40px";
    clock.style.width = "140px";
    clock.style.height = "140px";
    clock.style.borderRadius = "50%";
    clock.style.background = "rgba(0,0,0,0.4)";
    clock.style.backdropFilter = "blur(8px)";
    clock.style.border = "3px solid rgba(255,255,255,0.2)";
    clock.style.zIndex = "9999";
    clock.style.display = "flex";
    clock.style.alignItems = "center";
    clock.style.justifyContent = "center";
    clock.style.color = "white";
    clock.style.fontFamily = "Arial";

    window.parent.document.body.appendChild(clock);

    const canvas = window.parent.document.createElement("canvas");
    canvas.width = 140;
    canvas.height = 140;
    clock.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    function drawClock() {
        const now = new Date();
        const sec = now.getSeconds();
        const min = now.getMinutes();
        const hr = now.getHours() % 12;

        ctx.clearRect(0, 0, 140, 140);

        ctx.translate(70, 70);

        // circle
        ctx.beginPath();
        ctx.arc(0, 0, 65, 0, Math.PI * 2);
        ctx.strokeStyle = "#aaa";
        ctx.lineWidth = 2;
        ctx.stroke();

        // numbers
        ctx.font = "bold 14px Arial";
        ctx.fillStyle = "white";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        for (let i = 1; i <= 12; i++) {
            let angle = (i * Math.PI) / 6;
            let x = Math.sin(angle) * 50;
            let y = -Math.cos(angle) * 50;
            ctx.fillText(i.toString(), x, y);
        }

        // hour hand
        ctx.rotate((hr * Math.PI) / 6 + (min * Math.PI) / 360);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -30);
        ctx.strokeStyle = "white";
        ctx.lineWidth = 4;
        ctx.stroke();
        ctx.rotate(-((hr * Math.PI) / 6 + (min * Math.PI) / 360));

        // minute hand
        ctx.rotate((min * Math.PI) / 30);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -45);
        ctx.strokeStyle = "#ddd";
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.rotate(-(min * Math.PI) / 30);

        // second hand
        ctx.rotate((sec * Math.PI) / 30);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -50);
        ctx.strokeStyle = "red";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.rotate(-(sec * Math.PI) / 30);

        ctx.setTransform(1, 0, 0, 1, 0, 0);
    }

    setInterval(drawClock, 1000);
    drawClock();
}
</script>
""", height=0)


# ================== AVATAR BLOCK ==================
components.html(f"""
<script>
const existingAvatar = window.parent.document.getElementById("user-avatar");
if (!existingAvatar) {{

    const initials = "{st.session_state.username[:2].upper()}";

    const avatar = window.parent.document.createElement("div");
    avatar.id = "user-avatar";

    avatar.innerHTML = initials;

    avatar.style.position = "fixed";
    avatar.style.top = "70px";
    avatar.style.right = "200px";
    avatar.style.width = "45px";
    avatar.style.height = "45px";
    avatar.style.borderRadius = "50%";
    avatar.style.background = "#4A6CF7";
    avatar.style.color = "white";
    avatar.style.display = "flex";
    avatar.style.alignItems = "center";
    avatar.style.justifyContent = "center";
    avatar.style.fontWeight = "600";
    avatar.style.fontSize = "16px";
    avatar.style.zIndex = "9999";
    avatar.style.boxShadow = "0px 4px 15px rgba(0,0,0,0.4)";

    window.parent.document.body.appendChild(avatar);
}}
</script>
""", height=0)
# ================== END AVATAR ==================
# ---------------------------------------
# AUTH UI
# ---------------------------------------
def render_auth_ui():

    st.markdown("<h1 style='text-align:center; color:white;'>📧 SmartMail Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#c7d2fe;'>AI-Powered Email Writing Assistant</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])

    with left:
        st.image("assets/robot.png", use_container_width=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if not st.session_state.show_register:
            st.markdown("### Login to SmartMail Studio")

            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")

            if st.button("Login"):
                if verify_user(user, pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    save_session(user)
                    st.rerun()
                else:
                    st.error("Invalid credentials")

            if st.button("Create Account"):
                st.session_state.show_register = True
                st.rerun()

        else:
            st.markdown("### Create Account")

            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")

            if st.button("Create Account"):
                if create_user(new_user, new_pass):
                    st.success("Account created! Please login.")
                    st.session_state.show_register = False
                    st.rerun()
                else:
                    st.error("Username already exists")

            if st.button("Back to Login"):
                st.session_state.show_register = False
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------
# RESTORE SESSION
# ---------------------------------------
sessions = load_session("*")
if not st.session_state.logged_in and sessions:
    for u, s in sessions.items():
        if time.time() < s.get("expires_at", 0):
            st.session_state.username = u
            st.session_state.logged_in = True
            break

# ---------------------------------------
# LOGIN PAGE
# ---------------------------------------
if not st.session_state.logged_in:
    render_auth_ui()
    st.stop()

# ---------------------------------------
# SIDEBAR
# ---------------------------------------
with st.sidebar:
    st.markdown("## 📧 SmartMail Studio")

    if st.button("🏠 Dashboard"):
        st.session_state.page = "dashboard"

    if st.button("✍️ Compose Email"):
        st.session_state.page = "compose"

    if st.button("📤 Sent Emails"):
        st.session_state.page = "sent"

    st.markdown("---")
    st.markdown(f"👤 {st.session_state.username}")

    if st.button("🚪 Logout"):
        clear_session(st.session_state.username)
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ---------------------------------------
# DASHBOARD
# ---------------------------------------
if st.session_state.page == "dashboard":

    greeting = get_greeting()
    location = get_location()

    st.markdown(f"# {greeting}, {st.session_state.username} 👋")
    st.caption(f"📍 Logged in from {location}")
    st.markdown("### AI-Powered Email Writing Assistant")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✍️ Compose Email")
        st.write("Generate professional emails instantly.")

        if st.button("Compose Email"):
            st.session_state.page = "compose"

    with col2:
        st.markdown("### 📤 Recent Emails")

        history = get_user_history(st.session_state.username)

        if history:
            for rec in history[:3]:
                st.markdown(f"**{rec['subject']}**")
                st.caption(rec["to_addrs"])
        else:
            st.info("No emails yet.")

# ---------------------------------------
# COMPOSE PAGE
# ---------------------------------------
elif st.session_state.page == "compose":

    st.title("✍️ Generate Email")

    request = st.text_area("Describe your email")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate"):
            with st.spinner("Generating..."):
                res = start_request(
                    request,
                    st.session_state.thread_id,
                    st.session_state.username
                )

            if "__interrupt__" in res:
                vals = res["__interrupt__"][0].value
                st.session_state.draft = vals.get("draft_email") or vals.get("draft", "")
                st.session_state.subject = vals.get("subject", "")
            else:
                st.session_state.draft = res.get("draft", "")
                st.session_state.subject = res.get("subject", "")

    with col2:
        if st.button("Clear"):
            st.session_state.draft = ""
            st.session_state.subject = ""

    if st.session_state.draft:
        st.subheader("Review Email")

        subject = st.text_input("Subject", value=st.session_state.subject)
        body = st.text_area("Edit Email", value=st.session_state.draft, height=250)
        recipients = st.text_input("Recipients")

        if st.button("Send Email"):
            rec_list = [r.strip() for r in recipients.split(",") if r.strip()]

            if not rec_list:
                st.error("Enter at least one recipient")
            else:
                try:
                    resume_with_edit(
                        body,
                        st.session_state.thread_id,
                        rec_list,
                        subject,
                        "",
                        st.session_state.username
                    )

                    st.success("Email sent!")

                    st.session_state.draft = ""
                    st.session_state.subject = ""
                    st.session_state.thread_id = str(uuid.uuid4())

                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

# ---------------------------------------
# SENT EMAILS PAGE
# ---------------------------------------
elif st.session_state.page == "sent":

    st.title("📤 Sent Emails")

    history = get_user_history(st.session_state.username)

    if not history:
        st.info("No emails yet.")
    else:
        for rec in history:
            st.markdown(f"### {rec['subject']}")
            st.caption(f"To: {rec['to_addrs']}")

            with st.expander("View Email"):
                st.code(rec["body"])