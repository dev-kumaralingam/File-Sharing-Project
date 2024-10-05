import jwt
import bcrypt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"  # In a real-world scenario, store this securely

# Mock user database (replace with actual database in production)
users = {
    "alice": {
        "password": bcrypt.hashpw("password123".encode(), bcrypt.gensalt()),
        "role": "user"
    },
    "bob": {
        "password": bcrypt.hashpw("password456".encode(), bcrypt.gensalt()),
        "role": "admin"
    }
}

def authenticate_user(username, password):
    if username in users and bcrypt.checkpw(password.encode(), users[username]["password"]):
        return username
    return None

def create_token(username):
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        "sub": username,
        "role": users[username]["role"],
        "exp": expiration
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None