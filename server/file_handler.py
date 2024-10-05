import os
import hashlib
import json
from encryption import encrypt_message, decrypt_message

UPLOAD_DIR = "uploads"

async def handle_file_upload(websocket, data, user):
    filename = data['filename']
    content = data['content']
    file_hash = data['file_hash']
    
    # Create user directory if it doesn't exist
    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, filename)
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Verify file integrity
    if hashlib.sha256(content).hexdigest() == file_hash:
        await websocket.send(encrypt_message(json.dumps({
            'type': 'file_upload_success',
            'filename': filename
        })))
    else:
        os.remove(file_path)
        await websocket.send(encrypt_message(json.dumps({
            'type': 'file_upload_failed',
            'filename': filename,
            'reason': 'File integrity check failed'
        })))

async def handle_file_download(websocket, data, user):
    filename = data['filename']
    file_path = os.path.join(UPLOAD_DIR, user, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        await websocket.send(encrypt_message(json.dumps({
            'type': 'file_download',
            'filename': filename,
            'content': content.decode('latin1'),
            'file_hash': file_hash
        })))
    else:
        await websocket.send(encrypt_message(json.dumps({
            'type': 'file_download_failed',
            'filename': filename,
            'reason': 'File not found'
        })))

async def resume_file_transfer(websocket, data, user):
    filename = data['filename']
    start_byte = data['start_byte']
    
    file_path = os.path.join(UPLOAD_DIR, user, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            f.seek(start_byte)
            content = f.read()
        
        await websocket.send(encrypt_message(json.dumps({
            'type': 'resume_transfer',
            'filename': filename,
            'content': content.decode('latin1'),
            'start_byte': start_byte
        })))
    else:
        await websocket.send(encrypt_message(json.dumps({
            'type': 'resume_transfer_failed',
            'filename': filename,
            'reason': 'File not found'
        })))