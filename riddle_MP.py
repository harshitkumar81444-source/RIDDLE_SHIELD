import streamlit as st
import pandas as pd
import os
import random

# ---------------- Leaderboard Management ----------------
LEADERBOARD_FILE = "leaderboard.csv"

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

# ---------------- Riddle Game ----------------
riddles = {
    "I speak without a mouth and hear without ears. I have nobody, but I come alive with the wind. What am I?": "echo",
    "The more of me you take, the more you leave behind. What am I?": "footsteps",
    "What has to be broken before you can use it?": "egg",
    "I’m tall when I’m young, and I’m short when I’m old. What am I?": "candle",
    "What has keys but can’t open locks?": "piano"
}

def play_game(player_name):
    score = 0
    for riddle, answer in random.sample(list(riddles.items()), 3):  # ask 3 random riddles
        st.write("🤔 Riddle: ", riddle)
        user_answer = st.text_input("Your Answer:", key=riddle)

        if st.button("Submit", key=riddle+"_submit"):
            if user_answer.strip().lower() == answer:
                st.success("✅ Correct!")
                score += 1
            else:
                st.error(f"❌ Wrong! Correct answer: {answer}")

    st.write(f"**{player_name}, your final score: {score}**")
    update_leaderboard(player_name, score)
    show_leaderboard()

# ---------------- Streamlit App ----------------
st.title("🧩 Multiplayer Riddle Game")

if "page" not in st.session_state:
    st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    st.subheader("Enter your name to join the game")
    name = st.text_input("Your Name:")

    if st.button("Join Game"):
        if name.strip() == "":
            st.warning("Please enter a valid name.")
        else:
            st.session_state.name = name
            st.session_state.page = "game"
            st.rerun()

elif st.session_state.page == "game":
    st.subheader(f"Welcome, {st.session_state.name} 👋")
    play_game(st.session_state.name)

    if st.button("Play Again"):
        st.session_state.page = "welcome"
        st.rerun()
