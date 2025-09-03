import streamlit as st
import pandas as pd
import random
import os
import time

# ---------------------------
# Constants
# ---------------------------
APP_URL = "https://riddleshield-puyslisekmtui29rqnrhpl.streamlit.app"
LEADERBOARD_FILE = "leaderboard.csv"
GAME_STATE_FILE = "game_state.csv"

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
# Game State Functions
# ---------------------------
def is_game_started():
    if os.path.exists(GAME_STATE_FILE):
        df = pd.read_csv(GAME_STATE_FILE)
        return df["started"][0] == 1
    else:
        return False

def set_game_started():
    df = pd.DataFrame({"started": [1]})
    df.to_csv(GAME_STATE_FILE, index=False)

# ---------------------------
# QR Code Function
# ---------------------------
def show_qr_code():
    player_url = f"{APP_URL}?role=Player"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={player_url}"
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
if "scores" not in st.session_state:
    st.session_state["scores"] = {}
if "current_player" not in st.session_state:
    st.session_state["current_player"] = None
if "last_player_count" not in st.session_state:
    st.session_state["last_player_count"] = 0  # for flash notification

# ---------------------------
# Game Functions
# ---------------------------
def play_game(player_name):
    score = 0
    for riddle, answer in random.sample(list(riddles.items()), 3):
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
# Detect role
# ---------------------------
query_params = st.experimental_get_query_params()
role = query_params.get("role", ["Host"])[0]  # default Host

# ---------------------------
# Host View
# ---------------------------
if role == "Host":
    st.title("🎲 Tarun's Riddle Shield — Host Lobby")
    st.subheader("Host Panel")
    st.write("Project this QR code for classmates to join:")
    show_qr_code()

    st.subheader("Joined Players (Real-Time)")
    players_container = st.empty()

    # Real-time lobby refresh
    while not is_game_started():
        # Update joined players table
        if st.session_state["players"]:
            players_container.table(pd.DataFrame(st.session_state["players"], columns=["Name"]))
        else:
            players_container.info("No players yet. Waiting...")

        # Flash notification if new player joined
        if len(st.session_state["players"]) > st.session_state["last_player_count"]:
            new_player = st.session_state["players"][-1][0]
            st.toast(f"🎉 New player joined: {new_player}!")  # Streamlit >=1.23
            st.session_state["last_player_count"] = len(st.session_state["players"])

        if st.button("🚀 Start Game"):
            set_game_started()
            st.success("Game started! Players can now see questions.")
            break
        time.sleep(1)

# ---------------------------
# Player View
# ---------------------------
else:
    st.title("🎲 Welcome to Tarun's Riddle Shield!")
    st.write("Enter your name to join the game:")

    name = st.text_input("Your Name")
    if st.button("Join Game"):
        if name.strip():
            if name not in [p[0] for p in st.session_state["players"]]:
                st.session_state["players"].append([name])
            st.success(f"Welcome, {name}! Waiting for host to start...")
        else:
            st.error("Please enter a valid name.")

    # Real-time joined players notification
    joined_container = st.empty()
    if st.session_state["players"]:
        joined_container.info(
            "Players currently joined: " + ", ".join([p[0] for p in st.session_state["players"]])
        )

    # Flash notification if new player joined (players see other players too)
    if len(st.session_state["players"]) > st.session_state["last_player_count"]:
        new_player = st.session_state["players"][-1][0]
        st.toast(f"🎉 New player joined: {new_player}!")
        st.session_state["last_player_count"] = len(st.session_state["players"])

    # Check if game started by host
    if is_game_started():
        st.success("✅ The host has started the game!")
        if st.session_state["current_player"] is None:
            st.session_state["current_player"] = name
        play_game(st.session_state["current_player"])
