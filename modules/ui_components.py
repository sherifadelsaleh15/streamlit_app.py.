import streamlit as st
import os

def apply_custom_css():
    """Loads the Raleway Light Mode CSS"""
    css_path = "assets/styles.css"
    try:
        if os.path.exists(css_path):
            with open(css_path, "r") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def render_sidebar_logo():
    """Displays the logo at the top of the sidebar"""
    logo_path = "assets/images/140x60.png"
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=140)
        st.sidebar.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<h2 style='letter-spacing: 2px;'>STRATEGY HUB</h2>", unsafe_allow_html=True)

def render_header(title, subtitle):
    """Executive header with Raleway typography"""
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

def render_pdf_button():
    """Triggers browser print dialog for PDF export"""
    st.sidebar.markdown("---")
    if st.sidebar.button("Export Dashboard to PDF"):
        st.components.v1.html(
            "<script>window.parent.print();</script>",
            height=0, width=0,
        )
    st.sidebar.caption("Ensure 'Background Graphics' is ON in print settings.")

def render_footer():
    """Minimalist footer"""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-family: Raleway; font-size: 0.75rem; letter-spacing: 1px;'>"
        "2026 STRATEGY INTELLIGENCE HUB | CONFIDENTIAL INTERNAL DATA"
        "</p>", 
        unsafe_allow_html=True
    )
