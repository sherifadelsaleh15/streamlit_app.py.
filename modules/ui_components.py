import streamlit as st
import os

def apply_custom_css():
    """
    Injects the Raleway Dark Mode CSS from assets/styles.css
    """
    css_path = "assets/styles.css"
    try:
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def render_sidebar_logo():
    """
    Searches for the company logo in multiple paths.
    """
    possible_paths = [
        "assets/images/140x60.png",
        "images/140x60.png",
        "assets/140x60.png",
        "140x60.png"
    ]
    
    found_path = None
    for path in possible_paths:
        if os.path.exists(path):
            found_path = path
            break
            
    if found_path:
        st.sidebar.image(found_path, width=140)
        st.sidebar.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<h2 style='letter-spacing: 2px;'>STRATEGY HUB</h2>", unsafe_allow_html=True)
        st.sidebar.markdown("---")

def render_header(title, subtitle):
    """
    Renders an executive-style header with Raleway typography.
    """
    st.markdown(f"""
        <div style="margin-bottom: 2.5rem; font-family: 'Raleway', sans-serif;">
            <h1 style="color: #ffffff; font-size: 3rem; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 0; line-height: 1;">
                {title}
            </h1>
            <p style="color: #a3a3a3; font-size: 0.9rem; font-weight: 400; letter-spacing: 3px; text-transform: uppercase; margin-top: 10px;">
                {subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_footer():
    """
    Minimalist footer for the dark theme.
    """
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 1px solid #222222;'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #525252; font-family: Raleway; font-size: 0.75rem; letter-spacing: 1px;'>"
        "2026 STRATEGY INTELLIGENCE HUB | CONFIDENTIAL INTERNAL DATA"
        "</p>", 
        unsafe_allow_html=True
    )
