import streamlit as st
import numpy as np
import pandas as pd
import time
from baccarat_predictor import BaccaratPredictor
from utils import init_session_state
from auth_ui import auth_ui
from firebase_utils import get_db, update_user_data

# Page configuration
st.set_page_config(
    page_title="Pascua Baccarat Predictor",
    page_icon="🎲",
    layout="centered"
)

# Add custom CSS for centering content - Force refresh with timestamp to prevent caching issues
timestamp = str(int(time.time()))
st.markdown(f"""
<style>
/* ---------- CSS with timestamp: {timestamp} -------- */
/* Main container settings for proper centering */
.main .block-container {{
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 2rem;
    margin: 0 auto;
}}

/* Force center all main content - important flag for priority */
.css-1544g2n.e1fqkh3o4 {{
    padding: 5rem 1rem !important;
    max-width: 730px !important;
    margin: 0 auto !important;
}}

/* Center all forms */
div.stForm {{
    max-width: 600px !important;
    margin: 0 auto !important;
}}

/* Center all streamlit elements */
[data-testid="column"] {{
    width: 100% !important;
    margin: 0 auto !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
}}

/* Center radio buttons */
div.row-widget.stRadio > div {{
    display: flex !important;
    justify-content: center !important;
}}

/* Center all buttons */
div.stButton > button {{
    display: block !important;
    margin: 0 auto !important;
}}

/* Center all markdown text */
.element-container div.stMarkdown {{
    text-align: center !important;
    width: 100% !important;
    max-width: 730px !important;
    margin: 0 auto !important;
}}

/* Make specifically user login info left-aligned */
div.stMarkdown:has(p:contains("Logged in as")) {{
    text-align: left !important;
}}

/* Center form elements and text */
.stTextInput, .stDateInput, .stFileUploader {{
    max-width: 500px !important;
    margin: 0 auto !important;
}}

/* Force center all forms and inputs explicitly */
.stTextInput > div, .stDateInput > div, .stFileUploader > div {{
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
    max-width: 500px !important;
    margin: 0 auto !important;
}}

/* Ensure labels are centered too */
.stTextInput label, .stDateInput label, .stFileUploader label {{
    text-align: center !important;
    width: 100% !important;
}}

/* Center streamlit alerts */
[data-baseweb="notification"] {{
    margin: 0 auto !important;
    max-width: 730px !important;
}}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
init_session_state()

# Top bar with Login/User info and How to Use button
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    # Initialize how_to_use state if not exists
    if 'show_how_to_use' not in st.session_state:
        st.session_state.show_how_to_use = False
        
    if st.button("How to Use"):
        st.session_state.show_how_to_use = not st.session_state.show_how_to_use

with col3:
    # User authentication UI
    user_has_access = auth_ui()

# Header display
st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Pascua Baccarat Predictor</h1>", unsafe_allow_html=True)

# Admin panel for armanpascua8@gmail.com
if 'user' in st.session_state and st.session_state.user and st.session_state.user.get('email', '').lower() == 'armanpascua8@gmail.com':
    with st.expander("Admin Panel - Manage User Access"):
        admin_tabs = st.tabs(["Pending Payments", "All Users", "Auto-Verification"])
        
        # Get all users
        db = get_db()
        users_list = []
        pending_users = []
        
        if db:
            try:
                users_ref = db.collection('users')
                users = users_ref.get()
                
                for user in users:
                    user_data = user.to_dict()
                    if user_data.get('email') != 'armanpascua8@gmail.com':  # Skip admin
                        user_info = {
                            'id': user.id,
                            'email': user_data.get('email', 'Unknown'),
                            'has_paid': user_data.get('has_paid', False),
                            'last_login': user_data.get('last_login', 'Never'),
                            'payment_info': user_data.get('payment_info', None),
                            'verification_requested': user_data.get('verification_requested', False)
                        }
                        
                        users_list.append(user_info)
                        
                        # Add to pending list if verification requested
                        if user_info['verification_requested'] and not user_info['has_paid']:
                            pending_users.append(user_info)
            except Exception as e:
                st.error(f"Error fetching users: {e}")
        
        # Tab 1: Pending Payments
        with admin_tabs[0]:
            st.markdown("### Pending Payment Verifications")
            
            if pending_users:
                for user in pending_users:
                    with st.expander(f"📋 {user['email']} - Payment Verification"):
                        payment_info = user['payment_info']
                        
                        if payment_info:
                            st.markdown("#### Payment Details")
                            st.markdown(f"**Payment Method:** {payment_info.get('payment_method', 'Unknown')}")
                            st.markdown(f"**Amount:** ${payment_info.get('amount', 'Unknown')}")
                            st.markdown(f"**Transaction ID:** {payment_info.get('transaction_id', 'Unknown')}")
                            st.markdown(f"**Payment Reference:** {payment_info.get('payment_reference', 'Unknown')}")
                            st.markdown(f"**Payment Date:** {payment_info.get('payment_date', 'Unknown')}")
                            
                            # Display payment proof if available
                            if payment_info.get('payment_proof'):
                                st.markdown("#### Payment Proof")
                                try:
                                    import base64
                                    from io import BytesIO
                                    
                                    image_data = base64.b64decode(payment_info['payment_proof'])
                                    st.image(BytesIO(image_data), caption="Payment Screenshot")
                                except Exception:
                                    st.error("Could not display payment proof image")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("Approve Payment", key=f"approve_{user['id']}"):
                                    # Mark user as paid with 10 years access
                                    import datetime
                                    payment_expires = datetime.datetime.now() + datetime.timedelta(days=365*10)
                                    
                                    success = update_user_data(user['id'], {
                                        'has_paid': True,
                                        'payment_expires': payment_expires,
                                        'last_payment_date': datetime.datetime.now(),
                                        'last_payment_amount': payment_info.get('amount', 99),
                                        'last_payment_method': payment_info.get('payment_method', 'Verified payment'),
                                        'verification_requested': False,
                                        'payment_info': {
                                            **payment_info,
                                            'verification_status': 'approved',
                                            'verified_at': datetime.datetime.now(),
                                            'verified_by': 'admin'
                                        }
                                    })
                                    
                                    if success:
                                        st.success(f"Access granted to {user['email']}")
                                        st.rerun()
                                    else:
                                        st.error("Error updating user data")
                            
                            with col2:
                                if st.button("Reject", key=f"reject_{user['id']}"):
                                    success = update_user_data(user['id'], {
                                        'verification_requested': False,
                                        'payment_info': {
                                            **payment_info,
                                            'verification_status': 'rejected',
                                            'verified_at': datetime.datetime.now(),
                                            'verified_by': 'admin'
                                        }
                                    })
                                    
                                    if success:
                                        st.success(f"Payment from {user['email']} was rejected")
                                        st.rerun()
                                    else:
                                        st.error("Error updating user data")
                        else:
                            st.markdown("No payment information available")
            else:
                st.markdown("No pending payment verifications")
        
        # Tab 2: All Users
        with admin_tabs[1]:
            st.markdown("### All Users")
            
            if users_list:
                for user in users_list:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{user['email']}**")
                    
                    with col2:
                        st.markdown("✅ Paid" if user['has_paid'] else "❌ Not Paid")
                    
                    with col3:
                        if not user['has_paid']:
                            if st.button("Approve", key=f"all_approve_{user['id']}"):
                                # Mark user as paid with 10 years access
                                import datetime
                                payment_expires = datetime.datetime.now() + datetime.timedelta(days=365*10)
                                
                                success = update_user_data(user['id'], {
                                    'has_paid': True,
                                    'payment_expires': payment_expires,
                                    'last_payment_date': datetime.datetime.now(),
                                    'last_payment_amount': 99,
                                    'last_payment_method': 'Manual approval'
                                })
                                
                                if success:
                                    st.success(f"Access granted to {user['email']}")
                                    st.rerun()
                                else:
                                    st.error("Error updating user data")
            else:
                st.markdown("No users found")
        
        # Tab 3: Auto-Verification Settings 
        with admin_tabs[2]:
            st.markdown("### Payment Auto-Verification Settings")
            st.markdown("""
            #### How Automatic Verification Works
            
            1. When users make payments, they submit payment proof with their unique reference code
            2. The system stores this information and marks their account as pending verification
            3. You can verify these payments in the 'Pending Payments' tab
            4. You can also configure rules for automatic verification below
            """)
            
            st.markdown("#### Auto-Verification Rules")
            
            auto_verify_gcash = st.checkbox("Auto-verify GCash payments", value=False)
            auto_verify_paypal = st.checkbox("Auto-verify PayPal payments", value=False)
            
            if auto_verify_gcash or auto_verify_paypal:
                st.warning("""
                ⚠️ Caution: Full auto-verification requires integration with payment provider APIs for security.
                Currently, you'll still need to verify payments manually by checking the reference codes.
                
                For complete automation, contact a developer to integrate with GCash/PayPal APIs.
                """)
            
            st.markdown("#### Auto-Verification Status")
            st.info("Auto-verification is currently in manual mode. Payments require your approval in the Pending Payments tab.")

# How to Use guide
if st.session_state.show_how_to_use:
    st.info("""
    ### How to Use the Pascua Baccarat Predictor
    
    A simple, step-by-step guide for using the predictor effectively:
    
    The Pascua Baccarat Predictor is a smart tool that analyzes game outcomes and instantly predicts the next likely result: Player, Banker, or Tie.
    
    It follows a switching strategy:
    * If the previous prediction given wins → stick with the prediction
    * If the prediction loses and the opposite wins → switch to the opposite 
    * If you lose 3 times in a row → STOP betting, wait if the prediction win again and place bets again.
    
    ### Enter Previous Game Results
    Type in the outcomes one by one using these buttons:
    * BANKER for Banker
    * PLAYER for Player 
    * TIE for Tie
    
    ### Disclaimer
    The Pascua Baccarat Predictor is designed to support decision-making based on historical patterns. It does not guarantee 100% accurate predictions or consistent winnings.
    
    Baccarat is a game of chance, and outcomes are random.
    Use this tool responsibly and for entertainment purposes only.
    """)

# Main application content - only show if user has access
if user_has_access:
    # Header spacing
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Create a predictor instance
    predictor = BaccaratPredictor(st.session_state.history)
    
    # Get prediction and confidence level
    prediction, confidence = predictor.predict_next()
    st.session_state.prediction = prediction
    
    # Prediction bar labels
    col1, col2 = st.columns([10, 2])
    
    with col1:
        st.markdown("<p style='text-align: left; margin-bottom: 5px;'>Prediction</p>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<p style='text-align: right; margin-bottom: 5px;'>Opposite</p>", unsafe_allow_html=True)
    
    # Prediction bar - using single column for the bar
    # Determine how to display the prediction bar based on the prediction
    if not st.session_state.history:
        # No outcomes entered yet - show gray bar
        st.markdown(
            f"""
            <div style='display: flex; width: 100%; height: 30px; border-radius: 5px; overflow: hidden;'>
                <div style='width: 100%; background-color: #6c757d;'></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif prediction == "T":  # Tie prediction - full green bar
        st.markdown(
            f"""
            <div style='display: flex; width: 100%; height: 30px; border-radius: 5px; overflow: hidden;'>
                <div style='width: 100%; background-color: #198754;'></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:  # Player or Banker prediction - split bar
        player_color = "#0d6efd"  # Blue for Player
        banker_color = "#dc3545"  # Red for Banker
        
        # Create bar with player color on left if predicting player, otherwise banker color on left
        if prediction == "P":
            left_color = player_color
            right_color = banker_color
        else:
            left_color = banker_color
            right_color = player_color
        
        st.markdown(
            f"""
            <div style='display: flex; width: 100%; height: 30px; border-radius: 5px; overflow: hidden;'>
                <div style='width: 50%; background-color: {left_color};'></div>
                <div style='width: 50%; background-color: {right_color};'></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Input form for the result
    with st.form(key="result_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            delete_button = st.form_submit_button(
                "DELETE PREVIOUS", 
                use_container_width=True,
                type="secondary"
            )
        
        with col2:
            reset_button = st.form_submit_button(
                "RESET SESSION", 
                use_container_width=True,
                type="secondary"
            )
        
        # Buttons for submitting result
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(
                """
                <style>
                div[data-testid="stButton"] button[kind="secondary"]:nth-child(1) {
                    background-color: #dc3545;
                    color: white;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            banker_button = st.form_submit_button(
                "BANKER", 
                use_container_width=True,
                type="secondary"
            )
        
        with col2:
            st.markdown(
                """
                <style>
                div[data-testid="stButton"] button[kind="secondary"]:nth-child(3) {
                    background-color: #0d6efd;
                    color: white;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            player_button = st.form_submit_button(
                "PLAYER", 
                use_container_width=True,
                type="secondary"
            )
        
        with col3:
            st.markdown(
                """
                <style>
                div[data-testid="stButton"] button[kind="secondary"]:nth-child(5) {
                    background-color: #198754;
                    color: white;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            tie_button = st.form_submit_button(
                "TIE", 
                use_container_width=True,
                type="secondary"
            )
    
    # Handle form submissions
    if banker_button:
        st.session_state.history.append("B")
        st.rerun()
    
    if player_button:
        st.session_state.history.append("P")
        st.rerun()
    
    if tie_button:
        st.session_state.history.append("T")
        st.rerun()
    
    if delete_button and st.session_state.history:
        st.session_state.history.pop()
        st.rerun()
    
    if reset_button:
        st.session_state.history = []
        st.rerun()
    
    # Display history
    if st.session_state.history:
        st.markdown("<h3 style='text-align: center; margin-top: 20px;'>History</h3>", unsafe_allow_html=True)
        
        # Create blocks of 6 items per row
        rows = [st.session_state.history[i:i+6] for i in range(0, len(st.session_state.history), 6)]
        
        for row in rows:
            cols = st.columns(6)
            for i, result in enumerate(row):
                # BANKER: red, PLAYER: blue, TIE: green
                color = "#dc3545" if result == "B" else "#0d6efd" if result == "P" else "#198754"
                
                with cols[i]:
                    st.markdown(
                        f"""
                        <div style='background-color: {color}; color: white; 
                        padding: 10px; text-align: center; border-radius: 5px;'>
                        <strong>{result}</strong>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
else:
    # If user does not have access, show a message
    if 'user' not in st.session_state or st.session_state.user is None:
        st.markdown("""
        ## Welcome to Pascua Baccarat Predictor
        
        Please log in with your Google account to access the predictor. 
        New users get a free 3-minute trial.
        
        After the trial, you'll need to purchase access to continue using the predictor.
        """)
    # If user is logged in but trial has expired or they haven't paid,
    # the payment UI will be shown by the auth_ui() function
