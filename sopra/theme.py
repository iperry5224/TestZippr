"""
SOPRA Theme — Colors, CSS constants, chart styling, and shared configurations.
Single source of truth for all visual theming.
"""
import plotly.graph_objects as go

# ============================================================================
# CHART STYLE CONSTANTS — Single source of truth for all chart theming
# ============================================================================
CHART_BG = 'rgba(15, 27, 45, 0.5)'
CHART_PLOT_BG = 'rgba(15, 27, 45, 0.3)'
CHART_FONT_COLOR = '#f5f5f5'
CHART_GRID_COLOR = 'rgba(0, 217, 255, 0.12)'
CHART_GRID_LIGHT = 'rgba(0, 217, 255, 0.08)'
CHART_BORDER_COLOR = '#0f1b2d'
CHART_LEGEND = dict(font=dict(color="#f5f5f5"), bgcolor='rgba(0,0,0,0)')
COLOR_PASSED = "#00ff88"
COLOR_FAILED = "#e94560"
COLOR_NOT_ASSESSED = "#4a6fa5"
COLOR_CRITICAL = "#e94560"
COLOR_HIGH = "#ff6b6b"
COLOR_MEDIUM = "#ffc107"
COLOR_LOW = "#00d9ff"
PIE_COLORS_STATUS = [COLOR_PASSED, COLOR_FAILED, COLOR_NOT_ASSESSED]
BAR_COLORS_SEV = [COLOR_CRITICAL, COLOR_HIGH, COLOR_MEDIUM, COLOR_LOW]
SEV_ORDER = ["Critical", "High", "Medium", "Low"]
SEV_COLORS = {"Critical": COLOR_CRITICAL, "High": COLOR_HIGH, "Medium": COLOR_MEDIUM, "Low": COLOR_LOW}
SEV_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🔵"}


def chart_layout(height=320, **overrides):
    """Return a standard chart layout dict. Pass overrides to customize."""
    layout = dict(
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_PLOT_BG,
        font_color=CHART_FONT_COLOR,
        legend=CHART_LEGEND,
        height=height,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    layout.update(overrides)
    return layout


FAMILY_ABBREV = {
    "Access Control": "AC",
    "Audit & Accountability": "AU",
    "Audit and Accountability": "AU",
    "Configuration Management": "CM",
    "Contingency Planning": "CP",
    "Identification & Authentication": "IA",
    "Identification and Authentication": "IA",
    "Incident Response": "IR",
    "Maintenance": "MA",
    "Media Protection": "MP",
    "Physical & Environmental Protection": "PE",
    "Physical & Environmental": "PE",
    "Physical and Environmental Protection": "PE",
    "Planning": "PL",
    "Personnel Security": "PS",
    "Risk Assessment": "RA",
    "System & Services Acquisition": "SA",
    "System and Services Acquisition": "SA",
    "System & Communications Protection": "SC",
    "System and Communications Protection": "SC",
    "System & Comm Protection": "SC",
    "System & Information Integrity": "SI",
    "System and Information Integrity": "SI",
    "System & Info Integrity": "SI",
    "Program Management": "PM",
    "Supply Chain Risk Management": "SR",
}

# Severity helpers
SEV_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🔵"}


# ============================================================================
# GLOBAL CSS — injected once at app startup
# ============================================================================
GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Professional icon styling */
    .cat-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #00d9ff 0%, #0f3460 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .cat-icon-container {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }
    
    .cat-icon-box {
        width: 42px;
        height: 42px;
        border-radius: 10px;
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.2) 0%, rgba(15, 52, 96, 0.3) 100%);
        border: 1px solid rgba(0, 217, 255, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    
    .cat-icon-box i {
        font-size: 1.2rem;
        color: #00d9ff;
    }
    
    /* Metric card click overlay button - invisible but clickable */
    .metric-btn-wrapper {
        position: relative;
    }
    
    .metric-btn-wrapper button {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 10 !important;
    }
    
    .metric-card {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 217, 255, 0.4);
        border-color: #00d9ff;
    }
    
    :root {
        --sopra-primary: #454550;
        --sopra-secondary: #4a4a58;
        --sopra-accent: #e94560;
        --sopra-highlight: #0f3460;
        --sopra-success: #00d9ff;
        --sopra-warning: #ffc107;
        --sopra-danger: #e94560;
        --sopra-text: #f5f5f5;
    }
    
    /* Global text brightness for maximum readability */
    .main p, .main li, .main span, .main td, .main th, .main div {
        color: #f0f0f0 !important;
    }
    
    .main strong, .main b {
        color: #ffffff !important;
    }
    
    .stMarkdown p {
        color: #f0f0f0 !important;
    }
    
    .stMarkdown li {
        color: #f0f0f0 !important;
    }
    
    .stMarkdown code {
        color: #00d9ff !important;
        background: rgba(0, 217, 255, 0.1) !important;
    }
    
    /* Table styling for bright text */
    .stDataFrame, .stTable {
        color: #f0f0f0 !important;
    }
    
    /* Selectbox and multiselect text */
    .stSelectbox label, .stMultiSelect label, .stTextInput label, .stTextArea label {
        color: #f0f0f0 !important;
    }
    
    /* Caption and helper text */
    .stCaption, small, .caption {
        color: #c0c0c0 !important;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        color: #f0f0f0 !important;
    }
    
    /* Tab labels */
    .stTabs [data-baseweb="tab"] {
        color: #f0f0f0 !important;
    }
    
    /* Keep header colors cyan */
    .main h1, .main h2, .main h3, .main h4 {
        color: #00d9ff !important;
    }
    
    .main, .main .block-container, [data-testid="stAppViewContainer"], 
    [data-testid="stMain"], section.main, .appview-container {
        background-color: #0f1b2d !important;
    }
    
    .stApp, [data-testid="stAppViewContainer"] > section,
    [data-testid="stHeader"], header[data-testid="stHeader"] {
        background-color: #0f1b2d !important;
    }
    
    /* Sidebar background */
    section[data-testid="stSidebar"], [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div {
        background-color: #0b1524 !important;
    }
    
    /* Subtle grid background effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(0, 217, 255, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 217, 255, 0.04) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    h1, h2, h3 {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: #00d9ff !important;
    }
    
    .opra-header {
        background: linear-gradient(180deg, #0b1524 0%, #101e35 30%, #132848 70%, #0e1a2e 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        border: 1px solid rgba(0, 217, 255, 0.3);
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 0 40px rgba(0, 0, 0, 0.5), inset 0 0 80px rgba(0, 217, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .opra-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(ellipse at center, rgba(0, 217, 255, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    
    .opra-header h1 {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 3rem !important;
        color: #00d9ff !important;
        margin: 0;
        text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
    }
    
    .opra-header p {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #f5f5f5;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    .opra-card {
        background: linear-gradient(145deg, #162440, #1a2d50);
        border: 1px solid #4a5068;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .opra-card:hover {
        border-color: #00d9ff;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.2);
        transform: translateY(-2px);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #162440, #1a2d50);
        border: 1px solid #00d9ff;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
    
    /* Make ALL buttons look like styled dark grey tiles */
    .stButton button,
    .stButton > button,
    div[data-testid="stButton"] > button,
    button[kind="secondary"],
    .stButton button[kind="secondary"] {
        background: linear-gradient(145deg, #162440, #1a2d50) !important;
        border: 1px solid rgba(0, 217, 255, 0.5) !important;
        border-radius: 12px !important;
        color: #00d9ff !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        min-height: 100px !important;
        white-space: pre-wrap !important;
        line-height: 1.4 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover,
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover {
        border-color: #00d9ff !important;
        box-shadow: 0 0 25px rgba(0, 217, 255, 0.4) !important;
        transform: translateY(-3px) !important;
        background: linear-gradient(145deg, #1e3355, #233a60) !important;
    }
    
    .stButton button:active,
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    .stButton button:focus,
    .stButton > button:focus {
        box-shadow: 0 0 25px rgba(0, 217, 255, 0.4) !important;
        outline: none !important;
    }
    
    /* Primary buttons keep their distinctive red style */
    .stButton button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #e94560, #c73e54) !important;
        border: none !important;
        color: white !important;
        min-height: auto !important;
    }
    
    .stButton button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #ff5a75, #e94560) !important;
        box-shadow: 0 0 20px rgba(233, 69, 96, 0.4) !important;
    }
    
    /* Extra specificity for Streamlit button overrides */
    .element-container .stButton button,
    section[data-testid="stSidebar"] .stButton button,
    .main .stButton button {
        background: linear-gradient(145deg, #162440, #1a2d50) !important;
        border: 1px solid rgba(0, 217, 255, 0.5) !important;
        color: #00d9ff !important;
    }
    
    /* Ensure button text is visible */
    .stButton button p,
    .stButton button span,
    .stButton button div {
        color: #00d9ff !important;
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d9ff;
    }
    
    .metric-label {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #f5f5f5;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .risk-critical { color: #e94560 !important; }
    .risk-high { color: #ff6b6b !important; }
    .risk-medium { color: #ffc107 !important; }
    .risk-low { color: #00d9ff !important; }
    
    .stButton > button {
        background: linear-gradient(90deg, #e94560, #162440) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #162440, #e94560) !important;
        box-shadow: 0 0 20px rgba(233, 69, 96, 0.4) !important;
        transform: scale(1.02) !important;
    }
    
    .assessment-category {
        background: #0f1b2d;
        border-left: 4px solid #00d9ff;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Chart container styling for dark blue theme */
    [data-testid="stPlotlyChart"] {
        background: linear-gradient(145deg, rgba(22, 36, 64, 0.7), rgba(26, 45, 80, 0.5)) !important;
        border: 1px solid rgba(0, 217, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 8px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.03) !important;
    }
    
    .sidebar .stSelectbox, .sidebar .stMultiSelect {
        background: #4a4a58;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #454550;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #e94560;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00d9ff;
    }
"""

# ============================================================================
# ASSESSMENT CATEGORIES
# ============================================================================
OPRA_CATEGORIES = {
    "active_directory": {
        "name": "Active Directory Security",
        "icon": "fa-solid fa-sitemap",
        "icon_emoji": "🔐",  # Fallback
        "description": "Domain controllers, GPOs, privileged accounts, authentication",
        "controls": [
            {"id": "AD-001", "name": "Domain Admin Account Security", "family": "Access Control"},
            {"id": "AD-002", "name": "Service Account Management", "family": "Access Control"},
            {"id": "AD-003", "name": "Group Policy Security", "family": "Configuration Management"},
            {"id": "AD-004", "name": "Password Policy Enforcement", "family": "Identification & Auth"},
            {"id": "AD-005", "name": "Kerberos Configuration", "family": "Identification & Auth"},
            {"id": "AD-006", "name": "LDAP Signing & Binding", "family": "System & Comm Protection"},
            {"id": "AD-007", "name": "AdminSDHolder Protection", "family": "Access Control"},
            {"id": "AD-008", "name": "Trust Relationship Security", "family": "Access Control"},
            {"id": "AD-009", "name": "Replication Security", "family": "System & Comm Protection"},
            {"id": "AD-010", "name": "Audit Policy Configuration", "family": "Audit & Accountability"},
        ]
    },
    "network_infrastructure": {
        "name": "Network Infrastructure",
        "icon": "fa-solid fa-network-wired",
        "icon_emoji": "🌐",
        "description": "Firewalls, switches, routers, segmentation, IDS/IPS",
        "controls": [
            {"id": "NET-001", "name": "Network Segmentation", "family": "System & Comm Protection"},
            {"id": "NET-002", "name": "Firewall Rule Review", "family": "System & Comm Protection"},
            {"id": "NET-003", "name": "IDS/IPS Configuration", "family": "System & Info Integrity"},
            {"id": "NET-004", "name": "VPN Security", "family": "System & Comm Protection"},
            {"id": "NET-005", "name": "Switch Port Security", "family": "System & Comm Protection"},
            {"id": "NET-006", "name": "Router ACL Review", "family": "Access Control"},
            {"id": "NET-007", "name": "Network Device Hardening", "family": "Configuration Management"},
            {"id": "NET-008", "name": "Wireless Security", "family": "System & Comm Protection"},
            {"id": "NET-009", "name": "DNS Security", "family": "System & Comm Protection"},
            {"id": "NET-010", "name": "Network Monitoring", "family": "System & Info Integrity"},
        ]
    },
    "endpoint_security": {
        "name": "Endpoint Security",
        "icon": "fa-solid fa-laptop-code",
        "icon_emoji": "💻",
        "description": "Workstations, laptops, servers, EDR, patching",
        "controls": [
            {"id": "END-001", "name": "Endpoint Protection Platform", "family": "System & Info Integrity"},
            {"id": "END-002", "name": "Patch Management", "family": "System & Info Integrity"},
            {"id": "END-003", "name": "Host-based Firewall", "family": "System & Comm Protection"},
            {"id": "END-004", "name": "Application Whitelisting", "family": "Configuration Management"},
            {"id": "END-005", "name": "Local Admin Rights", "family": "Access Control"},
            {"id": "END-006", "name": "USB/Removable Media Control", "family": "Media Protection"},
            {"id": "END-007", "name": "Full Disk Encryption", "family": "System & Comm Protection"},
            {"id": "END-008", "name": "EDR/XDR Deployment", "family": "System & Info Integrity"},
            {"id": "END-009", "name": "Secure Boot Configuration", "family": "System & Info Integrity"},
            {"id": "END-010", "name": "Endpoint Logging", "family": "Audit & Accountability"},
        ]
    },
    "server_security": {
        "name": "Server Security",
        "icon": "fa-solid fa-server",
        "icon_emoji": "🖥️",
        "description": "Windows/Linux servers, hardening, services, databases",
        "controls": [
            {"id": "SRV-001", "name": "Server Hardening Baseline", "family": "Configuration Management"},
            {"id": "SRV-002", "name": "Unnecessary Services Disabled", "family": "Configuration Management"},
            {"id": "SRV-003", "name": "Database Security", "family": "System & Comm Protection"},
            {"id": "SRV-004", "name": "File Server Permissions", "family": "Access Control"},
            {"id": "SRV-005", "name": "Web Server Security", "family": "System & Comm Protection"},
            {"id": "SRV-006", "name": "Email Server Security", "family": "System & Comm Protection"},
            {"id": "SRV-007", "name": "Backup Server Protection", "family": "Contingency Planning"},
            {"id": "SRV-008", "name": "Virtualization Security", "family": "System & Comm Protection"},
            {"id": "SRV-009", "name": "Server Certificate Management", "family": "System & Comm Protection"},
            {"id": "SRV-010", "name": "Server Access Logging", "family": "Audit & Accountability"},
        ]
    },
    "physical_security": {
        "name": "Physical Security",
        "icon": "fa-solid fa-building-shield",
        "icon_emoji": "🏢",
        "description": "Data centers, server rooms, access controls, surveillance",
        "controls": [
            {"id": "PHY-001", "name": "Physical Access Control", "family": "Physical & Environmental"},
            {"id": "PHY-002", "name": "Visitor Management", "family": "Physical & Environmental"},
            {"id": "PHY-003", "name": "Surveillance Systems", "family": "Physical & Environmental"},
            {"id": "PHY-004", "name": "Server Room Access", "family": "Physical & Environmental"},
            {"id": "PHY-005", "name": "Environmental Controls", "family": "Physical & Environmental"},
            {"id": "PHY-006", "name": "Cable Management", "family": "Physical & Environmental"},
            {"id": "PHY-007", "name": "Equipment Disposal", "family": "Media Protection"},
            {"id": "PHY-008", "name": "Emergency Power", "family": "Physical & Environmental"},
            {"id": "PHY-009", "name": "Fire Suppression", "family": "Physical & Environmental"},
            {"id": "PHY-010", "name": "Physical Security Logging", "family": "Audit & Accountability"},
        ]
    },
    "data_protection": {
        "name": "Data Protection",
        "icon": "fa-solid fa-shield-halved",
        "icon_emoji": "🛡️",
        "description": "Encryption, DLP, backup, classification, retention",
        "controls": [
            {"id": "DAT-001", "name": "Data Classification", "family": "Risk Assessment"},
            {"id": "DAT-002", "name": "Data Loss Prevention", "family": "System & Info Integrity"},
            {"id": "DAT-003", "name": "Encryption at Rest", "family": "System & Comm Protection"},
            {"id": "DAT-004", "name": "Encryption in Transit", "family": "System & Comm Protection"},
            {"id": "DAT-005", "name": "Backup & Recovery", "family": "Contingency Planning"},
            {"id": "DAT-006", "name": "Data Retention Policy", "family": "System & Info Integrity"},
            {"id": "DAT-007", "name": "Sensitive Data Handling", "family": "Media Protection"},
            {"id": "DAT-008", "name": "Database Encryption", "family": "System & Comm Protection"},
            {"id": "DAT-009", "name": "Key Management", "family": "System & Comm Protection"},
            {"id": "DAT-010", "name": "Data Access Auditing", "family": "Audit & Accountability"},
        ]
    },
    "identity_access": {
        "name": "Identity & Access Management",
        "icon": "fa-solid fa-user-shield",
        "icon_emoji": "👤",
        "description": "Authentication, authorization, privileged access, MFA",
        "controls": [
            {"id": "IAM-001", "name": "Multi-Factor Authentication", "family": "Identification & Auth"},
            {"id": "IAM-002", "name": "Privileged Access Management", "family": "Access Control"},
            {"id": "IAM-003", "name": "Role-Based Access Control", "family": "Access Control"},
            {"id": "IAM-004", "name": "Account Lifecycle Management", "family": "Access Control"},
            {"id": "IAM-005", "name": "Password Vault/Management", "family": "Identification & Auth"},
            {"id": "IAM-006", "name": "Session Management", "family": "Access Control"},
            {"id": "IAM-007", "name": "Access Review Process", "family": "Access Control"},
            {"id": "IAM-008", "name": "Separation of Duties", "family": "Access Control"},
            {"id": "IAM-009", "name": "Remote Access Security", "family": "Access Control"},
            {"id": "IAM-010", "name": "Identity Federation", "family": "Identification & Auth"},
        ]
    },
    "monitoring_logging": {
        "name": "Monitoring & Logging",
        "icon": "fa-solid fa-chart-line",
        "icon_emoji": "📊",
        "description": "SIEM, log management, alerting, incident detection",
        "controls": [
            {"id": "MON-001", "name": "SIEM Implementation", "family": "Audit & Accountability"},
            {"id": "MON-002", "name": "Log Collection & Aggregation", "family": "Audit & Accountability"},
            {"id": "MON-003", "name": "Log Retention & Protection", "family": "Audit & Accountability"},
            {"id": "MON-004", "name": "Real-time Alerting", "family": "System & Info Integrity"},
            {"id": "MON-005", "name": "Security Event Correlation", "family": "System & Info Integrity"},
            {"id": "MON-006", "name": "Threat Detection Rules", "family": "System & Info Integrity"},
            {"id": "MON-007", "name": "Network Traffic Analysis", "family": "System & Info Integrity"},
            {"id": "MON-008", "name": "User Behavior Analytics", "family": "System & Info Integrity"},
            {"id": "MON-009", "name": "Incident Response Integration", "family": "Incident Response"},
            {"id": "MON-010", "name": "Compliance Reporting", "family": "Audit & Accountability"},
        ]
    },
    "vulnerability_management": {
        "name": "Vulnerability Management",
        "icon": "fa-solid fa-bug",
        "icon_emoji": "🔍",
        "description": "Scanning, patching SLAs, asset discovery, pen testing",
        "controls": [
            {"id": "VM-001", "name": "Vulnerability Scanning Program", "family": "Risk Assessment"},
            {"id": "VM-002", "name": "Vulnerability Remediation SLAs", "family": "Risk Assessment"},
            {"id": "VM-003", "name": "Asset Discovery & Inventory", "family": "System & Info Integrity"},
            {"id": "VM-004", "name": "Penetration Testing", "family": "Risk Assessment"},
            {"id": "VM-005", "name": "Threat Intelligence Integration", "family": "Risk Assessment"},
            {"id": "VM-006", "name": "Web Application Scanning", "family": "Risk Assessment"},
            {"id": "VM-007", "name": "Container Image Scanning", "family": "System & Info Integrity"},
            {"id": "VM-008", "name": "Database Vulnerability Assessment", "family": "Risk Assessment"},
            {"id": "VM-009", "name": "Vulnerability Exception Management", "family": "Risk Assessment"},
            {"id": "VM-010", "name": "Zero-Day Response Procedure", "family": "Incident Response"},
        ]
    },
    "configuration_management": {
        "name": "Configuration Management",
        "icon": "fa-solid fa-gears",
        "icon_emoji": "⚙️",
        "description": "Baselines, change management, golden images, drift detection",
        "controls": [
            {"id": "CFG-001", "name": "Baseline Configuration Standards", "family": "Configuration Management"},
            {"id": "CFG-002", "name": "Change Management Process", "family": "Configuration Management"},
            {"id": "CFG-003", "name": "Golden Image Management", "family": "Configuration Management"},
            {"id": "CFG-004", "name": "Software Inventory Control", "family": "Configuration Management"},
            {"id": "CFG-005", "name": "Hardware Inventory Control", "family": "Configuration Management"},
            {"id": "CFG-006", "name": "Configuration Drift Detection", "family": "Configuration Management"},
            {"id": "CFG-007", "name": "Firmware Security Management", "family": "System & Info Integrity"},
            {"id": "CFG-008", "name": "Network Device Configuration Backup", "family": "Configuration Management"},
            {"id": "CFG-009", "name": "Least Functionality Enforcement", "family": "Configuration Management"},
            {"id": "CFG-010", "name": "Security Configuration Compliance Reporting", "family": "Configuration Management"},
        ]
    },
    "incident_response": {
        "name": "Incident Response",
        "icon": "fa-solid fa-fire-extinguisher",
        "icon_emoji": "🚨",
        "description": "IR plans, tabletop exercises, forensics, communication",
        "controls": [
            {"id": "IR-001", "name": "Incident Response Plan", "family": "Incident Response"},
            {"id": "IR-002", "name": "Incident Response Team", "family": "Incident Response"},
            {"id": "IR-003", "name": "Tabletop Exercises", "family": "Incident Response"},
            {"id": "IR-004", "name": "Evidence Preservation & Chain of Custody", "family": "Incident Response"},
            {"id": "IR-005", "name": "Incident Classification & Prioritization", "family": "Incident Response"},
            {"id": "IR-006", "name": "External Reporting Requirements", "family": "Incident Response"},
            {"id": "IR-007", "name": "Forensic Readiness", "family": "Incident Response"},
            {"id": "IR-008", "name": "Automated Incident Response", "family": "Incident Response"},
            {"id": "IR-009", "name": "Lessons Learned Process", "family": "Incident Response"},
            {"id": "IR-010", "name": "Incident Communication Plan", "family": "Incident Response"},
        ]
    },
    "contingency_planning": {
        "name": "Contingency Planning",
        "icon": "fa-solid fa-life-ring",
        "icon_emoji": "🆘",
        "description": "BCP, DR plans, backup testing, alternate sites, RTO/RPO",
        "controls": [
            {"id": "CP-001", "name": "Business Continuity Plan", "family": "Contingency Planning"},
            {"id": "CP-002", "name": "Disaster Recovery Plan", "family": "Contingency Planning"},
            {"id": "CP-003", "name": "DR Testing & Exercises", "family": "Contingency Planning"},
            {"id": "CP-004", "name": "Backup Verification & Testing", "family": "Contingency Planning"},
            {"id": "CP-005", "name": "Alternate Processing Site", "family": "Contingency Planning"},
            {"id": "CP-006", "name": "System Recovery Prioritization", "family": "Contingency Planning"},
            {"id": "CP-007", "name": "Data Backup Offsite Storage", "family": "Contingency Planning"},
            {"id": "CP-008", "name": "Telecommunications Redundancy", "family": "Contingency Planning"},
            {"id": "CP-009", "name": "Essential Personnel Identification", "family": "Contingency Planning"},
            {"id": "CP-010", "name": "Contingency Plan Training", "family": "Contingency Planning"},
        ]
    },
    "security_awareness": {
        "name": "Security Awareness & Training",
        "icon": "fa-solid fa-graduation-cap",
        "icon_emoji": "🎓",
        "description": "Awareness training, phishing sims, personnel security",
        "controls": [
            {"id": "SAT-001", "name": "Security Awareness Program", "family": "Personnel Security"},
            {"id": "SAT-002", "name": "Phishing Simulation Program", "family": "Personnel Security"},
            {"id": "SAT-003", "name": "Role-Based Security Training", "family": "Personnel Security"},
            {"id": "SAT-004", "name": "Social Engineering Awareness", "family": "Personnel Security"},
            {"id": "SAT-005", "name": "Personnel Screening", "family": "Personnel Security"},
            {"id": "SAT-006", "name": "Personnel Termination Procedures", "family": "Personnel Security"},
            {"id": "SAT-007", "name": "Access Agreements", "family": "Personnel Security"},
            {"id": "SAT-008", "name": "Insider Threat Awareness", "family": "Personnel Security"},
            {"id": "SAT-009", "name": "Security Training Effectiveness", "family": "Personnel Security"},
            {"id": "SAT-010", "name": "Third-Party Personnel Security", "family": "Personnel Security"},
        ]
    },
    "application_security": {
        "name": "Application Security",
        "icon": "fa-solid fa-code",
        "icon_emoji": "💻",
        "description": "SSDLC, SAST/DAST, SCA, WAF, API security, secrets mgmt",
        "controls": [
            {"id": "APP-001", "name": "Secure SDLC", "family": "System & Services Acquisition"},
            {"id": "APP-002", "name": "Static Application Security Testing", "family": "System & Services Acquisition"},
            {"id": "APP-003", "name": "Dynamic Application Security Testing", "family": "System & Services Acquisition"},
            {"id": "APP-004", "name": "Software Composition Analysis", "family": "System & Services Acquisition"},
            {"id": "APP-005", "name": "Web Application Firewall", "family": "System & Comm Protection"},
            {"id": "APP-006", "name": "API Security", "family": "System & Comm Protection"},
            {"id": "APP-007", "name": "Secure Code Review", "family": "System & Services Acquisition"},
            {"id": "APP-008", "name": "Input Validation", "family": "System & Info Integrity"},
            {"id": "APP-009", "name": "Secrets Management", "family": "Identification & Auth"},
            {"id": "APP-010", "name": "Security Headers & TLS", "family": "System & Comm Protection"},
        ]
    },
    "supply_chain": {
        "name": "Supply Chain Risk Management",
        "icon": "fa-solid fa-truck-fast",
        "icon_emoji": "🔗",
        "description": "Vendor risk, SBOM, third-party patching, supplier security",
        "controls": [
            {"id": "SCR-001", "name": "Vendor Risk Assessment Program", "family": "System & Services Acquisition"},
            {"id": "SCR-002", "name": "Software Bill of Materials", "family": "System & Services Acquisition"},
            {"id": "SCR-003", "name": "Third-Party Software Patching", "family": "System & Info Integrity"},
            {"id": "SCR-004", "name": "Supplier Security Requirements", "family": "System & Services Acquisition"},
            {"id": "SCR-005", "name": "Component Authenticity Verification", "family": "System & Services Acquisition"},
            {"id": "SCR-006", "name": "Supply Chain Incident Notification", "family": "Incident Response"},
            {"id": "SCR-007", "name": "Vendor Access Controls", "family": "Access Control"},
            {"id": "SCR-008", "name": "Cloud Service Provider Assessment", "family": "System & Services Acquisition"},
            {"id": "SCR-009", "name": "End-of-Life Technology Management", "family": "System & Services Acquisition"},
            {"id": "SCR-010", "name": "Open Source Software Governance", "family": "System & Services Acquisition"},
        ]
    },
    "governance_compliance": {
        "name": "Governance & Compliance",
        "icon": "fa-solid fa-scale-balanced",
        "icon_emoji": "⚖️",
        "description": "Security policy, RMF, ATO, continuous monitoring, SSP",
        "controls": [
            {"id": "GOV-001", "name": "Information Security Policy", "family": "Planning"},
            {"id": "GOV-002", "name": "Risk Management Framework", "family": "Risk Assessment"},
            {"id": "GOV-003", "name": "Security Assessment & Authorization", "family": "Risk Assessment"},
            {"id": "GOV-004", "name": "Continuous Monitoring Program", "family": "Risk Assessment"},
            {"id": "GOV-005", "name": "System Security Plan", "family": "Planning"},
            {"id": "GOV-006", "name": "Regulatory Compliance Tracking", "family": "Planning"},
            {"id": "GOV-007", "name": "Security Metrics & Reporting", "family": "Planning"},
            {"id": "GOV-008", "name": "Security Architecture Review", "family": "Planning"},
            {"id": "GOV-009", "name": "Interconnection Security Agreements", "family": "Risk Assessment"},
            {"id": "GOV-010", "name": "Privacy Impact Assessment", "family": "Planning"},
        ]
    },
    "wireless_mobile": {
        "name": "Wireless & Mobile Security",
        "icon": "fa-solid fa-mobile-screen-button",
        "icon_emoji": "📱",
        "description": "MDM, BYOD, wireless networks, rogue AP, Bluetooth",
        "controls": [
            {"id": "WMS-001", "name": "Mobile Device Management", "family": "Access Control"},
            {"id": "WMS-002", "name": "BYOD Security Policy", "family": "Access Control"},
            {"id": "WMS-003", "name": "Wireless Network Security", "family": "System & Comm Protection"},
            {"id": "WMS-004", "name": "Rogue Wireless Detection", "family": "System & Info Integrity"},
            {"id": "WMS-005", "name": "Guest Wireless Isolation", "family": "System & Comm Protection"},
            {"id": "WMS-006", "name": "Mobile Application Security", "family": "System & Services Acquisition"},
            {"id": "WMS-007", "name": "Mobile Device Encryption", "family": "System & Comm Protection"},
            {"id": "WMS-008", "name": "Lost/Stolen Device Response", "family": "Media Protection"},
            {"id": "WMS-009", "name": "Bluetooth Security", "family": "System & Comm Protection"},
            {"id": "WMS-010", "name": "Wireless Penetration Testing", "family": "Risk Assessment"},
        ]
    },
    "virtualization_containers": {
        "name": "Virtualization & Container Security",
        "icon": "fa-solid fa-cubes",
        "icon_emoji": "📦",
        "description": "Hypervisor hardening, VM isolation, Kubernetes, container runtime",
        "controls": [
            {"id": "VCS-001", "name": "Hypervisor Hardening", "family": "Configuration Management"},
            {"id": "VCS-002", "name": "VM Isolation & Segmentation", "family": "System & Comm Protection"},
            {"id": "VCS-003", "name": "Container Runtime Security", "family": "System & Comm Protection"},
            {"id": "VCS-004", "name": "Container Registry Security", "family": "System & Info Integrity"},
            {"id": "VCS-005", "name": "VM Snapshot Management", "family": "Media Protection"},
            {"id": "VCS-006", "name": "Kubernetes RBAC", "family": "Access Control"},
            {"id": "VCS-007", "name": "Virtual Network Security", "family": "System & Comm Protection"},
            {"id": "VCS-008", "name": "Container Secrets Management", "family": "Identification & Auth"},
            {"id": "VCS-009", "name": "VM Template Security", "family": "Configuration Management"},
            {"id": "VCS-010", "name": "Container Network Policies", "family": "System & Comm Protection"},
        ]
    },
    "email_communications": {
        "name": "Email & Communications Security",
        "icon": "fa-solid fa-envelope-open-text",
        "icon_emoji": "📧",
        "description": "Email gateway, DMARC, phishing protection, DLP, UC security",
        "controls": [
            {"id": "ECS-001", "name": "Email Gateway Protection", "family": "System & Info Integrity"},
            {"id": "ECS-002", "name": "DMARC/DKIM/SPF Implementation", "family": "System & Comm Protection"},
            {"id": "ECS-003", "name": "Email Encryption", "family": "System & Comm Protection"},
            {"id": "ECS-004", "name": "Phishing Protection", "family": "System & Info Integrity"},
            {"id": "ECS-005", "name": "Email Data Loss Prevention", "family": "System & Comm Protection"},
            {"id": "ECS-006", "name": "Unified Communications Security", "family": "System & Comm Protection"},
            {"id": "ECS-007", "name": "Email Retention & Archival", "family": "Audit & Accountability"},
            {"id": "ECS-008", "name": "Secure File Transfer", "family": "System & Comm Protection"},
            {"id": "ECS-009", "name": "Collaboration Platform Security", "family": "Access Control"},
            {"id": "ECS-010", "name": "External Email Marking", "family": "System & Info Integrity"},
        ]
    },
    "cryptographic_controls": {
        "name": "Cryptographic Controls",
        "icon": "fa-solid fa-key",
        "icon_emoji": "🔑",
        "description": "TLS, PKI, key management, HSM, crypto standards",
        "controls": [
            {"id": "CRY-001", "name": "Cryptographic Standards Policy", "family": "System & Comm Protection"},
            {"id": "CRY-002", "name": "TLS Configuration", "family": "System & Comm Protection"},
            {"id": "CRY-003", "name": "Certificate Lifecycle Management", "family": "System & Comm Protection"},
            {"id": "CRY-004", "name": "PKI Infrastructure Security", "family": "System & Comm Protection"},
            {"id": "CRY-005", "name": "Encryption Key Rotation", "family": "System & Comm Protection"},
            {"id": "CRY-006", "name": "Hardware Security Module Usage", "family": "System & Comm Protection"},
            {"id": "CRY-007", "name": "Deprecated Algorithm Remediation", "family": "System & Comm Protection"},
            {"id": "CRY-008", "name": "Crypto Agility Planning", "family": "System & Comm Protection"},
            {"id": "CRY-009", "name": "Disk Encryption Key Escrow", "family": "System & Comm Protection"},
            {"id": "CRY-010", "name": "Random Number Generation", "family": "System & Comm Protection"},
        ]
    },
}
