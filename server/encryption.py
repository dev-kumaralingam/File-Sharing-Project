from cryptography.fernet import Fernet

# In a real-world scenario, store this key securely and don't hardcode it
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_message(message):
    return fernet.encrypt(message.encode()).decode()

def decrypt_message(encrypted_message):
    return fernet.decrypt(encrypted_message.encode()).decode()