import streamlit as st
import os

def apply_custom_css():
    """
    Loads the Raleway Light Mode CSS from assets/styles.css
    """
    css_path = "assets/styles.css"
    try:
        if os.path.exists(css_path):
            with open(css_path, "r") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        # This prevents the app from crashing if the CSS file is missing
        pass

def render_sidebar_logo():
    """
    Searches for and displays the company logo in the sidebar.
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
        # Fallback text if logo is not found
        st.sidebar.markdown("<h2 style='letter-spacing: 2px; color: #1a1a1a;'>STRATEGY HUB</h2>", unsafe_allow_html=True)
        st.sidebar.markdown("---")

def render_header(title, subtitle):
    """
    Renders the main dashboard header in Raleway font (Black on White).
    """
    st.markdown(f"""
        <div style="margin-bottom: 2.5rem; font-family: 'Raleway', sans-serif;">
            <h1 style="color: #1a1a1a; font-size: 3rem; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 0; line-height: 1;">
                {title}
            </h1>
            <p style="color: #64748b; font-size: 0.9rem; font-weight: 400; letter-spacing: 3px; text-transform: uppercase; margin-top: 10px;">
                {subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_footer():
    """
    Renders a clean, light-mode footer.
    """
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-family: Raleway; font-size: 0.75rem; letter-spacing: 1px;'>"
        "2026 STRATEGY INTELLIGENCE HUB | CONFIDENTIAL INTERNAL DATA"
        "</p>", 
        unsafe_allow_html=True
    )
