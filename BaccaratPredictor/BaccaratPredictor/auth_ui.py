import streamlit as st
import time
import datetime
from firebase_utils import (
    initialize_firebase, get_user_data, update_user_data, check_user_payment_status, record_payment
)
from streamlit_extras.colored_header import colored_header

def init_auth_session_state():
    """Initialize session state variables for authentication"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None
    if 'trial_start_time' not in st.session_state:
        st.session_state.trial_start_time = None
    if 'show_payment' not in st.session_state:
        st.session_state.show_payment = False
    if 'login_form_submitted' not in st.session_state:
        st.session_state.login_form_submitted = False

def simple_login_form():
    """Display a simple login form"""
    # Initialize Firebase
    initialize_firebase()

    # Add CSS for centering
    st.markdown("""
    <style>
    div.stForm {
        max-width: 500px;
        margin: 0 auto;
    }
    div.stButton > button {
        display: block;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

    # Centered heading
    st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)

    # Login form
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        register_mode = st.checkbox("New user? Register here")
        submit_button = st.form_submit_button("Sign In" if not register_mode else "Register")
        form_submit = submit_button

    if form_submit:
        st.session_state.login_form_submitted = True

        if not email or not password:
            st.error("Please enter both email and password")
            return False

        if register_mode:
            # Register new user
            user_id = f"user_{email.replace('@', '_at_').replace('.', '_dot_')}"

            # Create user data
            user_data = {
                'email': email,
                'created_at': datetime.datetime.now(),
                'last_login': datetime.datetime.now(),
                'free_trial_used': False,
                'has_paid': False,
                'payment_expires': None
            }

            # Update user in database
            if update_user_data(user_id, user_data):
                st.success("Registration successful! You can now sign in.")

                # Store user in session
                st.session_state.user = {
                    'email': email,
                    'name': email.split('@')[0]
                }
                st.session_state.user_id = user_id
                st.session_state.auth_status = "authenticated"

                # Start free trial
                st.session_state.trial_start_time = time.time()
                st.session_state.show_payment = False

                st.rerun()
            else:
                st.error("Error creating account. Please try again.")
        else:
            # Login existing user
            user_id = f"user_{email.replace('@', '_at_').replace('.', '_dot_')}"
            user_data = get_user_data(user_id)

            if user_data:
                # User exists, update login time
                update_user_data(user_id, {'last_login': datetime.datetime.now()})

                # Store user in session
                st.session_state.user = {
                    'email': email,
                    'name': email.split('@')[0]
                }
                st.session_state.user_id = user_id
                st.session_state.auth_status = "authenticated"

                # Check payment status
                has_access = check_user_payment_status(user_id)

                if has_access:
                    st.session_state.show_payment = False
                else:
                    # Check if free trial is available
                    if not user_data.get('free_trial_used', True):
                        st.session_state.trial_start_time = time.time()
                        st.session_state.show_payment = False
                    else:
                        st.session_state.show_payment = True

                st.rerun()
            else:
                st.error("User not found. Please register first.")

        return True

    return False

def display_user_info():
    """Display user information"""
    if st.session_state.user:
        # Center the user info with columns
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"**Logged in as: {st.session_state.user.get('name', 'User')}**")
            st.markdown(f"{st.session_state.user.get('email', '')}")

        # Centered logout button
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            st.markdown("""
            <style>
            [data-testid="stButton"] {
                width: 100%;
                margin: 0 auto;
            }
            [data-testid="stButton"] button {
                width: 100%;
                text-align: center;
            }
            </style>
            """, unsafe_allow_html=True)
            # Clear session state
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.auth_status = None
            st.session_state.trial_start_time = None
            st.session_state.show_payment = False
            st.session_state.login_form_submitted = False
            st.rerun()

def check_trial_expired():
    """Check if the free trial period (3 minutes) has expired"""
    if st.session_state.trial_start_time:
        elapsed_time = time.time() - st.session_state.trial_start_time
        remaining_time = max(0, 180 - elapsed_time)  # 3 minutes = 180 seconds

        # Format the time display
        mins = int(remaining_time // 60)
        secs = int(remaining_time % 60)
        time_display = f"{mins:02d}:{secs:02d}"

        # Display the remaining time with a progress bar
        colored_header(
            label=f"Free Trial Time Remaining: {time_display}",
            description="",
            color_name="blue-70"
        )

        progress = 1 - (remaining_time / 180)  # 3 minutes = 180 seconds
        st.progress(progress)

        # Check if trial has expired
        if remaining_time <= 0:
            # Immediately mark trial as expired
            st.session_state.show_payment = True
            st.session_state.trial_start_time = None

            # Mark the trial as used in database
            if st.session_state.user_id:
                update_user_data(st.session_state.user_id, {'free_trial_used': True})

            # Show a message that trial has ended and redirect to payment
            st.error("Your free trial has ended. Please purchase to continue using the predictor.")

            # Force a rerun to show payment page immediately
            time.sleep(1)  # Small delay to ensure user sees the message
            st.rerun()

            return True
        return False
    return True

def display_payment_options():
    """Display payment options"""
    # Create a container to center and constrain the content width
    payment_container = st.container()

    col1, col2, col3 = st.columns([1, 10, 1])
    with col2:
        # Create centered layout for payment section
        st.markdown("""
        <div style="background-color: #f8d7da; color: #721c24; padding: 1em; border-radius: 10px; text-align: center; margin-bottom: 1em; max-width: 500px; margin-left: auto; margin-right: auto;">
            <h2 style="margin-top: 0;">Your Free Trial Has Ended</h2>
            <p style="font-size: 1.2em;">To continue using the Pascua Baccarat Predictor, please purchase access below.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Payment header
        colored_header(
            label="Unlock Full Access",
            description="One-time payment for lifetime access to Pascua Baccarat Predictor",
            color_name="blue-70"
        )

        # Payment amount
        st.markdown("<h3 style='text-align: center;'>One-time Payment: $99 USD</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Get lifetime access to the Pascua Baccarat Predictor with a one-time payment.</p>", unsafe_allow_html=True)

        amount = 99
        duration = 365 * 10  # 10 years (essentially lifetime)

        # Payment method selection
        st.markdown("<h4 style='text-align: center; margin-top: 20px;'>Select Payment Method</h4>", unsafe_allow_html=True)

        # Center radio buttons
        st.markdown("""
        <style>
        div.row-widget.stRadio > div {
            display: flex;
            justify-content: center;
        }
        </style>
        """, unsafe_allow_html=True)

        payment_method = st.radio(
            "",  # Empty label since we have a header above
            ["GCash", "PayPal"],
            label_visibility="collapsed"
        )

        # Payment reference code
        import uuid
        import datetime

        if 'payment_ref_code' not in st.session_state:
            # Generate a unique payment reference code with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
            unique_id = str(uuid.uuid4())[:8]
            st.session_state.payment_ref_code = f"PBP-{timestamp}-{unique_id}"

        # Payment instructions
        st.markdown("<h4 style='text-align: center; margin-top: 20px;'>Payment Instructions</h4>", unsafe_allow_html=True)

        # Payment info box
        payment_info = ""
        if payment_method == "GCash":
            payment_info = f"""
            <div style="background-color: #e9ecef; padding: 20px; border-radius: 5px; margin: 20px 0; width: 100%; display: flex; flex-direction: column; align-items: center; text-align: center;">
                <p style="width: 100%;"><strong>1.</strong> Open your GCash app</p>
                <p style="width: 100%;"><strong>2.</strong> Send $99 USD to: <strong>09703291591</strong></p>
                <p style="width: 100%;"><strong>3.</strong> Use this exact reference code: <strong>{st.session_state.payment_ref_code}</strong></p>
                <p style="width: 100%;"><strong>4.</strong> Take a screenshot of your payment confirmation</p>
            </div>
            """
        else:
            payment_info = f"""
            <div style="background-color: #e9ecef; padding: 20px; border-radius: 5px; margin: 20px 0; width: 100%; display: flex; flex-direction: column; align-items: center; text-align: center;">
                <p style="width: 100%;"><strong>1.</strong> Send $99 USD to: <strong>armanpascua8@gmail.com</strong></p>
                <p style="width: 100%;"><strong>2.</strong> Use this exact reference code: <strong>{st.session_state.payment_ref_code}</strong></p>
                <p style="width: 100%;"><strong>3.</strong> Take a screenshot of your payment confirmation</p>
            </div>
            """

        st.markdown(payment_info, unsafe_allow_html=True)

        # Payment verification form
        st.markdown("<h4 style='text-align: center; margin-top: 30px;'>Verify Your Payment</h4>", unsafe_allow_html=True)

        # Center all content CSS
        st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 800px !important;
        }
        .stApp {
            max-width: 800px;
            margin: 0 auto;
        }
        .element-container {
            width: 100% !important;
            margin: 0 auto !important;
            text-align: center !important;
        }
        .stForm > div {
            max-width: 800px !important;
            margin: 0 auto !important;
        }
        .stRadio > div {
            display: flex;
            justify-content: center;
        }
        .stMarkdown {
            width: 100% !important;
            margin: 0 auto !important;
            text-align: center !important;
        }
        .stMarkdown p {
            text-align: center !important;
        }
        div[data-testid="stFileUploader"] {
            width: 100% !important;
            max-width: 400px !important;
            margin: 0 auto !important;
        }
        .stDateInput {
            width: 100% !important;
            max-width: 400px !important;
            margin: 0 auto !important;
        }
        .stTextInput {
            width: 100% !important;
            max-width: 400px !important;
            margin: 0 auto !important;
        }
        .stForm > form {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
            max-width: 400px;
            margin: 0 auto;
        }
        h1, h2, h3, h4, h5, h6, p {
            text-align: center !important;
            width: 100% !important;
        }
        div[data-testid="stForm"] {
            width: 100%;
            max-width: 400px;
            margin: 0 auto;
        }
        </style>
        """, unsafe_allow_html=True)

        # Payment verification form
        with st.form("payment_verification_form"):
            transaction_id = st.text_input("Transaction ID or Reference Number")
            payment_date = st.date_input("Payment Date")
            payment_proof = st.file_uploader("Upload Payment Screenshot", type=["jpg", "jpeg", "png"])

            # Submit button (centered via CSS)
            submit_button = st.form_submit_button("Submit Payment Information")

            if submit_button:
                if not transaction_id or not payment_proof:
                    st.error("Please provide the transaction ID and upload the payment screenshot.")
                else:
                    # Store payment verification data in user record
                    if st.session_state.user_id:
                        # Store payment information
                        payment_info = {
                            'payment_method': payment_method,
                            'amount': amount,
                            'transaction_id': transaction_id,
                            'payment_date': payment_date,
                            'payment_reference': st.session_state.payment_ref_code,
                            'verification_status': 'pending',
                            'verification_requested_at': datetime.datetime.now(),
                            'payment_proof_provided': True
                        }

                        # Store payment proof as base64 string
                        import base64
                        file_bytes = payment_proof.getvalue()
                        file_base64 = base64.b64encode(file_bytes).decode()
                        payment_info['payment_proof'] = file_base64

                        # Update user data
                        success = update_user_data(st.session_state.user_id, {
                            'payment_info': payment_info,
                            'verification_requested': True
                        })

                        if success:
                            st.success("""
                            Thank you! Your payment information has been submitted successfully.
                            Your access is being processed and will be activated shortly.
                            Please check back in a few minutes.
                            """)
                        else:
                            st.error("Error submitting payment information. Please try again or contact support.")

        # Help section
        st.markdown("<h4 style='text-align: center; margin-top: 20px;'>Need Help?</h4>", unsafe_allow_html=True)

        help_info = """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; text-align: center;">
            <p>If you experience any issues with payment, please contact:</p>
            <p><strong>Email:</strong> armanpascua8@gmail.com</p>
            <p><strong>Phone:</strong> 09703291591</p>
            <p>Include your reference code for faster assistance.</p>
        </div>
        """

        st.markdown(help_info, unsafe_allow_html=True)

def auth_ui():
    """Main authentication UI function"""
    initialize_firebase()
    init_auth_session_state()

    # Display login form or user info
    if not st.session_state.user:
        simple_login_form()
        return False
    else:
        display_user_info()

        # Check if the user is armanpascua8@gmail.com (owner account - automatic access)
        if st.session_state.user.get('email', '').lower() == 'armanpascua8@gmail.com':
            return True

        # Check if user data exists in Firebase
        user_data = None
        if st.session_state.user_id:
            user_data = get_user_data(st.session_state.user_id)

        # Check if the user has verification pending
        if user_data and user_data.get('verification_requested', False) and not user_data.get('has_paid', False):
            st.success("""
            ### Payment Verification in Progress

            Thank you for submitting your payment information. Your verification is being processed.
            You will receive access as soon as your payment is verified.

            Verifications are typically processed within 1-2 hours during business hours.
            """)
            return False

        # Check if trial period has expired in database
        if user_data and user_data.get('free_trial_used', False) and not user_data.get('has_paid', False):
            # Force show payment if trial has been used according to database
            st.session_state.show_payment = True
            st.session_state.trial_start_time = None

        # Check if the user has payment or is in trial
        if st.session_state.show_payment:
            display_payment_options()
            return False
        elif st.session_state.trial_start_time is not None:
            # Check if trial has expired based on timer
            if check_trial_expired():
                display_payment_options()  # Show payment options immediately if expired
                return False
            return True
        elif user_data and user_data.get('has_paid', False):
            # User has paid
            return True
        else:
            # Check if we should start a trial
            if user_data and not user_data.get('free_trial_used', True):
                # Start trial if it hasn't been used
                st.session_state.trial_start_time = time.time()
                return True
            else:
                # Show payment options as fallback
                st.session_state.show_payment = True
                display_payment_options()
                return False