import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Quantum AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("⚙️ Settings")

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Get your key at platform.openai.com"
    )

    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
    )

    system_prompt = st.text_area(
        "System Prompt",
        value="You are a helpful, friendly AI assistant. Be concise and clear in your responses.",
        height=120,
    )

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("✨ Quantum AI")
st.caption("Powered by OpenAI · Ask me anything")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    if not api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(api_key=api_key)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
            )
            reply = response.choices[0].message.content
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})