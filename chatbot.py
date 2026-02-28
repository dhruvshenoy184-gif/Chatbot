import streamlit as st
from groq import Groq
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

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
SYSTEM_PROMPT = "You are a helpful, friendly AI assistant. Be concise and clear in your responses."
USERS_FILE = "users.json"
HISTORY_FILE = "history.json"

BOT_AVATAR = "https://play-lh.googleusercontent.com/A9D18P0Sm7s9T4LMjmuL8YWsYSGQrPABiLNh9LNvRrJlQ80HVI4hxe-GaCyi-180Cg=w240-h480-rw"  # will be replaced below

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
    users[username] = {"password": hash_password(password), "avatar": None}
    save_json(USERS_FILE, users)
    return True, "Account created!"

def login(username, password):
    users = load_json(USERS_FILE)
    if username not in users:
        return False, "Username not found."
    user = users[username]
    stored_pw = user["password"] if isinstance(user, dict) else user
    if stored_pw != hash_password(password):
        return False, "Incorrect password."
    return True, "Logged in!"

def get_user_avatar(username):
    users = load_json(USERS_FILE)
    user = users.get(username, {})
    if isinstance(user, dict):
        return user.get("avatar", None)
    return None

def set_user_avatar(username, avatar_url):
    users = load_json(USERS_FILE)
    if isinstance(users[username], dict):
        users[username]["avatar"] = avatar_url
    else:
        users[username] = {"password": users[username], "avatar": avatar_url}
    save_json(USERS_FILE, users)

def load_all_chats(username):
    history = load_json(HISTORY_FILE)
    return history.get(username, {})

def save_all_chats(username, chats):
    history = load_json(HISTORY_FILE)
    history[username] = chats
    save_json(HISTORY_FILE, history)

def generate_chat_title(first_message):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Generate a very short 3-5 word title for a chat that starts with this message. Reply with ONLY the title, nothing else."},
            {"role": "user", "content": first_message}
        ],
        max_tokens=20,
    )
    return response.choices[0].message.content.strip().strip('"')

def user_avatar_display(username):
    avatar = get_user_avatar(username)
    if avatar:
        return avatar
    # Generate initial avatar using a free avatar API
    initial = username[0].upper()
    return f"https://ui-avatars.com/api/?name={initial}&background=6d28d9&color=fff&size=128&font-size=0.6&bold=true"

# ── Session state defaults ────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

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
                    st.session_state.messages = []
                    st.session_state.current_chat = None
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
    BOT_AVATAR = "https://i.imgur.com/4yGVpBl.png"  # Quantum AI logo placeholder

    with st.sidebar:
        st.title("⚙️ Settings")

        # User avatar preview + change option
        avatar_url = user_avatar_display(st.session_state.username)
        st.image(avatar_url, width=60)
        st.markdown(f"👤 **{st.session_state.username}**")

        with st.expander("Change Avatar"):
            new_avatar = st.text_input("Paste image URL", placeholder="https://...")
            if st.button("Save Avatar", use_container_width=True):
                if new_avatar.startswith("http"):
                    set_user_avatar(st.session_state.username, new_avatar)
                    st.success("Avatar updated!")
                    st.rerun()
                else:
                    st.error("Please enter a valid URL.")
            if st.button("Reset to Default", use_container_width=True):
                set_user_avatar(st.session_state.username, None)
                st.rerun()

        st.divider()

        model = st.selectbox(
            "Model",
            ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama3-8b-8192"],
            index=0,
        )

        st.divider()

        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.current_chat = None
            st.rerun()

        st.markdown("### 💬 Past Chats")
        all_chats = load_all_chats(st.session_state.username)
        if all_chats:
            for chat_id in reversed(list(all_chats.keys())):
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(chat_id, use_container_width=True, key=f"load_{chat_id}"):
                        st.session_state.messages = all_chats[chat_id]
                        st.session_state.current_chat = chat_id
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{chat_id}"):
                        del all_chats[chat_id]
                        save_all_chats(st.session_state.username, all_chats)
                        if st.session_state.current_chat == chat_id:
                            st.session_state.messages = []
                            st.session_state.current_chat = None
                        st.rerun()
        else:
            st.caption("No past chats yet.")

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.messages = []
            st.session_state.current_chat = None
            st.rerun()

    st.title("✨ Quantum AI")
    st.caption("Ask me anything")

    for msg in st.session_state.messages:
        avatar = BOT_AVATAR if msg["role"] == "assistant" else user_avatar_display(st.session_state.username)
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=user_avatar_display(st.session_state.username)):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=BOT_AVATAR):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages,
                )
                reply = response.choices[0].message.content
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        if st.session_state.current_chat is None:
            st.session_state.current_chat = generate_chat_title(prompt)

        all_chats = load_all_chats(st.session_state.username)
        all_chats[st.session_state.current_chat] = st.session_state.messages
        save_all_chats(st.session_state.username, all_chats)

