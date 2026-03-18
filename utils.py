"""
Utility functions for Smoke Finder app
This module provides helper functions used across multiple pages including:
- Secrets validation
- Google Sheets integration
- Common error handling

Created to centralize shared functionality and avoid code duplication.
"""

import streamlit as st

def check_secrets():
    """
    Check if required secrets are configured.
    Returns True if all required secrets are present, False otherwise.
    Shows error message if secrets are missing.
    
    Required secrets:
    - email: DataForSEO API email
    - password: DataForSEO API password
    - gcp_service_account: Google Cloud service account for Sheets integration
    """
    required_secrets = ["email", "password", "gcp_service_account"]
    missing = []
    
    for secret in required_secrets:
        try:
            _ = st.secrets[secret]
        except (KeyError, FileNotFoundError):
            missing.append(secret)
    
    if missing:
        st.error(f"⚠️ Missing secrets: {', '.join(missing)}")
        st.info("""
        **How to fix:**
        1. Copy `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml`
        2. Fill in your credentials:
           - `email` and `password`: DataForSEO API credentials
           - `gcp_service_account`: Google Cloud service account JSON
        3. Restart the app
        """)
        return False
    return True


def get_rest_client():
    """
    Get DataForSEO REST client if secrets are configured.
    Returns RestClient instance or None if secrets are missing.
    """
    from client import RestClient
    
    if not check_secrets():
        return None
    
    return RestClient(st.secrets["email"], st.secrets["password"])


def get_gspread_client():
    """
    Get Google Sheets client if secrets are configured.
    Returns gspread client or None if secrets are missing.
    """
    import gspread
    
    if not check_secrets():
        return None
    
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])
