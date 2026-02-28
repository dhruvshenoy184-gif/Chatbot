import streamlit as st
from openai import OpenAI
import json
import os
import hashlib

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quantum AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
SYSTEM_PROMPT = "You are a helpful, friendly AI assistant. Be concise and clear in your responses."
USERS_FILE = "users.json"
HISTORY_FILE = "history.json"

# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f)

def signup(username, password):
    users = load_json(USERS_FILE)
    if username in users:
        return False, "Username already exists."
    users[username] = hash_password(password)
    save_json(USERS_FILE, users)
    return True, "Account created!"

def login(username, password):
    users = load_json(USERS_FILE)
    if username not in users:
        return False, "Username not found."
    if users[username] != hash_password(password):
        return False, "Incorrect password."
    return True, "Logged in!"

def get_history(username):
    history = load_json(HISTORY_FILE)
    return history.get(username, [])

def save_history(username, messages):
    history = load_json(HISTORY_FILE)
    history[username] = messages
    save_json(HISTORY_FILE, history)

# ── Session state defaults ────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"

# ── Auth screen ───────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.title("✨ Quantum AI")
    st.caption("Please log in or sign up to continue")
    st.divider()

    auth_mode = st.radio("", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_mode == "Login":
        if st.button("Login", use_container_width=True, type="primary"):
            if username and password:
                success, msg = login(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.messages = get_history(username)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Please enter username and password.")
    else:
        if st.button("Sign Up", use_container_width=True, type="primary"):
            if username and password:
                if len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    success, msg = signup(username, password)
                    if success:
                        st.success(msg + " You can now log in.")
                    else:
                        st.error(msg)
            else:
                st.warning("Please enter username and password.")

# ── Main chat app ─────────────────────────────────────────────────────────────
else:
    with st.sidebar:
        st.title("⚙️ Settings")
        st.markdown(f"👤 Logged in as **{st.session_state.username}**")
        st.divider()

        model = st.selectbox(
            "Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            index=0,
        )

        st.divider()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            save_history(st.session_state.username, [])
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.messages = []
            st.rerun()

    st.title("✨ Quantum AI")
    st.caption("Ask me anything")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages,
                )
                reply = response.choices[0].message.content
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        save_history(st.session_state.username, st.session_state.messages)
