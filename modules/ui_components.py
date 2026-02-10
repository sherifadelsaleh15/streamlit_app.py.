import streamlit as st
import os

def apply_custom_css():
    """
    Loads the custom CSS from the assets folder.
    Ensures the professional dashboard styling is applied.
    """
    css_path = "assets/styles.css"
    try:
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        # If CSS fails, the app continues with default Streamlit styling
        pass

def render_sidebar_logo():
    """
    Displays the company logo at the top of the sidebar.
    Uses the specific 140x60.png file uploaded to assets/images/.
    """
    # The exact path to your logo on GitHub
    logo_path = "assets/images/140x60.png"
    
    if os.path.exists(logo_path):
        # We use a fixed width of 140 to match your file dimensions
        st.sidebar.image(logo_path, width=140)
        # Adds a clean spacer after the logo
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
    else:
        # Fallback text if the logo is not found
        st.sidebar.markdown("### Strategy Hub")
        st.sidebar.markdown("---")

def render_header(title, subtitle):
    """
    Renders a clean, professional header for the main dashboard area.
    No emojis or icons as requested.
    """
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
    """
    Renders a minimalist footer at the bottom of the page.
    """
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>"
        "2026 Strategy Intelligence Hub | Confidential Internal Data"
        "</p>", 
        unsafe_allow_html=True
    )
