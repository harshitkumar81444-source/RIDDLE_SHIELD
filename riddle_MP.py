import streamlit as st
from tinydb import TinyDB, Query
import qrcode
import io

# Database setup
db = TinyDB("players.json")
Player = Query()

st.set_page_config(page_title="Safety Riddle Multiplayer", page_icon="🔥", layout="centered")

# --- Generate QR Code for joining ---
BASE_URL = "http://localhost:8501"   # 🔹 For local use
# Later change to your Streamlit Cloud URL, e.g. "https://yourapp.streamlit.app"

qr = qrcode.make(BASE_URL)
buf = io.BytesIO()
qr.save(buf, format="PNG")

# --- Sidebar for host ---
st.sidebar.title("Host Controls")
if st.sidebar.button("Reset Game"):
    db.truncate()
    st.sidebar.success("Game reset. All players removed.")

# --- Main App ---
st.title("🎮 Safety Riddle Game - Multiplayer")

# QR Display
st.subheader("📲 Scan to Join")
st.image(buf.getvalue(), width=200)
st.write("Or open:", BASE_URL)

# --- Player Join ---
with st.form("join_form"):
    name = st.text_input("Enter your name to join:")
    submit = st.form_submit_button("Join Game")

if submit and name.strip():
    if not db.search(Player.name == name):
        db.insert({"name": name, "score": 0})
        st.success(f"Welcome {name}! You joined the lobby.")
    else:
        st.warning("Name already taken. Try another.")

# --- Lobby ---
st.subheader("👥 Current Lobby")
players = db.all()
if players:
    for p in players:
        st.write(f"- {p['name']} (score: {p['score']})")
else:
    st.info("No players yet. Ask classmates to scan QR and join.")
