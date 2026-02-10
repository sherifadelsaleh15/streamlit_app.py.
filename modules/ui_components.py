import streamlit as st

def apply_custom_css():
    """Loads the CSS file from the assets folder"""
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
    st.caption("🚀 2026 Strategy Intelligence Hub | Confidential Internal Data")
