import streamlit as st
import os

def apply_custom_css():
    """Loads the CSS file from the assets folder"""
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def render_sidebar_logo():
    """Displays the logo at the top of the sidebar"""
    # Updated to match your specific filename
    logo_path = "assets/images/140x60.png" 
    
    if os.path.exists(logo_path):
        # We use a fixed width or container width to keep it looking sharp
        st.sidebar.image(logo_path, use_container_width=False, width=140)
    else:
        st.sidebar.subheader("Strategy Hub")

def render_header(title, subtitle):
    """Renders a consistent branded header"""
    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h1 class='main-title'>{title}</h1>
            <p style="color: #64748b; font-size: 1.1rem;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Renders a simple footer with branding"""
    st.markdown("---")
    st.caption("2026 Strategy Intelligence Hub | Confidential Internal Data")
