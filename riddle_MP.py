import streamlit as st
import pandas as pd
import random
import time
import os

# ---------------------------
# Constants
# ---------------------------
APP_URL = "https://riddleshield-puyslisekmtui29rqnrhpl.streamlit.app"
LEADERBOARD_FILE = "leaderboard.csv"
GAME_STATE_FILE = "game_state.csv"
QUESTION_TIME = 30  # seconds per question

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
questions = list(riddles.keys())

# ---------------------------
# Session State Initialization
# ---------------------------
if "players" not in st.session_state:
    st.session_state["players"] = []
if "joined_count" not in st.session_state:
    st.session_state["joined_count"] = 0
if "game_started" not in st.session_state:
    st.session_state["game_started"] = False
if "current_question_index" not in st.session_state:
    st.session_state["current_question_index"] = 0
if "question_start_time" not in st.session_state:
    st.session_state["question_start_time"] = None
if "player_answers" not in st.session_state:
    st.session_state["player_answers"] = {}  # {player_name: {q_index: (answer, timestamp)}}

# ---------------------------
# Leaderboard Functions
# ---------------------------
def update_leaderboard():
    scores = {}
    for player, answers in st.session_state["player_answers"].items():
        total = 0
        for q_idx, (ans, ts) in answers.items():
            correct_ans = riddles[questions[q_idx]]
            if ans.strip().lower() == correct_ans:
                start_time = st.session_state["question_start_times"].get(q_idx, ts)
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
    st.subheader("Host Panel")
    st.write("Project this QR code for classmates to join:")
    show_qr_code()

    # Joined Players Table
    st.subheader("Joined Players (Real-Time Table)")
    if st.session_state["players"]:
        st.table(pd.DataFrame(st.session_state["players"], columns=["Name"]))
    else:
        st.info("No players yet. Waiting...")

    # Start Game Button
    if not st.session_state["game_started"] and st.button("🚀 Start Game"):
        st.session_state["game_started"] = True
        st.session_state["question_start_times"] = {}
        st.session_state["question_start_time"] = time.time()
        st.success("Game started! Players can now see questions.")

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
                st.success(f"🎉 Welcome, {name}! Waiting for host to start...")
        else:
            st.error("Please enter a valid name.")

    # Waiting for host to start
    if not st.session_state["game_started"]:
        st.info("⏳ Waiting for host to start the game...")

    # Game Loop
    if st.session_state["game_started"]:
        q_idx = st.session_state["current_question_index"]
        if q_idx >= len(questions):
            st.success("🏁 All questions completed!")
            st.subheader("Final Leaderboard")
            st.table(update_leaderboard())
        else:
            question = questions[q_idx]
            st.subheader(f"Question {q_idx + 1}:")
            st.write(question)

            # Track question start time
            if q_idx not in st.session_state["question_start_times"]:
                st.session_state["question_start_times"][q_idx] = time.time()

            elapsed = int(time.time() - st.session_state["question_start_times"][q_idx])
            remaining = max(0, QUESTION_TIME - elapsed)
            st.info(f"⏳ Time remaining: {remaining}s")

            # Answer input
            if name not in st.session_state["player_answers"]:
                st.session_state["player_answers"][name] = {}
            player_ans = st.text_input("Your Answer", key=f"{name}_{q_idx}", value=st.session_state["player_answers"][name].get(q_idx, ("", 0))[0])
            if st.button("Submit Answer", key=f"submit_{name}_{q_idx}"):
                st.session_state["player_answers"][name][q_idx] = (player_ans, time.time())
                st.success("Answer recorded!")

            # Auto reveal answer after time
            if elapsed >= QUESTION_TIME:
                correct_answer = riddles[question]
                st.success(f"⏰ Time's up! Correct answer: {correct_answer}")
                st.subheader("Leaderboard")
                st.table(update_leaderboard())
                # Move to next question after 5 seconds
                time.sleep(5)
                st.session_state["current_question_index"] += 1
                st.experimental_rerun()
