"""
Authentication Module

Handles user authentication, session management, and user administration
for the AI Resume Screener application. Supports role-based access control
with Admin and Recruiter roles.

Uses PostgreSQL for persistent user storage.
"""

import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional

import streamlit as st

from database_postgres import User, session_scope


# ─── Configuration ─────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "default-secret-change-in-production")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

# Default admin credentials (should be changed on first login)
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",  # Will be hashed on first use
    "role": "admin",
    "name": "System Administrator",
    "email": "admin@resumescreener.com",
}

DEFAULT_RECRUITER = {
    "username": "recruiter",
    "password": "recruiter123",  # Will be hashed on first use
    "role": "recruiter",
    "name": "Demo Recruiter",
    "email": "recruiter@resumescreener.com",
}


# ─── Password Hashing ─────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password as string.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    Args:
        password: Plain text password to verify.
        hashed: bcrypt hashed password.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─── User Database Operations ──────────────────────────────────────────────

def initialize_default_users():
    """
    Create default admin and recruiter accounts if they don't exist.
    """
    try:
        with session_scope() as session:
            # Check if admin exists
            admin_exists = session.query(User).filter_by(username="admin").first()
            if not admin_exists:
                admin_user = User(
                    user_id=str(uuid.uuid4()),
                    username=DEFAULT_ADMIN["username"],
                    password_hash=hash_password(DEFAULT_ADMIN["password"]),
                    role=DEFAULT_ADMIN["role"],
                    name=DEFAULT_ADMIN["name"],
                    email=DEFAULT_ADMIN["email"],
                    created_at=datetime.utcnow(),
                )
                session.add(admin_user)

            # Check if recruiter exists
            recruiter_exists = session.query(User).filter_by(username="recruiter").first()
            if not recruiter_exists:
                recruiter_user = User(
                    user_id=str(uuid.uuid4()),
                    username=DEFAULT_RECRUITER["username"],
                    password_hash=hash_password(DEFAULT_RECRUITER["password"]),
                    role=DEFAULT_RECRUITER["role"],
                    name=DEFAULT_RECRUITER["name"],
                    email=DEFAULT_RECRUITER["email"],
                    created_at=datetime.utcnow(),
                )
                session.add(recruiter_user)

    except Exception as e:
        st.error(f"Failed to initialize default users: {str(e)}")


def add_user(username: str, password: str, role: str, name: str, email: str) -> dict:
    """
    Add a new user to the system.

    Args:
        username: Unique username.
        password: Plain text password (will be hashed).
        role: User role ('admin' or 'recruiter').
        name: Full name of the user.
        email: Email address.

    Returns:
        dict: Created user data (excluding password hash).

    Raises:
        ValueError: If username already exists or inputs are invalid.
    """
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    if role not in ["admin", "recruiter"]:
        raise ValueError("Role must be either 'admin' or 'recruiter'")

    with session_scope() as session:
        # Check if username already exists
        existing_user = session.query(User).filter_by(username=username.strip().lower()).first()
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")

        user_id = str(uuid.uuid4())
        new_user = User(
            user_id=user_id,
            username=username.strip().lower(),
            password_hash=hash_password(password),
            role=role,
            name=name.strip(),
            email=email.strip(),
            created_at=datetime.utcnow(),
            is_active=True,
        )
        session.add(new_user)

    return {
        "user_id": user_id,
        "username": username.strip().lower(),
        "role": role,
        "name": name.strip(),
        "email": email.strip(),
        "is_active": True,
    }


def get_all_users() -> list:
    """
    Retrieve all users from the system.

    Returns:
        list: List of user dictionaries (excluding password hashes).
    """
    try:
        with session_scope() as session:
            users = session.query(User).all()
            return [user.to_dict(include_password=False) for user in users]
    except Exception as e:
        st.error(f"Failed to retrieve users: {str(e)}")
        return []


def get_user_by_username(username: str) -> Optional[dict]:
    """
    Find a user by username (includes password hash for authentication).

    Args:
        username: Username to search for.

    Returns:
        dict: User data including password hash, or None if not found.
    """
    try:
        with session_scope() as session:
            user = session.query(User).filter_by(username=username.lower(), is_active=True).first()
            if user:
                return user.to_dict(include_password=True)
            return None
    except Exception:
        return None


def update_user(user_id: str, **kwargs) -> dict:
    """
    Update user information.

    Args:
        user_id: ID of the user to update.
        **kwargs: Fields to update (e.g., name, email, role, password).

    Returns:
        dict: Updated user data (excluding password hash).

    Raises:
        ValueError: If user not found or invalid data.
    """
    with session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Hash password if provided
        if "password" in kwargs:
            if len(kwargs["password"]) < 6:
                raise ValueError("Password must be at least 6 characters long")
            user.password_hash = hash_password(kwargs.pop("password"))

        # Update allowed fields
        updatable_fields = ["name", "email", "role", "is_active"]
        for field in updatable_fields:
            if field in kwargs:
                setattr(user, field, kwargs[field])

        session.add(user)

    return user.to_dict(include_password=False)


def delete_user(user_id: str) -> bool:
    """
    Delete a user from the system.

    Args:
        user_id: ID of the user to delete.

    Returns:
        bool: True if user was deleted, False otherwise.

    Raises:
        ValueError: If trying to delete the last admin or user not found.
    """
    with session_scope() as session:
        # Prevent deleting the last admin
        user_to_delete = session.query(User).filter_by(user_id=user_id).first()
        if not user_to_delete:
            raise ValueError(f"User with ID {user_id} not found")

        if user_to_delete.role == "admin":
            admin_count = session.query(User).filter_by(role="admin").count()
            if admin_count <= 1:
                raise ValueError("Cannot delete the last admin user")

        session.delete(user_to_delete)
        return True


# ─── Authentication & Token Management ────────────────────────────────────────
def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password.

    Args:
        username: Username to authenticate.
        password: Plain text password.

    Returns:
        dict: User data (excluding password hash) if authentication succeeds.
        None: If authentication fails.
    """
    user_data = get_user_by_username(username)
    if not user_data:
        return None

    if not user_data.get("is_active", True):
        return None

    if verify_password(password, user_data["password_hash"]):
        # Update last login
        try:
            with session_scope() as session:
                user = session.query(User).filter_by(user_id=user_data["user_id"]).first()
                if user:
                    user.last_login = datetime.utcnow()
                    session.add(user)
        except Exception:
            pass  # Don't fail authentication if last_login update fails

        # Return user data without password hash
        return {k: v for k, v in user_data.items() if k != "password_hash"}

    return None


def create_token(user_data: dict) -> str:
    """
    Create a JWT token for authenticated user.

    Args:
        user_data: User dictionary from authentication.

    Returns:
        str: Encoded JWT token.
    """
    payload = {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "role": user_data["role"],
        "name": user_data["name"],
        "email": user_data.get("email", ""),
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token to decode.

    Returns:
        dict: Token payload if valid.
        None: If token is invalid or expired.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ─── Streamlit Session State Helpers ──────────────────────────────────────────
def initialize_auth_session():
    """
    Initialize authentication-related session state variables.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None


def login_user(username: str, password: str) -> bool:
    """
    Perform login and update session state.

    Args:
        username: Username to login with.
        password: Password to verify.

    Returns:
        bool: True if login successful, False otherwise.
    """
    user = authenticate_user(username, password)
    if user:
        token = create_token(user)
        st.session_state.authenticated = True
        st.session_state.current_user = user
        st.session_state.auth_token = token
        return True
    return False


def logout_user():
    """
    Logout current user and clear session state.
    """
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.auth_token = None
    if "screened" in st.session_state:
        st.session_state.screened = False
    if "ranked_list" in st.session_state:
        st.session_state.ranked_list = []
    if "parsed_resumes" in st.session_state:
        st.session_state.parsed_resumes = []
    if "parsed_jd" in st.session_state:
        st.session_state.parsed_jd = None
    if "jd_text" in st.session_state:
        st.session_state.jd_text = ""


def require_auth(roles: list = None):
    """
    Decorator-like function to require authentication for pages.
    Redirects to login if not authenticated.

    Args:
        roles: List of allowed roles (e.g., ['admin', 'recruiter']).
              If None, any authenticated user can access.
    """
    if not st.session_state.get("authenticated", False):
        st.warning("Please login to access this page.")
        show_login_page()
        st.stop()

    if roles and st.session_state.current_user.get("role") not in roles:
        st.error("You do not have permission to access this page.")
        st.stop()


# ─── Streamlit UI Components ──────────────────────────────────────────────────
def show_login_page():
    """
    Display login page with username and password fields.
    """
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background-color: #f8f9fa;
        }
        .login-title {
            text-align: center;
            color: #2F5496;
            margin-bottom: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="login-container">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h2 class="login-title">🔐 AI Resume Screener Login</h2>',
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Login", type="primary", use_container_width=True
            )
        with col2:
            st.markdown("")  # Spacer

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                with st.spinner("Authenticating..."):
                    if login_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info(
        "**Demo Credentials:**\n- Admin: `admin` / `admin123`\n- Recruiter: `recruiter` / `recruiter123`"
    )


def show_user_profile():
    """
    Display current user's profile information.
    """
    user = st.session_state.current_user
    if not user:
        return

    with st.sidebar:
        st.divider()
        st.markdown(f"**👤 {user.get('name', 'User')}**")
        st.markdown(f"**Role:** {user.get('role', 'N/A').title()}")
        st.markdown(f"**Email:** {user.get('email', 'N/A')}")

        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()


def show_admin_panel():
    """
    Display admin panel for user and system management.
    """
    st.title("⚙️ Admin Panel")

    if st.session_state.current_user.get("role") != "admin":
        st.error("Access denied. Admin privileges required.")
        return

    # Tab navigation
    tab_users, tab_settings = st.tabs(["👥 User Management", "⚙️ System Settings"])

    with tab_users:
        st.subheader("User Management")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("#### Add New User")
            with st.form("add_user_form"):
                new_username = st.text_input("Username*")
                new_name = st.text_input("Full Name*")
                new_email = st.text_input("Email*")
                new_password = st.text_input("Password* (min 6 chars)", type="password")
                new_role = st.selectbox("Role", ["recruiter", "admin"])

                add_submitted = st.form_submit_button(
                    "Add User", type="primary", use_container_width=True
                )

                if add_submitted:
                    if not all([new_username, new_name, new_email, new_password]):
                        st.error("All fields are required.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        try:
                            add_user(
                                username=new_username,
                                password=new_password,
                                role=new_role,
                                name=new_name,
                                email=new_email,
                            )
                            st.success(f"User '{new_username}' added successfully!")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

        with col2:
            st.markdown("#### Existing Users")
            users = get_all_users()

            if users:
                # Display users in a table
                user_data = []
                for u in users:
                    user_data.append(
                        {
                            "ID": u["user_id"][:8] + "...",
                            "Username": u["username"],
                            "Name": u["name"],
                            "Email": u.get("email", "N/A"),
                            "Role": u["role"].title(),
                            "Active": "✅" if u.get("is_active", True) else "❌",
                        }
                    )

                st.dataframe(user_data, use_container_width=True)

                # User actions
                st.markdown("#### User Actions")
                user_to_manage = st.selectbox(
                    "Select User",
                    options=[u["user_id"] for u in users],
                    format_func=lambda x: next(
                        (u["username"] for u in users if u["user_id"] == x), x
                    ),
                )

                if user_to_manage:
                    selected_user = next(
                        (u for u in users if u["user_id"] == user_to_manage), None
                    )

                    if selected_user:
                        action_col1, action_col2 = st.columns(2)

                        with action_col1:
                            # Edit user
                            with st.expander("Edit User"):
                                with st.form("edit_user_form"):
                                    edit_name = st.text_input(
                                        "Full Name",
                                        value=selected_user.get("name", ""),
                                    )
                                    edit_email = st.text_input(
                                        "Email", value=selected_user.get("email", "")
                                    )
                                    edit_role = st.selectbox(
                                        "Role",
                                        ["recruiter", "admin"],
                                        index=0
                                        if selected_user.get("role") == "recruiter"
                                        else 1,
                                    )
                                    edit_password = st.text_input(
                                        "New Password (leave blank to keep current)",
                                        type="password",
                                    )
                                    edit_active = st.checkbox(
                                        "Active",
                                        value=selected_user.get("is_active", True),
                                    )

                                    edit_submitted = st.form_submit_button(
                                        "Update User", use_container_width=True
                                    )

                                    if edit_submitted:
                                        try:
                                            update_kwargs = {
                                                "name": edit_name,
                                                "email": edit_email,
                                                "role": edit_role,
                                                "is_active": edit_active,
                                            }
                                            if edit_password:
                                                update_kwargs["password"] = (
                                                    edit_password
                                                )

                                            update_user(user_to_manage, **update_kwargs)
                                            st.success("User updated successfully!")
                                            st.rerun()
                                        except ValueError as e:
                                            st.error(str(e))

                        with action_col2:
                            # Delete user
                            st.markdown("**Delete User**")
                            if (
                                selected_user["username"]
                                == st.session_state.current_user["username"]
                            ):
                                st.warning("You cannot delete your own account.")
                            else:
                                if st.button(
                                    "🗑️ Delete User",
                                    type="secondary",
                                    use_container_width=True,
                                ):
                                    try:
                                        delete_user(user_to_manage)
                                        st.success("User deleted successfully!")
                                        st.rerun()
                                    except ValueError as e:
                                        st.error(str(e))
            else:
                st.info("No users found. Add your first user using the form.")

    with tab_settings:
        st.subheader("System Settings")

        # Show system information
        st.markdown("#### System Information")
        
        # Get database status
        try:
            from database import get_database_status
            db_status = get_database_status()
            db_info = "PostgreSQL ✅" if db_status.get("connected") else "PostgreSQL ❌"
        except Exception:
            db_info = "PostgreSQL (Status unknown)"

        st.info(
            f"""
            - **Total Users:** {len(get_all_users())}
            - **Active Sessions:** 1
            - **Database:** {db_info}
            - **JWT Expiry:** {TOKEN_EXPIRY_HOURS} hours
            """
        )

        # Change own password
        st.markdown("#### Change Your Password")
        with st.form("change_password_form"):
            current_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")

            pwd_submitted = st.form_submit_button(
                "Change Password", use_container_width=True
            )

            if pwd_submitted:
                if not all([current_pwd, new_pwd, confirm_pwd]):
                    st.error("All fields are required.")
                elif new_pwd != confirm_pwd:
                    st.error("New passwords do not match.")
                elif len(new_pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    current_user = st.session_state.current_user
                    if verify_password(current_pwd, get_user_by_username(current_user["username"])["password_hash"]):
                        try:
                            update_user(current_user["user_id"], password=new_pwd)
                            st.success(
                                "Password changed successfully! Please login again."
                            )
                            logout_user()
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                    else:
                        st.error("Current password is incorrect.")
