import streamlit as st
import os

def apply_custom_css():
    """Applies professional dashboard styling"""
    css_path = "assets/styles.css"
    try:
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def render_sidebar_logo():
    """Searches for and displays the logo"""
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
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("### Strategy Hub")

def render_header(title, subtitle):
    """Branded header without icons"""
    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h1 style="color: #1e293b; font-size: 2.5rem; font-weight: 800; margin-bottom: 0;">
                {title}
            </h1>
            <p style="color: #64748b; font-size: 1.1rem; margin-top: 5px;">
                {subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Clean minimalist footer"""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>"
        "2026 Strategy Intelligence Hub | Confidential Internal Data"
        "</p>", 
        unsafe_allow_html=True
    )
