import streamlit as st
import pandas as pd
import random
import time
import os

# ---------------------------
# Constants
# ---------------------------
APP_URL = "https://riddleshield-puyslisekmtui29rqnrhpl.streamlit.app"
QUESTION_TIME = 30  # seconds per question
GAME_STATE_FILE = "game_state.csv"

# ---------------------------
# Riddles
# ---------------------------
riddles = {
    "I speak without a mouth and hear without ears. I have nobody, but I come alive with the wind. What am I?": "echo",
    "The more of me you take, the more you leave behind. What am I?": "footsteps",
    "What has to be broken before you can use it?": "egg",
    "I’m tall when I’m young, and I’m short when I’m old. What am I?": "candle",
    "What has keys but can’t open locks?": "piano"
}

# ---------------------------
# Initialize session state
# ---------------------------
if "players" not in st.session_state:
    st.session_state["players"] = []
if "player_answers" not in st.session_state:
    st.session_state["player_answers"] = {}  # {player_name: {q_idx: (answer, timestamp)}}

# ---------------------------
# Game state functions
# ---------------------------
def load_game_state():
    if os.path.exists(GAME_STATE_FILE):
        return pd.read_csv(GAME_STATE_FILE)
    else:
        df = pd.DataFrame([[0,0,0]], columns=["game_started","current_question","timestamp"])
        df.to_csv(GAME_STATE_FILE, index=False)
        return df

def save_game_state(game_started, current_question, timestamp):
    df = pd.DataFrame([[game_started, current_question, timestamp]], columns=["game_started","current_question","timestamp"])
    df.to_csv(GAME_STATE_FILE, index=False)

# ---------------------------
# QR code
# ---------------------------
def show_qr_code():
    player_url = f"{APP_URL}?role=Player"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={player_url}"
    st.image(qr_url, caption="📱 Scan to join the game", width=250)

# ---------------------------
# Detect role
# ---------------------------
query_params = st.experimental_get_query_params()
role = query_params.get("role", ["Host"])[0]  # default Host

# ---------------------------
# Leaderboard
# ---------------------------
def get_leaderboard():
    scores = {}
    for player, answers in st.session_state["player_answers"].items():
        total = 0
        for q_idx, (ans, ts) in answers.items():
            correct = riddles[list(riddles.keys())[q_idx]]
            start_time = ts
            if ans.strip().lower() == correct:
                total += max(0, QUESTION_TIME - int(ts - start_time))
        scores[player] = total
    return pd.DataFrame(list(scores.items()), columns=["Player","Score"]).sort_values(by="Score", ascending=False)

# ---------------------------
# Host View
# ---------------------------
if role == "Host":
    st.title("🎲 Tarun's Riddle Shield — Host Lobby")
    st.subheader("Host Panel")
    st.write("Project this QR code for classmates to join:")
    show_qr_code()

    st.subheader("Joined Players")
    if st.session_state["players"]:
        st.table(pd.DataFrame(st.session_state["players"], columns=["Name"]))
    else:
        st.info("No players yet.")

    # Load game state
    game_state = load_game_state()
    game_started = game_state.loc[0,"game_started"]

    if not game_started and st.button("🚀 Start Game"):
        save_game_state(1, 0, time.time())
        st.success("Game started!")

    if game_started:
        st.info("Game is live! Players can now see the questions.")

# ---------------------------
# Player View
# ---------------------------
else:
    st.title("🎲 Welcome to Tarun's Riddle Shield!")
    name = st.text_input("Enter your name")

    if st.button("Join Game") and name.strip():
        if name not in [p[0] for p in st.session_state["players"]]:
            st.session_state["players"].append([name])
            st.success(f"🎉 Welcome, {name}! Waiting for host to start...")
        elif not name.strip():
            st.error("Enter a valid name.")

    # Poll the shared game state
    game_state = load_game_state()
    game_started = game_state.loc[0,"game_started"]
    current_q_idx = int(game_state.loc[0,"current_question"])
    question_start_time = float(game_state.loc[0,"timestamp"])

    if not game_started:
        st.info("⏳ Waiting for host to start...")

    else:
        # Game loop
        if name.strip():
            if current_q_idx >= len(riddles):
                st.success("🏁 Quiz Finished!")
                st.subheader("Final Leaderboard")
                st.table(get_leaderboard())
            else:
                question = list(riddles.keys())[current_q_idx]
                st.subheader(f"Question {current_q_idx+1}")
                st.write(question)

                elapsed = int(time.time() - question_start_time)
                remaining = max(0, QUESTION_TIME - elapsed)
                st.info(f"⏳ Time remaining: {remaining}s")

                if name not in st.session_state["player_answers"]:
                    st.session_state["player_answers"][name] = {}

                ans_input = st.text_input("Your Answer:", key=f"{name}_{current_q_idx}", 
                                          value=st.session_state["player_answers"][name].get(current_q_idx, ("",0))[0])
                if st.button("Submit Answer", key=f"submit_{name}_{current_q_idx}"):
                    st.session_state["player_answers"][name][current_q_idx] = (ans_input, time.time())
                    st.success("Answer recorded!")

                # Auto reveal answer after time
                if elapsed >= QUESTION_TIME:
                    st.success(f"⏰ Time's up! Correct answer: {riddles[question]}")
                    st.subheader("Leaderboard")
                    st.table(get_leaderboard())

                    # Move to next question
                    save_game_state(1, current_q_idx + 1, time.time())
                    st.experimental_rerun()
