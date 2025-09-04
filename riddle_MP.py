import streamlit as st
import pandas as pd
import random
import time

# ---------------------------
# Constants
# ---------------------------
APP_URL = "https://riddleshield-puyslisekmtui29rqnrhpl.streamlit.app"
QUESTION_TIME = 30  # seconds per question
NEXT_QUESTION_DELAY = 3  # seconds after revealing answer

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
# Session State Initialization
# ---------------------------
if "players" not in st.session_state:
    st.session_state["players"] = []
if "game_started" not in st.session_state:
    st.session_state["game_started"] = False
if "question_index" not in st.session_state:
    st.session_state["question_index"] = 0
if "question_order" not in st.session_state:
    st.session_state["question_order"] = list(riddles.keys())
    random.shuffle(st.session_state["question_order"])
if "player_answers" not in st.session_state:
    st.session_state["player_answers"] = {}  # {player: {q_index: (answer, timestamp)}}
if "question_start_times" not in st.session_state:
    st.session_state["question_start_times"] = {}  # {q_index: start_time}

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
# Leaderboard Calculation
# ---------------------------
def get_leaderboard():
    scores = {}
    for player, answers in st.session_state["player_answers"].items():
        total = 0
        for q_idx, (ans, ts) in answers.items():
            correct = riddles[st.session_state["question_order"][q_idx]]
            if ans.strip().lower() == correct:
                start_time = st.session_state["question_start_times"].get(q_idx, ts)
                total += max(0, QUESTION_TIME - int(ts - start_time))
        scores[player] = total
    return pd.DataFrame(list(scores.items()), columns=["Player", "Score"]).sort_values(by="Score", ascending=False)

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

    # Start Game button
    if not st.session_state["game_started"]:
        if st.button("🚀 Start Game"):
            st.session_state["game_started"] = True
            st.session_state["question_start_times"][st.session_state["question_index"]] = time.time()
            st.success("Game started! Players can now see questions.")

    # Show current question with countdown
    if st.session_state["game_started"]:
        q_idx = st.session_state["question_index"]
        if q_idx < len(st.session_state["question_order"]):
            question = st.session_state["question_order"][q_idx]
            st.subheader(f"Question {q_idx +1}: {question}")

            # Timer placeholder
            timer_placeholder = st.empty()
            start_time = st.session_state["question_start_times"][q_idx]

            elapsed = int(time.time() - start_time)
            remaining = max(0, QUESTION_TIME - elapsed)
            timer_placeholder.markdown(f"⏳ Time Remaining: {remaining:02d}s")

            if remaining <= 0:
                correct_answer = riddles[question]
                st.success(f"⏰ Time's up! Correct answer: {correct_answer}")
                # Show leaderboard after each question
                st.subheader("🏆 Live Leaderboard")
                st.table(get_leaderboard())
                # Move to next question after delay
                time.sleep(NEXT_QUESTION_DELAY)
                st.session_state["question_index"] += 1
                if st.session_state["question_index"] < len(st.session_state["question_order"]):
                    st.session_state["question_start_times"][st.session_state["question_index"]] = time.time()
                st.experimental_rerun()
        else:
            st.success("🏁 Quiz Finished!")
            st.subheader("Final Leaderboard")
            st.table(get_leaderboard())

# ---------------------------
# Player View
# ---------------------------
else:
    st.title("🎲 Welcome to Tarun's Riddle Shield!")
    name = st.text_input("Enter your name")

    if st.button("Join Game"):
        if name.strip() and name not in [p[0] for p in st.session_state["players"]]:
            st.session_state["players"].append([name])
            st.success(f"🎉 Welcome, {name}! Waiting for host to start...")
        elif not name.strip():
            st.error("Enter a valid name.")

    if not st.session_state["game_started"]:
        st.info("⏳ Waiting for host to start...")

    # Player question view
    if st.session_state["game_started"] and name.strip():
        q_idx = st.session_state["question_index"]
        if q_idx >= len(st.session_state["question_order"]):
            st.success("🏁 Quiz Finished!")
        else:
            question = st.session_state["question_order"][q_idx]
            st.subheader(f"Question {q_idx +1}")
            st.write(question)

            # Timer placeholder
            timer_placeholder = st.empty()
            start_time = st.session_state["question_start_times"].get(q_idx, time.time())
            elapsed = int(time.time() - start_time)
            remaining = max(0, QUESTION_TIME - elapsed)
            timer_placeholder.markdown(f"⏳ Time Remaining: {remaining:02d}s")

            # Player answer input
            if name not in st.session_state["player_answers"]:
                st.session_state["player_answers"][name] = {}
            ans_input = st.text_input("Your Answer:", key=f"{name}_{q_idx}", 
                                      value=st.session_state["player_answers"][name].get(q_idx, ("",0))[0])
            if st.button("Submit Answer", key=f"submit_{name}_{q_idx}"):
                st.session_state["player_answers"][name][q_idx] = (ans_input, time.time())
                st.success("Answer recorded!")
