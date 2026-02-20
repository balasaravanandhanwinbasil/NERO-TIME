'''
FIREBASE STORAGE AND RETRIEVAL + FIREAUTH
'''
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import secrets

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

# ==================== AUTHENTICATION ====================

def hash_password(password, salt=None):
    """Hashing passwords for security"""
    if salt is None:
        salt = secrets.token_hex(32)

    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex(), salt

def verify_password(stored_hash, stored_salt, password):
    """Verify a password against stored hash"""
    hashed, _ = hash_password(password, stored_salt)
    return hashed == stored_hash

def create_user(username, password, email=None):
    """Create a new user account"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        # Check if username already exists
        users_ref = db.collection('users')
        existing_user = users_ref.where('username', '==', username).limit(1).stream()
        
        if list(existing_user):
            return {"success": False, "message": "Username already exists"}
        
        # Hash the password
        password_hash, salt = hash_password(password)
        
        # Create user document with auto-generated ID
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'salt': salt,
            'created_at': firestore.SERVER_TIMESTAMP,
            'tutorial_completed': False
        }
        
        doc_ref = users_ref.add(user_data)
        user_id = doc_ref[1].id  # Get the generated document ID
        
        return {
            "success": True, 
            "message": "Account created successfully!",
            "user_id": user_id
        }
    
    except Exception as e:
        return {"success": False, "message": f"Error creating account: {str(e)}"}

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        # Find user by username
        users_ref = db.collection('users')
        user_query = users_ref.where('username', '==', username).limit(1).stream()
        
        users = list(user_query)
        if not users:
            return {"success": False, "message": "Invalid username or password"}
        
        user_doc = users[0]
        user_data = user_doc.to_dict()
        
        # Verify password
        stored_hash = user_data.get('password_hash')
        stored_salt = user_data.get('salt')
        
        if verify_password(stored_hash, stored_salt, password):
            return {
                "success": True,
                "message": "Login successful!",
                "user_id": user_doc.id,
                "username": user_data.get('username'),
                "email": user_data.get('email'),
                "tutorial_completed": user_data.get("tutorial_completed", False)
            }
        else:
            return {"success": False, "message": "Invalid username or password"}
    
    except Exception as e:
        return {"success": False, "message": f"Error during login: {str(e)}"}

def check_username_exists(username):
    """Check if a username already exists"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        users_ref = db.collection('users')
        existing_user = users_ref.where('username', '==', username).limit(1).stream()
        return len(list(existing_user)) > 0
    except Exception as e:
        st.error(f"Error checking username: {e}")
        return False

def update_user_email(user_id, new_email):
    """Update user's email address"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        user_ref = db.collection('users').document(user_id)
        user_ref.update({'email': new_email})
        return {"success": True, "message": "Email updated successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Error updating email: {str(e)}"}

def change_password(user_id, old_password, new_password):
    """Change user's password"""
    global db
    if db is None:
        db = init_firebase()
    
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return {"success": False, "message": "User not found"}
        
        user_data = user_doc.to_dict()
        
        # Verify old password
        if not verify_password(user_data['password_hash'], user_data['salt'], old_password):
            return {"success": False, "message": "Incorrect current password"}
        
        # Hash new password
        new_hash, new_salt = hash_password(new_password)
        
        # Update password
        user_ref.update({
            'password_hash': new_hash,
            'salt': new_salt
        })
        
        return {"success": True, "message": "Password changed successfully!"}
    
    except Exception as e:
        return {"success": False, "message": f"Error changing password: {str(e)}"}

# ==================== DATA STORAGE FUNCTIONS ====================

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
