def render_header(title, subtitle):
    """Renders a Raleway header for light mode"""
    st.markdown(f"""
        <div style="margin-bottom: 2.5rem; font-family: 'Raleway', sans-serif;">
            <h1 style="color: #1a1a1a; font-size: 3rem; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 0;">
                {title}
            </h1>
            <p style="color: #64748b; font-size: 0.9rem; font-weight: 400; letter-spacing: 3px; text-transform: uppercase; margin-top: 10px;">
                {subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Footer for light mode"""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-family: Raleway; font-size: 0.75rem;'>"
        "2026 STRATEGY INTELLIGENCE HUB | CONFIDENTIAL INTERNAL DATA"
        "</p>", 
        unsafe_allow_html=True
    )
