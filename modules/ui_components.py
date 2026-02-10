import streamlit as st
import os

def render_sidebar_logo():
    """
    Enhanced logo loader that searches multiple common paths 
    to ensure the logo appears regardless of folder structure.
    """
    # List of possible paths to check
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
        # This will only show up if the file is truly missing from GitHub
        st.sidebar.markdown("### Strategy Hub")
        # For debugging: uncomment the line below to see where it's looking
        # st.sidebar.write("Debug: Logo not found in any path.")
