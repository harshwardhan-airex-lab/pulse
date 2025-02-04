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
        /* Global styling */
        .stApp {
            background: #0f172a !important;
        }
        
        /* Main title styling */
        .stTitle, h1 {
            color: #3b82f6 !important;
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            padding: 1.5rem 0 !important;
            margin-bottom: 2rem !important;
        }
        
        /* Headers */
        h2, h3, .stHeader h1 {
            color: #60a5fa !important;
            font-weight: 600 !important;
            margin: 1rem 0 !important;
        }
        
        /* Input containers */
        .stTextInput > div, .stNumberInput > div {
            background: #ffffff !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 6px !important;
            margin: 0.5rem 0 !important;
        }
        
        /* Input fields */
        .stTextInput input, .stNumberInput input {
            color: #000000 !important;
            background: #ffffff !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            padding: 0.75rem !important;
            -webkit-text-fill-color: #000000 !important;
        }
        
        /* Labels */
        .stTextInput label, .stNumberInput label, .stSelectbox label {
            color: #93c5fd !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            margin-bottom: 0.25rem !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: #3b82f6 !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.75rem 2rem !important;
            border-radius: 6px !important;
            border: none !important;
            transition: all 0.3s ease !important;
            min-width: 120px !important;
        }
        
        .stButton > button:hover {
            background: #2563eb !important;
            transform: translateY(-1px) !important;
        }
        
        /* Number input buttons */
        .stNumberInput button {
            background: #3b82f6 !important;
            color: white !important;
            border: none !important;
            padding: 0.25rem !important;
            border-radius: 4px !important;
        }
        
        .stNumberInput button:hover {
            background: #2563eb !important;
        }
        
        /* Number input value */
        input[type="number"] {
            color: #000000 !important;
            background: #ffffff !important;
            -webkit-text-fill-color: #000000 !important;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #0f172a !important;
            border-right: 1px solid #1e293b;
        }
        
        /* Expander sections */
        .streamlit-expanderHeader {
            background: #1e293b !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 6px !important;
            color: #ffffff !important;
            padding: 1rem !important;
        }
        
        .streamlit-expanderContent {
            background: #1e293b !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 0 0 6px 6px !important;
            margin-top: -1px !important;
            padding: 1rem !important;
        }
        
        /* Select boxes */
        .stSelectbox > div {
            background: #ffffff !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 6px !important;
        }
        
        .stSelectbox > div > div {
            color: #000000 !important;
        }
        
        /* Text input for patterns */
        textarea, .stTextInput textarea {
            color: #000000 !important;
            background: #ffffff !important;
            -webkit-text-fill-color: #000000 !important;
        }
        
        /* Success messages */
        .element-container.css-1e5imcs.e1f1d6gn1 {
            color: #10b981 !important;
            background: rgba(16, 185, 129, 0.1) !important;
            border-radius: 6px !important;
            padding: 0.5rem 1rem !important;
        }
        
        /* Error messages */
        .element-container.css-1e5imcs.e1f1d6gn1.alert {
            color: #ef4444 !important;
            background: rgba(239, 68, 68, 0.1) !important;
            border-radius: 6px !important;
            padding: 0.5rem 1rem !important;
        }
        
        /* JSON display */
        pre {
            background: #1e293b !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 6px !important;
            padding: 1rem !important;
            color: #e2e8f0 !important;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1e293b;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #3b82f6;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #2563eb;
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