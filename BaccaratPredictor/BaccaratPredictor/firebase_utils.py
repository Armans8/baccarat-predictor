import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import streamlit as st

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    if not firebase_admin._apps:
        try:
            # Try to get credentials from Streamlit secrets (new format)
            try:
                from streamlit import secrets
                if 'firebase' in secrets:
                    # Create a dictionary from the individual fields in secrets.toml
                    cred_dict = {
                        "type": secrets.firebase.type,
                        "project_id": secrets.firebase.project_id,
                        "private_key_id": secrets.firebase.private_key_id,
                        "private_key": secrets.firebase.private_key,
                        "client_email": secrets.firebase.client_email,
                        "client_id": secrets.firebase.client_id,
                        "auth_uri": secrets.firebase.auth_uri,
                        "token_uri": secrets.firebase.token_uri,
                        "auth_provider_x509_cert_url": secrets.firebase.auth_provider_x509_cert_url,
                        "client_x509_cert_url": secrets.firebase.client_x509_cert_url,
                        "universe_domain": secrets.firebase.universe_domain
                    }
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    return True
            except Exception as e:
                st.warning(f"Could not load from Streamlit secrets, trying environment variable: {e}")
                
            # Fall back to environment variable (original format)
            firebase_creds_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
            if firebase_creds_json:
                try:
                    cred_dict = json.loads(firebase_creds_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    return True
                except Exception as e:
                    st.error(f"Error initializing Firebase from environment: {e}")
                    return False
            else:
                st.error("Firebase credentials not found in environment variables or Streamlit secrets")
                return False
        except Exception as e:
            st.error(f"Error initializing Firebase: {e}")
            return False
    return True

# Database Operations
def get_db():
    """Get Firestore database instance"""
    if initialize_firebase():
        return firestore.client()
    return None

def get_user_data(user_id):
    """Get user data from Firestore"""
    db = get_db()
    if not db:
        return None
        
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            return user_doc.to_dict()
        else:
            return None
    except firebase_admin.exceptions.FirebaseError as e:
        st.error(f"Firebase error: {e}")
        return None
    except Exception as e:
        st.error("An unexpected error occurred. Please try again later.")
        print(f"Error details: {e}")  # Log for debugging
        return None

def update_user_data(user_id, data):
    """Update user data in Firestore"""
    db = get_db()
    if not db:
        return False
        
    try:
        user_ref = db.collection('users').document(user_id)
        
        # Check if document exists
        doc = user_ref.get()
        if doc.exists:
            # Update existing document
            user_ref.update(data)
        else:
            # Create new document
            user_ref.set(data)
            
        return True
    except Exception as e:
        st.error(f"Error updating user data: {e}")
        return False

def check_user_payment_status(user_id):
    """Check if user has active payment or free trial"""
    user_data = get_user_data(user_id)
    
    if not user_data:
        return False
    
    # Check if user has paid
    if user_data.get('has_paid', False):
        # Check if payment has expired
        payment_expires = user_data.get('payment_expires')
        if payment_expires:
            try:
                # Handle timezone-aware and naive datetime objects safely
                now = datetime.datetime.now()
                if hasattr(payment_expires, 'tzinfo') and payment_expires.tzinfo:
                    # Convert now to timezone-aware
                    import pytz
                    now = pytz.UTC.localize(now)
                # Check if payment is still valid
                return payment_expires > now
            except Exception:
                # If there's any error comparing datetimes, just return True
                # This ensures users don't lose access due to technical issues
                return True
        return True
    
    # Check if user is in free trial
    if not user_data.get('free_trial_used', True):
        # Mark the free trial as used
        update_user_data(user_id, {
            'free_trial_used': True,
            'free_trial_start': datetime.datetime.now()
        })
        return True
        
    return False

def record_payment(user_id, payment_method, amount, duration_days=30):
    """Record a payment in the database"""
    db = get_db()
    if not db:
        return False
        
    # Calculate payment expiration date
    payment_expires = datetime.datetime.now() + datetime.timedelta(days=duration_days)
    
    try:
        # Update user data
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'has_paid': True,
            'payment_expires': payment_expires,
            'last_payment_date': datetime.datetime.now(),
            'last_payment_amount': amount,
            'last_payment_method': payment_method
        })
        
        # Add payment record
        payment_data = {
            'user_id': user_id,
            'payment_method': payment_method,
            'amount': amount,
            'date': datetime.datetime.now(),
            'expires': payment_expires,
            'status': 'completed'
        }
        
        db.collection('payments').add(payment_data)
        return True
    except Exception as e:
        st.error(f"Error recording payment: {e}")
        return False
