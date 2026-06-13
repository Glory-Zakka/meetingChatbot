import streamlit as st
import requests
import datetime

import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

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
if "page" not in st.session_state:
    st.session_state.page = "chat"
if "admin_tab" not in st.session_state:
    st.session_state.admin_tab = "📤 Upload"
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None


# ── Helper ─────────────────────────────────────────────────
def normalize_user(user):
    if not user:
        return user
    if "user_role" not in user and "role" in user:
        user["user_role"] = user["role"]
    return user


# ── API functions ──────────────────────────────────────────
def login(email, password):
    try:
        r = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            return normalize_user(r.json())
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
            return normalize_user(r.json())
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


def upload_document(token, file):
    try:
        r = requests.post(
            f"{API_BASE_URL}/admin/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (file.name, file.getvalue(), file.type)},
            timeout=120,
        )
    
        if r.status_code == 200:
            return r.json()
        try:
            error_detail = r.json().get("detail", "Unknown error")
        except Exception:
            error_detail = r.text
        st.error(f"Upload failed: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None

def list_documents(token):
    try:
        r = requests.get(
            f"{API_BASE_URL}/admin/documents",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def delete_document(token, file_name):
    try:
        r = requests.delete(
            f"{API_BASE_URL}/admin/documents/{file_name}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        if r.status_code == 200:
            return r.json()
        try:
            error_detail = r.json().get("detail", "Unknown error")
        except Exception:
            error_detail = r.text
        st.error(f"Delete failed: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def get_stats(token):
    try:
        r = requests.get(
            f"{API_BASE_URL}/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def get_audit_logs(token, limit=100, offset=0, user_email=None,
                    action=None, date_from=None, date_to=None):
    try:
        params = {"limit": limit, "offset": offset}
        if user_email:
            params["user_email"] = user_email
        if action:
            params["action"] = action
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        r = requests.get(
            f"{API_BASE_URL}/admin/audit-logs",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def list_users(token):
    """Fetches all users from the backend (staff endpoint)."""
    # Use a backend route — we need to add a /admin/users endpoint
    # For now, we'll get users from a new endpoint we'll add
    try:
        r = requests.get(
            f"{API_BASE_URL}/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def deactivate_user(token, user_id):
    try:
        r = requests.patch(
            f"{API_BASE_URL}/auth/users/{user_id}/deactivate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        try:
            error_detail = r.json().get("detail", "Unknown error")
        except Exception:
            error_detail = r.text
        st.error(f"Deactivate failed: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def activate_user(token, user_id):
    try:
        r = requests.patch(
            f"{API_BASE_URL}/auth/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        try:
            error_detail = r.json().get("detail", "Unknown error")
        except Exception:
            error_detail = r.text
        st.error(f"Activate failed: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def register_user(token, full_name, email, password, role):
    try:
        r = requests.post(
            f"{API_BASE_URL}/auth/register",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": full_name,
                "email": email,
                "password": password,
                "role": role,
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        try:
            error_detail = r.json().get("detail", "Unknown error")
        except Exception:
            error_detail = r.text
        st.error(f"Registration failed: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def handle_user_input(question):
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

        user_role = str(user.get("user_role", "")).lower()
        is_admin = user_role == "admin"

        if st.button("💬 Chat", use_container_width=True,
                      type="primary" if st.session_state.page == "chat" else "secondary"):
            st.session_state.page = "chat"
            st.rerun()

        if is_admin:
            if st.button("⚙️ Admin Panel", use_container_width=True,
                          type="primary" if st.session_state.page == "admin" else "secondary"):
                st.session_state.page = "admin"
                st.rerun()

        st.write("---")

        if st.session_state.page == "chat":
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
            st.session_state.page = "chat"
            st.session_state.confirm_delete = None
            st.rerun()


# ── Chat interface ─────────────────────────────────────────
def show_chat():
    show_sidebar()

    st.title("📋 Meeting Minute Chatbot")
    st.caption("Ask questions about previous meetings")
    st.write("---")

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

    if prompt := st.chat_input("Ask a question about your meetings..."):
        handle_user_input(prompt)
        st.rerun()


# ── Admin panel — Tabs ────────────────────────────────────
def show_admin():
    show_sidebar()

    st.title("⚙️ Admin Panel")
    st.caption("Manage documents, users, and view activity logs")
    st.write("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard", "📤 Upload", "📚 Documents", "👥 Users & Logs"
    ])

    with tab1:
        show_admin_dashboard()

    with tab2:
        show_admin_upload()

    with tab3:
        show_admin_documents()

    with tab4:
        show_admin_users_and_logs()


# ── Admin: Dashboard ──────────────────────────────────────
def show_admin_dashboard():
    st.subheader("System Overview")
    stats = get_stats(st.session_state.token)
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Documents", stats.get("total_documents", 0))
        with col2:
            st.metric("🧩 Chunks", stats.get("total_chunks", 0))
        with col3:
            st.metric("👥 Total Users", stats.get("total_users", 0))
        with col4:
            st.metric("✅ Active Users", stats.get("active_users", 0))

    st.write("---")
    st.subheader("Recent Activity")
    logs_data = get_audit_logs(st.session_state.token, limit=10)
    if logs_data and logs_data.get("logs"):
        for log_entry in logs_data["logs"][:10]:
            action_icons = {
                "login": "🔐", "chat_query": "💬", "upload": "📤",
                "delete": "🗑️", "create_user": "➕",
                "deactivate_user": "🚫", "activate_user": "✅"
            }
            icon = action_icons.get(log_entry["action"], "📌")
            status_color = "🟢" if log_entry["status"] == "success" else "🔴"
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.write(f"{icon} **{log_entry['action']}**")
                with col2:
                    user = log_entry.get("user_email") or "anonymous"
                    resource = log_entry.get("resource_id") or ""
                    st.write(
                        f"{status_color} {user} — {resource}  \n"
                        f"<small>{log_entry['created_at']}</small>",
                        unsafe_allow_html=True
                    )
    else:
        st.info("No activity yet.")


# ── Admin: Upload ─────────────────────────────────────────
def show_admin_upload():
    st.subheader("📤 Upload New Meeting Document")
    st.write("Upload a PDF or Word file. The system will automatically process and index it.")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx"],
        help="Only PDF and DOCX files are supported. Maximum 50MB.",
        key="file_uploader",
    )

    if uploaded_file is not None:
        st.write(f"**Selected:** {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        if st.button("🚀 Process and Upload", type="primary"):
            with st.spinner("Uploading and processing... this may take a minute."):
                result = upload_document(st.session_state.token, uploaded_file)

            if result:
                st.success("✅ Document processed successfully!")
                st.write(f"**File:** {result['file_name']}")
                st.write(f"**Chunks created:** {result['total_chunks']}")
                metadata = result.get("metadata", {})
                if metadata.get("meeting_date"):
                    st.write(f"**Meeting date:** {metadata['meeting_date']}")
                if metadata.get("department"):
                    st.write(f"**Department:** {metadata['department']}")
                if metadata.get("decisions_made"):
                    st.write(f"**Decisions found:** {len(metadata['decisions_made'])}")
                st.balloons()
                st.rerun()


# ── Admin: Documents ──────────────────────────────────────
def show_admin_documents():
    st.subheader("📚 All Meeting Documents")
    docs_data = list_documents(st.session_state.token)
    if docs_data and docs_data.get("documents"):
        st.write(f"Total: **{docs_data['total']}** documents")
        st.write("")

        for doc in docs_data["documents"]:
            col1, col2, col3 = st.columns([5, 2, 1])
            with col1:
                st.write(f"📄 **{doc['file_name']}**")
                st.caption(
                    f"Type: {doc['file_type'].upper()} | "
                    f"Size: {doc['file_size_bytes']:,} bytes | "
                    f"Chunks: {doc.get('chunks', 0)}"
                )
            with col2:
                mod_time = datetime.datetime.fromtimestamp(doc["modified"])
                st.caption(f"Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")
            with col3:
                if st.button("🗑️ Delete", key=f"del_{doc['file_name']}",
                              type="secondary"):
                    st.session_state.confirm_delete = doc["file_name"]
                    st.rerun()

            # Confirmation dialog
            if st.session_state.confirm_delete == doc["file_name"]:
                st.warning(
                    f"⚠️ Are you sure you want to delete "
                    f"**{doc['file_name']}**? This will remove the file "
                    f"and all {doc.get('chunks', 0)} associated chunks. "
                    f"This cannot be undone."
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Yes, delete", key=f"yes_{doc['file_name']}",
                                  type="primary"):
                        with st.spinner("Deleting..."):
                            result = delete_document(
                                st.session_state.token,
                                doc["file_name"]
                            )
                        if result:
                            st.success(
                                f"Deleted {result['file_name']} "
                                f"({result['chunks_deleted']} chunks removed)"
                            )
                        st.session_state.confirm_delete = None
                        st.rerun()
                with col_no:
                    if st.button("❌ Cancel", key=f"no_{doc['file_name']}"):
                        st.session_state.confirm_delete = None
                        st.rerun()
    else:
        st.info("No documents uploaded yet.")


# ── Admin: Users & Logs ───────────────────────────────────
def show_admin_users_and_logs():
    sub_tab1, sub_tab2 = st.tabs(["👥 Users", "📋 Activity Log"])

    with sub_tab1:
        st.subheader("User Management")
        st.write("Create new users and manage existing accounts.")

        with st.expander("➕ Create New User"):
            with st.form("create_user_form"):
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["staff", "admin"])
                create_submitted = st.form_submit_button("Create User")

                if create_submitted:
                    if not new_name or not new_email or not new_password:
                        st.error("All fields are required.")
                    else:
                        result = register_user(
                            st.session_state.token,
                            new_name, new_email, new_password, new_role
                        )
                        if result:
                            st.success(
                                f"✅ User {result['email']} created as {result['role']}"
                            )
                            st.rerun()

        st.write("---")
        st.write("**Existing Users**")
        users_data = list_users(st.session_state.token)
        if users_data and users_data.get("users"):
            for u in users_data["users"]:
                col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                with col1:
                    st.write(f"**{u['full_name']}**")
                with col2:
                    st.write(f"📧 {u['email']}")
                with col3:
                    role_icon = "👑" if u["role"] == "admin" else "👤"
                    st.write(f"{role_icon} {u['role']}")
                with col4:
                    if u["is_active"]:
                        st.caption("✅ Active")
                    else:
                        st.caption("🚫 Inactive")
                    if u["is_active"]:
                        if st.button("Deactivate", key=f"deact_{u['id']}"):
                            deactivate_user(st.session_state.token, u["id"])
                            st.rerun()
                    else:
                        if st.button("Activate", key=f"act_{u['id']}"):
                            activate_user(st.session_state.token, u["id"])
                            st.rerun()
        else:
            st.info("No users found or endpoint unavailable.")

    with sub_tab2:
        st.subheader("Activity Log")
        st.write("View all system activities. Use filters to narrow down.")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_user = st.text_input("Filter by user email")
        with col_f2:
            filter_action = st.selectbox(
                "Action type",
                ["all", "login", "chat_query", "upload",
                 "delete", "create_user", "deactivate_user", "activate_user"]
            )
        with col_f3:
            filter_date = st.date_input("From date", value=None)

        if st.button("Apply Filters"):
            st.session_state.audit_filter = {
                "user_email": filter_user or None,
                "action": None if filter_action == "all" else filter_action,
                "date_from": (
                    filter_date.isoformat() if filter_date else None
                ),
            }

        filters = st.session_state.get("audit_filter", {})
        logs_data = get_audit_logs(
            st.session_state.token,
            limit=100,
            user_email=filters.get("user_email"),
            action=filters.get("action"),
            date_from=filters.get("date_from"),
        )

        if logs_data and logs_data.get("logs"):
            st.write(f"Showing {len(logs_data['logs'])} of {logs_data['total']} total entries")
            for log_entry in logs_data["logs"]:
                action_icons = {
                    "login": "🔐", "chat_query": "💬", "upload": "📤",
                    "delete": "🗑️", "create_user": "➕",
                    "deactivate_user": "🚫", "activate_user": "✅"
                }
                icon = action_icons.get(log_entry["action"], "📌")
                status = "✅" if log_entry["status"] == "success" else "❌"
                with st.expander(
                    f"{icon} {log_entry['action'].upper()} — "
                    f"{log_entry.get('user_email') or 'anonymous'} — "
                    f"{log_entry['created_at']} {status}"
                ):
                    st.write(f"**User:** {log_entry.get('user_email') or 'N/A'}")
                    st.write(f"**Action:** {log_entry['action']}")
                    st.write(f"**Resource:** {log_entry.get('resource_id') or 'N/A'}")
                    st.write(f"**Status:** {log_entry['status']}")
                    st.write(f"**IP:** {log_entry.get('ip_address') or 'N/A'}")
                    if log_entry.get("details"):
                        st.write("**Details:**")
                        st.json(log_entry["details"])
        else:
            st.info("No logs found.")


# ── Main router ────────────────────────────────────────────
if st.session_state.token is None:
    show_login()
else:
    user = get_me(st.session_state.token)
    if user:
        st.session_state.user = user
        user_role = str(user.get("user_role", "")).lower()
        if st.session_state.page == "admin" and user_role == "admin":
            show_admin()
        else:
            show_chat()
    else:
        st.session_state.token = None
        st.session_state.user = None
        st.session_state.page = "chat"
        st.warning("Your session has expired. Please sign in again.")
        show_login()