import streamlit as st
import pandas as pd
import random
import os

# ---------------------------
# Constants
# ---------------------------
APP_URL = "https://riddleshield-puyslisekmtui29rqnrhpl.streamlit.app"  # Your public app URL
LEADERBOARD_FILE = "leaderboard.csv"

# ---------------------------
# Leaderboard Functions
# ---------------------------
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        return pd.read_csv(LEADERBOARD_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Score"])

def save_leaderboard(df):
    df.to_csv(LEADERBOARD_FILE, index=False)

def update_leaderboard(name, score):
    df = load_leaderboard()
    if name in df["Name"].values:
        df.loc[df["Name"] == name, "Score"] += score
    else:
        new_row = pd.DataFrame([[name, score]], columns=["Name", "Score"])
        df = pd.concat([df, new_row], ignore_index=True)
    save_leaderboard(df)

def show_leaderboard():
    df = load_leaderboard()
    if df.empty:
        st.write("No scores yet.")
    else:
        st.subheader("🏆 Leaderboard")
        st.table(df.sort_values(by="Score", ascending=False).reset_index(drop=True))

# ---------------------------
# QR Code Function (Option 2)
# ---------------------------
def show_qr_code():
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={APP_URL}"
    st.image(qr_url, caption="📱 Scan to join the game", width=250)

# ---------------------------
# Game Data
# ---------------------------
riddles = {
    "I speak without a mouth and hear without ears. I have nobody, but I come alive with the wind. What am I?": "echo",
    "The more of me you take, the more you leave behind. What am I?": "footsteps",
    "What has to be broken before you can use it?": "egg",
    "I’m tall when I’m young, and I’m short when I’m old. What am I?": "candle",
    "What has keys but can’t open locks?": "piano"
}

# ---------------------------
# Session State
# ---------------------------
if "players" not in st.session_state:
    st.session_state["players"] = []
if "game_started" not in st.session_state:
    st.session_state["game_started"] = False
if "scores" not in st.session_state:
    st.session_state["scores"] = {}

# ---------------------------
# Game Functions
# ---------------------------
def play_game(player_name):
    score = 0
    for riddle, answer in random.sample(list(riddles.items()), 3):  # ask 3 random riddles
        st.write("🤔 Riddle: ", riddle)
        user_answer = st.text_input("Your Answer:", key=riddle + "_" + player_name)

        if st.button("Submit", key=riddle + "_submit_" + player_name):
            if user_answer.strip().lower() == answer:
                st.success("✅ Correct!")
                score += 1
            else:
                st.error(f"❌ Wrong! Correct answer: {answer}")

    st.write(f"**{player_name}, your final score: {score}**")
    update_leaderboard(player_name, score)
    show_leaderboard()

# ---------------------------
# Streamlit App Layout
# ---------------------------
st.title("🎲 Safety Riddle Game — Multiplayer Mode")

# Role selector (host or player)
role = st.sidebar.selectbox("Choose role", ["Host", "Player"])

# ---------------------------
# Host View
# ---------------------------
if role == "Host":
    st.header("👨‍🏫 Host Lobby")
    st.write("Project this QR code on the smart board for classmates to join:")
    show_qr_code()

    st.subheader("Joined Players")
    if st.session_state["players"]:
        st.table(pd.DataFrame(st.session_state["players"], columns=["Name"]))
    else:
        st.info("No players yet. Waiting...")

    if st.button("🚀 Start Game"):
        st.session_state["game_started"] = True
        st.success("Game started! Players can now see questions.")

# ---------------------------
# Player View
# ---------------------------
else:
    if not st.session_state["game_started"]:
        st.header("🙋 Enter Your Name to Join")
        name = st.text_input("Your Name")
        if st.button("Join"):
            if name.strip():
                if name not in [p[0] for p in st.session_state["players"]]:
                    st.session_state["players"].append([name])
                st.success(f"Welcome, {name}! Waiting for host to start...")
            else:
                st.error("Please enter a valid name.")
    else:
        st.success("✅ The host has started the game!")
        player_names = [p[0] for p in st.session_state["players"]]
        if role == "Player":
            # Each player plays individually
            if "current_player" not in st.session_state:
                st.session_state["current_player"] = name
            play_game(st.session_state["current_player"])
        show_leaderboard()
