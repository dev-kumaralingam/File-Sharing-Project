import asyncio
import websockets
import json
import ssl
from auth import authenticate_user, create_token
from file_handler import handle_file_upload, handle_file_download, resume_file_transfer
from encryption import encrypt_message, decrypt_message
from database import update_user_status, get_online_users

connected_clients = {}

async def handle_client(websocket, path):
    try:
        # Authentication
        auth_message = await websocket.recv()
        auth_data = json.loads(auth_message)
        user = authenticate_user(auth_data['username'], auth_data['password'])
        if not user:
            await websocket.send(json.dumps({'type': 'error', 'message': 'Authentication failed'}))
            return

        token = create_token(user)
        await websocket.send(json.dumps({'type': 'auth_success', 'token': token}))

        # Add client to connected clients
        connected_clients[user] = websocket
        update_user_status(user, 'online')
        await broadcast_user_status(user, 'online')

        async for message in websocket:
            data = json.loads(decrypt_message(message))
            if data['type'] == 'file_upload':
                await handle_file_upload(websocket, data, user)
            elif data['type'] == 'file_download':
                await handle_file_download(websocket, data, user)
            elif data['type'] == 'resume_transfer':
                await resume_file_transfer(websocket, data, user)
            elif data['type'] == 'message':
                await broadcast(encrypt_message(json.dumps({
                    'type': 'message',
                    'sender': user,
                    'content': data['content']
                })))
            elif data['type'] == 'get_online_users':
                online_users = get_online_users()
                await websocket.send(encrypt_message(json.dumps({
                    'type': 'online_users',
                    'users': online_users
                })))

    finally:
        if user in connected_clients:
            del connected_clients[user]
            update_user_status(user, 'offline')
            await broadcast_user_status(user, 'offline')

async def broadcast(message):
    for client in connected_clients.values():
        await client.send(message)

async def broadcast_user_status(user, status):
    await broadcast(encrypt_message(json.dumps({
        'type': 'user_status',
        'user': user,
        'status': status
    })))

if __name__ == "__main__":
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('path/to/cert.pem', 'path/to/key.pem')
    
    server = websockets.serve(handle_client, "localhost", 8765, ssl=ssl_context)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()