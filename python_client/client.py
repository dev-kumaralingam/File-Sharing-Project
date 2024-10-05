import asyncio
import websockets
import json
import base64
import hashlib
from getpass import getpass
from cryptography.fernet import Fernet

class FileClient:
    def __init__(self):
        self.uri = "wss://localhost:8765"
        self.websocket = None
        self.fernet = None

    async def connect(self):
        self.websocket = await websockets.connect(self.uri, ssl=True)
        await self.authenticate()

    async def authenticate(self):
        username = input("Enter username: ")
        password = getpass("Enter password: ")
        await self.websocket.send(json.dumps({
            'type': 'auth',
            'username': username,
            'password': password
        }))
        response = await self.websocket.recv()
        data = json.loads(response)
        if data['type'] == 'auth_success':
            print("Authentication successful")
            self.fernet = Fernet(data['encryption_key'].encode())
        else:
            print("Authentication failed:", data['message'])
            exit(1)

    async def handle_communication(self):
        receive_task = asyncio.create_task(self.receive_messages())
        send_task = asyncio.create_task(self.send_messages())
        await asyncio.gather(receive_task, send_task)

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(self.decrypt_message(message))
                if data['type'] == 'message':
                    print(f"{data['sender']}: {data['content']}")
                elif data['type'] == 'file_received':
                    print(f"File received: {data['filename']}")
                elif data['type'] == 'online_users':
                    print("Online users:", ", ".join(data['users']))
                elif data['type'] == 'user_status':
                    print(f"{data['user']} is now {data['status']}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection to server closed")

    async def send_messages(self):
        try:
            while True:
                message = input("Enter a message (or 'file' to send a file, 'users' to get online users): ")
                if message.lower() == 'file':
                    await self.send_file()
                elif message.lower() == 'users':
                    await self.get_online_users()
                else:
                    await self.websocket.send(self.encrypt_message(json.dumps({
                        'type': 'message',
                        'content': message
                    })))
        except websockets.exceptions.ConnectionClosed:
            print("Connection to server closed")

    async def send_file(self):
        filepath = input("Enter the file path: ")
        try:
            with open(filepath, 'rb') as file:
                content = base64.b64encode(file.read()).decode('utf-8')
                filename = filepath.split('/')[-1]
                file_hash = hashlib.sha256(content.encode()).hexdigest()
                await self.websocket.send(self.encrypt_message(json.dumps({
                    'type': 'file_upload',
                    'filename': filename,
                    'content': content,
                    'file_hash': file_hash
                })))
            print(f"File {filename} sent successfully")
        except FileNotFoundError:
            print("File not found")
        except Exception as e:
            print(f"Error sending file: {str(e)}")

    async def get_online_users(self):
        await self.websocket.send(self.encrypt_message(json.dumps({
            'type': 'get_online_users'
        })))

    def encrypt_message(self, message):
        return self.fernet.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted_message):
        return self.fernet.decrypt(encrypted_message.encode()).decode()

async def main():
    client = FileClient()
    await client.connect()
    await client.handle_communication()

if __name__ == "__main__":
    asyncio.run(main())