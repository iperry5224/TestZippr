"""
NIST 800-53 Rev 5 Authentication Module
========================================
Handles user authentication, session management, and access control.
"""

import streamlit as st
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from pathlib import Path
from functools import wraps

# =============================================================================
# CONFIGURATION
# =============================================================================

# Authentication settings
AUTH_CONFIG = {
    'session_timeout_minutes': 60,
    'max_login_attempts': 5,
    'lockout_duration_minutes': 15,
    'require_mfa': False,  # Set to True to enable MFA
    'password_min_length': 8,
}

# User credentials storage path (for demo purposes - use proper DB in production)
# For containers: use environment variable or relative path
import os
USERS_FILE = Path(os.environ.get('SAELAR_USERS_FILE', Path(__file__).parent / '.nist_users.json'))

# Default admin credentials (change in production!)
DEFAULT_USERS = {
    'admin': {
        'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
        'role': 'admin',
        'full_name': 'Administrator',
        'email': 'admin@example.com',
        'created': datetime.now().isoformat(),
        'last_login': None,
        'login_attempts': 0,
        'locked_until': None,
    },
    'auditor': {
        'password_hash': hashlib.sha256('audit123'.encode()).hexdigest(),
        'role': 'auditor',
        'full_name': 'Security Auditor',
        'email': 'auditor@example.com',
        'created': datetime.now().isoformat(),
        'last_login': None,
        'login_attempts': 0,
        'locked_until': None,
    },
    'viewer': {
        'password_hash': hashlib.sha256('view123'.encode()).hexdigest(),
        'role': 'viewer',
        'full_name': 'Report Viewer',
        'email': 'viewer@example.com',
        'created': datetime.now().isoformat(),
        'last_login': None,
        'login_attempts': 0,
        'locked_until': None,
    }
}

# Role-based permissions
ROLE_PERMISSIONS = {
    'admin': {
        'can_run_assessment': True,
        'can_view_results': True,
        'can_export': True,
        'can_manage_users': True,
        'can_view_certificates': True,
        'can_configure_settings': True,
    },
    'auditor': {
        'can_run_assessment': True,
        'can_view_results': True,
        'can_export': True,
        'can_manage_users': False,
        'can_view_certificates': True,
        'can_configure_settings': False,
    },
    'viewer': {
        'can_run_assessment': False,
        'can_view_results': True,
        'can_export': False,
        'can_manage_users': False,
        'can_view_certificates': False,
        'can_configure_settings': False,
    }
}


# =============================================================================
# USER MANAGEMENT
# =============================================================================

def _load_users() -> Dict:
    """Load users from storage file."""
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_USERS.copy()


def _save_users(users: Dict):
    """Save users to storage file."""
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        st.error(f"Error saving users: {e}")


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, role: str, full_name: str, email: str) -> Tuple[bool, str]:
    """
    Create a new user account.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    users = _load_users()
    
    # Validation
    if username in users:
        return False, "Username already exists"
    
    if len(password) < AUTH_CONFIG['password_min_length']:
        return False, f"Password must be at least {AUTH_CONFIG['password_min_length']} characters"
    
    if role not in ROLE_PERMISSIONS:
        return False, f"Invalid role. Must be one of: {', '.join(ROLE_PERMISSIONS.keys())}"
    
    # Create user
    users[username] = {
        'password_hash': _hash_password(password),
        'role': role,
        'full_name': full_name,
        'email': email,
        'created': datetime.now().isoformat(),
        'last_login': None,
        'login_attempts': 0,
        'locked_until': None,
    }
    
    _save_users(users)
    return True, "User created successfully"


def delete_user(username: str) -> Tuple[bool, str]:
    """Delete a user account."""
    users = _load_users()
    
    if username not in users:
        return False, "User not found"
    
    if username == 'admin':
        return False, "Cannot delete the admin user"
    
    del users[username]
    _save_users(users)
    return True, "User deleted successfully"


def update_password(username: str, new_password: str) -> Tuple[bool, str]:
    """Update a user's password."""
    users = _load_users()
    
    if username not in users:
        return False, "User not found"
    
    if len(new_password) < AUTH_CONFIG['password_min_length']:
        return False, f"Password must be at least {AUTH_CONFIG['password_min_length']} characters"
    
    users[username]['password_hash'] = _hash_password(new_password)
    _save_users(users)
    return True, "Password updated successfully"


def get_all_users() -> Dict:
    """Get all users (without password hashes)."""
    users = _load_users()
    safe_users = {}
    for username, data in users.items():
        safe_users[username] = {k: v for k, v in data.items() if k != 'password_hash'}
    return safe_users


# =============================================================================
# AUTHENTICATION
# =============================================================================

def _check_account_locked(username: str) -> Tuple[bool, Optional[str]]:
    """Check if an account is locked due to too many failed attempts."""
    users = _load_users()
    
    if username not in users:
        return False, None
    
    user = users[username]
    locked_until = user.get('locked_until')
    
    if locked_until:
        locked_time = datetime.fromisoformat(locked_until)
        if datetime.now() < locked_time:
            remaining = (locked_time - datetime.now()).seconds // 60
            return True, f"Account locked. Try again in {remaining} minutes."
        else:
            # Unlock the account
            users[username]['locked_until'] = None
            users[username]['login_attempts'] = 0
            _save_users(users)
    
    return False, None


def _record_failed_attempt(username: str):
    """Record a failed login attempt."""
    users = _load_users()
    
    if username in users:
        users[username]['login_attempts'] = users[username].get('login_attempts', 0) + 1
        
        if users[username]['login_attempts'] >= AUTH_CONFIG['max_login_attempts']:
            lockout_time = datetime.now() + timedelta(minutes=AUTH_CONFIG['lockout_duration_minutes'])
            users[username]['locked_until'] = lockout_time.isoformat()
        
        _save_users(users)


def _reset_login_attempts(username: str):
    """Reset login attempts after successful login."""
    users = _load_users()
    
    if username in users:
        users[username]['login_attempts'] = 0
        users[username]['locked_until'] = None
        users[username]['last_login'] = datetime.now().isoformat()
        _save_users(users)


def authenticate(username: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate a user.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check if account is locked
    is_locked, lock_message = _check_account_locked(username)
    if is_locked:
        return False, lock_message
    
    users = _load_users()
    
    if username not in users:
        return False, "Invalid username or password"
    
    user = users[username]
    password_hash = _hash_password(password)
    
    if user['password_hash'] != password_hash:
        _record_failed_attempt(username)
        attempts_left = AUTH_CONFIG['max_login_attempts'] - users[username].get('login_attempts', 0)
        if attempts_left > 0:
            return False, f"Invalid username or password. {attempts_left} attempts remaining."
        else:
            return False, f"Account locked for {AUTH_CONFIG['lockout_duration_minutes']} minutes."
    
    # Successful authentication
    _reset_login_attempts(username)
    return True, "Login successful"


def get_user_role(username: str) -> Optional[str]:
    """Get the role for a user."""
    users = _load_users()
    if username in users:
        return users[username]['role']
    return None


def get_user_permissions(username: str) -> Dict:
    """Get permissions for a user based on their role."""
    role = get_user_role(username)
    if role and role in ROLE_PERMISSIONS:
        return ROLE_PERMISSIONS[role]
    return {}


def has_permission(username: str, permission: str) -> bool:
    """Check if a user has a specific permission."""
    permissions = get_user_permissions(username)
    return permissions.get(permission, False)


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def init_session_state():
    """Initialize authentication session state."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None


def login_user(username: str):
    """Set session state for logged in user."""
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.user_role = get_user_role(username)
    st.session_state.login_time = datetime.now()
    st.session_state.session_token = secrets.token_hex(32)


def logout_user():
    """Clear session state for logout."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.login_time = None
    st.session_state.session_token = None


def is_session_valid() -> bool:
    """Check if the current session is still valid."""
    if not st.session_state.get('authenticated'):
        return False
    
    login_time = st.session_state.get('login_time')
    if login_time:
        timeout = timedelta(minutes=AUTH_CONFIG['session_timeout_minutes'])
        if datetime.now() - login_time > timeout:
            logout_user()
            return False
    
    return True


def get_current_user() -> Optional[str]:
    """Get the currently logged in username."""
    if is_session_valid():
        return st.session_state.get('username')
    return None


def get_current_role() -> Optional[str]:
    """Get the current user's role."""
    if is_session_valid():
        return st.session_state.get('user_role')
    return None


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_login_form() -> bool:
    """
    Render the login form.
    
    Returns:
        True if user successfully logged in, False otherwise
    """
    st.markdown("""
    <div class="login-header">
        <h1>🛡️ NIST 800-53 Assessment</h1>
        <p>Please log in to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            submit = st.form_submit_button("🔐 Login", use_container_width=True)
        with col2:
            remember = st.checkbox("Remember me")
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
                return False
            
            success, message = authenticate(username, password)
            
            if success:
                login_user(username)
                st.success(f"✅ Welcome, {username}!")
                st.rerun()
                return True
            else:
                st.error(f"❌ {message}")
                return False
    
    # Show default credentials hint (remove in production!)
    with st.expander("ℹ️ Demo Credentials"):
        st.markdown("""
        | Username | Password | Role |
        |----------|----------|------|
        | admin | admin123 | Administrator |
        | auditor | audit123 | Security Auditor |
        | viewer | view123 | Report Viewer |
        
        ⚠️ **Note:** Change these credentials before production use!
        """)
    
    return False


def render_user_info():
    """Render current user information in sidebar."""
    if is_session_valid():
        username = st.session_state.username
        role = st.session_state.user_role
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 👤 {username}")
        st.sidebar.markdown(f"*Role: {role.title()}*")
        
        # Show permissions
        permissions = get_user_permissions(username)
        active_perms = [p.replace('can_', '').replace('_', ' ').title() 
                       for p, v in permissions.items() if v]
        
        if active_perms:
            st.sidebar.markdown("**Permissions:**")
            for perm in active_perms[:3]:  # Show first 3
                st.sidebar.markdown(f"• {perm}")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()


def render_user_management():
    """Render user management interface (admin only)."""
    if not has_permission(get_current_user(), 'can_manage_users'):
        st.warning("⚠️ You don't have permission to manage users.")
        return
    
    st.markdown("## 👥 User Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 View Users", "➕ Add User", "🔧 Modify User"])
    
    with tab1:
        users = get_all_users()
        
        for username, data in users.items():
            with st.expander(f"👤 {username} ({data['role']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Full Name:** {data['full_name']}")
                    st.markdown(f"**Email:** {data['email']}")
                with col2:
                    st.markdown(f"**Role:** {data['role']}")
                    st.markdown(f"**Created:** {data['created'][:10]}")
                    st.markdown(f"**Last Login:** {data['last_login'][:10] if data['last_login'] else 'Never'}")
    
    with tab2:
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", options=list(ROLE_PERMISSIONS.keys()))
            new_fullname = st.text_input("Full Name")
            new_email = st.text_input("Email")
            
            if st.form_submit_button("Create User"):
                success, message = create_user(new_username, new_password, new_role, new_fullname, new_email)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
    
    with tab3:
        users = get_all_users()
        selected_user = st.selectbox("Select User", options=list(users.keys()))
        
        if selected_user:
            col1, col2 = st.columns(2)
            
            with col1:
                new_pw = st.text_input("New Password", type="password", key="mod_pw")
                if st.button("Update Password"):
                    if new_pw:
                        success, message = update_password(selected_user, new_pw)
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
            
            with col2:
                if selected_user != 'admin':
                    if st.button("🗑️ Delete User", type="secondary"):
                        success, message = delete_user(selected_user)
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")


# =============================================================================
# DECORATORS
# =============================================================================

def require_auth(func):
    """Decorator to require authentication for a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        init_session_state()
        if not is_session_valid():
            render_login_form()
            return None
        return func(*args, **kwargs)
    return wrapper


def require_permission(permission: str):
    """Decorator to require a specific permission."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            username = get_current_user()
            if not username or not has_permission(username, permission):
                st.error(f"⚠️ Permission denied: {permission}")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
