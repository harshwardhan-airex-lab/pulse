import streamlit as st
import base64
import os

def add_bg_from_local(image_file: str):
    """
    Add a background image to the Streamlit app.
    
    Args:
        image_file (str): Path to the background image file
    """
    if not os.path.isfile(image_file):
        return
        
    with open(image_file, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
        
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{encoded_string});
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-color: rgba(0, 0, 0, 0.7); /* Add a dark overlay */
            background-blend-mode: overlay; /* This will blend the overlay with the image */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def apply_custom_styles():
    """
    Apply custom styling to the Streamlit app with black parameter values
    """
    custom_css = """
<style>
    /* Remove the background gradient */
    .stApp {
        color: #f8f9fa !important;
    }

    /* Rest of your existing styles remain the same */
    /* Main Title Styling */
    .stTitle, h1 {
        color: #f8f9fa !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        text-align: center !important;
        letter-spacing: -1px;
    }

    /* Section Headers */
    h2, h3, .stHeader h1 {
        color: #e9ecef !important;
        font-weight: 600 !important;
        margin: 1.5rem 0 !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 0.5rem;
    }

    /* Glassmorphism Input Fields */
    .stTextInput > div, .stNumberInput > div, .stSelectbox > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(12px) !important;
    }

    /* Inputs and Text Styling */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        color: #ffffff !important;
        background: transparent !important;
        font-size: 1rem !important;
        padding: 0.75rem !important;
    }

    /* Labels */
    .stTextInput label, .stNumberInput label, .stSelectbox label {
        color: #dee2e6 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }

    /* Buttons */
    .stButton > button {
        background: rgba(45, 45, 45, 0.8) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.8rem 2rem !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
   .stButton > button:hover {
        background: rgba(64, 64, 64, 0.9) !important;  /* Back to black/dark gray */
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.8) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px) !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(26, 26, 26, 0.8);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(64, 64, 64, 0.8);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(77, 77, 77, 0.9);
    }
    /* Text Selection Color */
    ::selection {
        background: rgba(0, 255, 0, 0.3) !important;
        color: #ffffff !important;
    }
    ::-moz-selection {
        background: rgba(0, 255, 0, 0.3) !important;
        color: #ffffff !important;
    }
      /* Text hover color */
    p:hover, span:hover, a:hover, label:hover {
        color: #00ff00 !important;
        transition: color 0.001s ease;
    }
</style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # Add custom font
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                font-family: 'Inter', sans-serif;
            }
        </style>
    """, unsafe_allow_html=True)