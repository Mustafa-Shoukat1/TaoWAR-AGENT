import streamlit as st
import base64
from database.users import check_user_credentials
from config import LOCAL_IMAGE_PATH


# ✅ Encode Local Image for Background
def get_base64_image(image_path):
    """Converts a local image to base64 encoding for use in CSS."""
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    return encoded

encoded_image = get_base64_image(LOCAL_IMAGE_PATH)

def login_page():
    """Login screen with a background image."""
    
    # ✅ Apply Background CSS Only on the Login Page
    st.markdown(f"""
        <style>
            .stApp {{
                background: url("data:image/jpg;base64,{encoded_image}") no-repeat center center fixed;
                background-size: cover;  /* ✅ Ensures the image fits the screen */
            }}
            .login-container {{
                text-align: center;
                padding: 50px;
                background: rgba(0, 0, 0, 0.6);  /* ✅ Dark overlay for readability */
                border-radius: 10px;
                color: white;
                margin: auto;
                width: 40%;
            }}
            .stTextInput > div > div > input {{
                background-color: #ffffff !important; /* ✅ White background for input fields */
                color: black !important;
            }}
            .stButton > button {{
                background-color: #ff8c00 !important; /* ✅ Styled login button */
                color: white !important;
                font-weight: bold;
                border-radius: 5px;
            }}
        </style>
    """, unsafe_allow_html=True)

    # ✅ Centered Login Box with Dark Overlay
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: white;'>🔒 Login</h1>", unsafe_allow_html=True)

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if check_user_credentials(username, password):
            st.session_state.authenticated = True
            # Store username in session state for later use
            st.session_state.username = username
            st.rerun()
        else:
            st.error("⚠️ Invalid credentials. Please try again.")

    st.markdown("</div>", unsafe_allow_html=True)

# ✅ Ensure authentication state is initialized
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False