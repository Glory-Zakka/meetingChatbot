import streamlit as st
import requests

API_BASE_URL = st.secrets["API_BASE_URL"]

st.set_page_config(
    page_title="Meeting Minute Chatbot",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ─────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── API functions ──────────────────────────────────────────
def login(email, password):
    try:
        r = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def get_me(token):
    try:
        r = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException:
        return None


def ask_question(token, question, n_results=5):
    try:
        r = requests.post(
            f"{API_BASE_URL}/chat/ask",
            headers={"Authorization": f"Bearer {token}"},
            json={"question": question, "n_results": n_results},
            timeout=60,
        )
        if r.status_code == 200:
            return r.json()
        st.error(f"Error: {r.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def handle_user_input(question):
    """Process a question and append response to message history."""
    st.session_state.messages.append({"role": "user", "content": question})

    with st.spinner("Searching meeting records..."):
        response = ask_question(st.session_state.token, question)

    if response:
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["answer"],
            "sources": response["sources"],
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Sorry, I could not get a response. Please try again.",
            "sources": [],
        })


# ── Login page ─────────────────────────────────────────────
def show_login():
    st.title("📋 Meeting Minute Chatbot")
    st.write("Sign in to continue")
    st.write("")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@organization.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in")

        if submit:
            result = login(email, password)
            if result:
                st.session_state.token = result.get("access_token")
                st.session_state.user = result
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid email or password")


# ── Sidebar ────────────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        user = st.session_state.user or {}
        st.markdown(f"### 👤 {user.get('full_name', 'User')}")
        st.caption(f"📧 {user.get('user_email', '')}")
        st.caption(f"🎭 Role: {user.get('user_role', 'staff')}")
        st.write("---")

        st.markdown("### 💡 Sample questions")
        sample_questions = [
            "What decisions were made about security policy?",
            "What was discussed about the hackathon?",
            "What are the action items from the procurement meeting?",
            "What was decided in the last staff meeting?",
        ]
        for q in sample_questions:
            if st.button(q, key=f"sample_{q}", use_container_width=True):
                handle_user_input(q)
                st.rerun()

        st.write("---")
        if st.button("🚪 Sign out", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()


# ── Chat interface ─────────────────────────────────────────
def show_chat():
    show_sidebar()

    st.title("📋 Meeting Minute Chatbot")
    st.caption("Ask questions about previous meetings")
    st.write("---")

    # Display message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                sources = message.get("sources") or []
                if sources:
                    st.write("")
                    st.write("**📚 Sources:**")
                    for source in sources:
                        doc_name = source.get("document_name", "Unknown")
                        date = source.get("meeting_date") or "N/A"
                        dept = source.get("department", "N/A")
                        st.write(
                            f"📄 **{doc_name}**  \n"
                            f"   Date: {date} | Department: {dept}"
                        )

    # Chat input
    if prompt := st.chat_input("Ask a question about your meetings..."):
        handle_user_input(prompt)
        st.rerun()


# ── Main router ────────────────────────────────────────────
if st.session_state.token is None:
    show_login()
else:
    user = get_me(st.session_state.token)
    if user:
        st.session_state.user = user
        show_chat()
    else:
        st.session_state.token = None
        st.session_state.user = None
        st.warning("Your session has expired. Please sign in again.")
        show_login()