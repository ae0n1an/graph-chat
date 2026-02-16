import streamlit as st

# Configure the landing page
st.set_page_config(page_title="MyThanks Chatbot", page_icon="🛒", layout="wide")

def render_landing_page():
    st.markdown(
        """
        <style>
            /* Hide Streamlit elements on landing page */
            [data-testid="stSidebar"] { display: none; }
            [data-testid="stSidebarNav"] { display: none; }
            header { visibility: hidden; }
            

            .stApp {
                background: linear-gradient(135deg, #EE1C25 0%, #b3141b 100%);
                background-attachment: fixed;
                overflow: hidden !important;
            }
            .block-container {
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100% !important;
            }
            .main {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            /* Landing Page Container */
            .landing-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 70vh; /* Reduced height to ensure no scroll */
                width: 100vw;
                text-align: center;
                color: white;
                font-family: 'Inter', sans-serif;
                overflow: hidden;
            }
            
            /* Logo Animation */
            .logo-animation {
                font-size: 70px; /* Reduced from 100px */
                margin-bottom: 10px;
                animation: float 3s ease-in-out infinite;
                filter: drop-shadow(0 10px 15px rgba(0,0,0,0.3));
            }
            
            @keyframes float {
                0% { transform: translateY(0px) rotate(0deg); }
                50% { transform: translateY(-15px) rotate(5deg); }
                100% { transform: translateY(0px) rotate(0deg); }
            }
            
            /* Title & Text Animations */
            .title {
                font-size: 3.2rem; /* Reduced from 4.5rem */
                font-weight: 900;
                margin-bottom: 0.5rem;
                letter-spacing: -1.5px;
                opacity: 0;
                animation: fadeInDown 1.2s ease-out forwards;
                text-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }
            
            .subtitle {
                font-size: 1.1rem; /* Reduced from 1.4rem */
                margin-bottom: 2rem;
                max-width: 500px;
                line-height: 1.6;
                opacity: 0;
                animation: fadeInUp 1.2s ease-out 0.6s forwards;
            }
            
            @keyframes fadeInDown {
                from { opacity: 0; transform: translateY(-50px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(50px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Button Styling */
            .stButton > button {
                background-color: white !important;
                color: #EE1C25 !important;
                font-weight: 800 !important;
                padding: 1rem 3.5rem !important;
                border-radius: 50px !important;
                border: none !important;
                font-size: 1.3rem !important;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2) !important;
                opacity: 0;
                animation: fadeIn 1.2s ease-out 1.2s forwards;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .stButton > button:hover {
                transform: scale(1.1) translateY(-5px) !important;
                box-shadow: 0 15px 35px rgba(0,0,0,0.4) !important;
                background-color: #f8f8f8 !important;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            /* Responsive tweaks */
            @media (max-width: 768px) {
                .title { font-size: 3rem; }
                .subtitle { font-size: 1.1rem; }
                .logo-animation { font-size: 80px; }
            }
        </style>
        
        <div class="landing-container">
            <div class="logo-animation">🛒</div>
            <h1 class="title">MyThanks Chatbot</h1>
            <p class="subtitle">Empowering Coles teams with instant data insights and AI-driven analytics.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Sign-in button logic
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("Sign In to MyThanks", use_container_width=True):
            st.switch_page("pages/Chat.py")

if __name__ == "__main__":
    render_landing_page()