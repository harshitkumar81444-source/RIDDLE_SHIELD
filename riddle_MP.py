import streamlit as st
import pandas as pd
import random
import time
import json
from pathlib import Path

# ---------------------------
# Constants
# ---------------------------
APP_URL = "https://riddleshield-puyslisekmtui29rqnrhpl.streamlit.app"
QUESTION_TIME = 30  # seconds per question
STATE_FILE = Path("game_state.json")

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
# Shared State Helpers
# ---------------------------
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "players": [],
        "game_started": False,
        "question_index": 0,
        "question_order": random.sample(list(riddles.keys()), len(riddles)),
        "player_answers": {},
        "question_start_times": {}
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ---------------------------
# Leaderboard Calculation
# ---------------------------
def get_leaderboard(state):
    scores = {}
    for player, answers in state["player_answers"].items():
        total = 0
        for q_idx, (ans, ts) in answers.items():
            correct = riddles[state["question_order"][q_idx]]
            if ans.strip().lower() == correct:
                start_time = state["question_start_times"].get(str(q_idx), ts)
                total += max(0, QUESTION_TIME - int(ts - start_time))
        scores[player] = total
    return pd.DataFrame(list(scores.items()), columns=["Player", "Score"]).sort_values(by="Score", ascending=False)

# ---------------------------
# QR Code for Host
# ---------------------------
def show_qr_code():
    player_url = f"{APP_URL}?role=Player"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={player_url}"
    st.image(qr_url, caption="📱 Scan to join the game", width=250)

# ---------------------------
# Detect Role
# ---------------------------
query_params = st.experimental_get_query_params()
role = query_params.get("role", ["Host"])[0]  # default Host

# ---------------------------
# Host View
# ---------------------------
if role == "Host":
    st.title("🎲 Tarun's Riddle Shield — Host Lobby")
    state = load_state()

    st.subheader("Host Panel")
    st.write("Project this QR code for classmates to join:")
    show_qr_code()

    st.subheader("Joined Players")
    if state["players"]:
        st.table(pd.DataFrame(state["players"], columns=["Name"]))
    else:
        st.info("No players yet.")

    # Start Game button
    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            state["game_started"] = True
            state["question_index"] = 0
            state["question_start_times"][str(0)] = time.time()
            save_state(state)
            st.success("Game started! Players can now see questions.")

    # Show current question if game started
    if state["game_started"]:
        q_idx = state["question_index"]
        if q_idx < len(state["question_order"]):
            st.subheader(f"📖 Current Question: {state['question_order'][q_idx]}")
        else:
            st.success("✅ Game Over!")

# ---------------------------
# Player View
# ---------------------------
else:
    st.title("🎲 Welcome to Tarun's Riddle Shield!")
    state = load_state()
    name = st.text_input("Enter your name")

    if st.button("Join Game"):
        if name.strip() and name not in [p[0] for p in state["players"]]:
            state["players"].append([name])
            save_state(state)
            st.success(f"🎉 Welcome, {name}! Waiting for host to start...")
        elif not name.strip():
            st.error("Enter a valid name.")

    if not state["game_started"]:
        st.info("⏳ Waiting for host to start...")
        st.stop()

    # Game loop
    q_idx = state["question_index"]
    if q_idx >= len(state["question_order"]):
        st.success("🏁 Quiz Finished!")
        st.subheader("Final Leaderboard")
        st.table(get_leaderboard(state))
    else:
        question = state["question_order"][q_idx]
        st.subheader(f"Question {q_idx +1}")
        st.write(question)

        # Timer
        if str(q_idx) not in state["question_start_times"]:
            state["question_start_times"][str(q_idx)] = time.time()
            save_state(state)

        elapsed = int(time.time() - state["question_start_times"][str(q_idx)])
        remaining = max(0, QUESTION_TIME - elapsed)
        st.info(f"⏳ Time remaining: {remaining}s")

        # Player answer
        if name not in state["player_answers"]:
            state["player_answers"][name] = {}
        ans_input = st.text_input("Your Answer:", key=f"{name}_{q_idx}", 
                                  value=state["player_answers"][name].get(str(q_idx), ("",0))[0])
        if st.button("Submit Answer", key=f"submit_{name}_{q_idx}"):
            state["player_answers"][name][str(q_idx)] = (ans_input, time.time())
            save_state(state)
            st.success("Answer recorded!")

        # Auto reveal after 30s
        if elapsed >= QUESTION_TIME:
            correct_answer = riddles[question]
            st.success(f"⏰ Time's up! Correct answer: {correct_answer}")
            st.subheader("Leaderboard")
            st.table(get_leaderboard(state))
            time.sleep(5)
            state["question_index"] += 1
            save_state(state)
            st.experimental_rerun()
