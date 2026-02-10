'''
FIREBASE STORAGE AND RETRIEVAL
'''
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# db variable for Firebase
db = None

def init_firebase():
    """Initialise Firebase app and return Firestore information"""
    global db
    
    try:
        # Check if already initialised
        firebase_admin.get_app()
    except ValueError:
        # JSON File (for vscode)
        try:
            cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred)
        except FileNotFoundError:
            # STREAMLIT Secrets folder for Firebase info
            cred_dict = {
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"],
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
            }
            cred = credentials.Certificate(cred_dict)

            firebase_admin.initialize_app(cred)
    
    # Initialize db 
    if db is None:
        db = firestore.client()
    
    return db

def save_to_firebase(user_id, data_type, data):
    """Save data to Firebase of a certain data type"""
    global db

    # INITIALISE db IF NOT DONE ALREADY
    if db is None:
        db = init_firebase()
    
    try:
        doc_ref = db.collection('users').document(user_id).collection(data_type).document('current')
        doc_ref.set({'data': data, 'updated_at': firestore.SERVER_TIMESTAMP})
        return True
    except Exception as e:
        st.error(f"Error saving to Firebase: {e}")
        return False

def load_from_firebase(user_id, data_type):
    """Load data from Firebase of a certain data type"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        doc_ref = db.collection('users').document(user_id).collection(data_type).document('current')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('data', None)
        return None
    except Exception as e:
        st.error(f"Error loading from Firebase: {e}")
        return None

def save_timetable_snapshot(user_id, timetable, activities, events):
    """Saving a Timetable inside timetable_history"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        snapshot_data = {
            'timetable': timetable,
            'activities': activities,
            'events': events,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        db.collection('users').document(user_id).collection('timetable_history').add(snapshot_data)
        return True
    except Exception as e:
        st.error(f"Error saving snapshot: {e}")
        return False

def get_timetable_history(user_id, limit=10):
    """Retrieving Timetable History"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        docs = db.collection('users').document(user_id).collection('timetable_history')\
            .order_by('created_at', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        return [{'id': doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Error loading history: {e}")
        return []
