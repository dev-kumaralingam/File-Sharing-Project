let socket;
let encryptionKey;

function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    socket = new WebSocket('wss://localhost:8765');

    socket.onopen = function() {
        socket.send(JSON.stringify({
            type: 'auth',
            username: username,
            password: password
        }));
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'auth_success') {
            document.getElementById('login-container').style.display = 'none';
            document.getElementById('main-container').style.display = 'block';
            encryptionKey = data.encryption_key;
            displayMessage('System', 'Connected to server');
        } else if (data.type === 'error') {
            alert(data.message);
        } else {
            handleMessage(data);
        }
    };
}

function handleMessage(data) {
    const decryptedData = JSON.parse(decrypt(data.message));
    if (decryptedData.type === 'message') {
        displayMessage(decryptedData.sender, decryptedData.content);
    } else if (decryptedData.type === 'file_upload_success') {
        displayMessage('System', `File uploaded: ${decryptedData.filename}`);
    } else if (decryptedData.type === 'file_download') {
        saveFile(decryptedData.filename, decryptedData.content);
    } else if (decryptedData.type === 'online_users') {
        displayOnlineUsers(decryptedData.users);
    } else if (decryptedData.type === 'user_status') {
        displayMessage('System', `${decryptedData.user} is now ${decryptedData.status}`);
    }
}

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value;
    socket.send(encrypt(JSON.stringify({
    type: 'message',
    content: message
})));
messageInput.value = '';
}

function sendFile() {
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
const reader = new FileReader();

reader.onload = function(e) {
    const content = e.target.result;
    const fileHash = CryptoJS.SHA256(content).toString();

    socket.send(encrypt(JSON.stringify({
        type: 'file_upload',
        filename: file.name,
        content: content,
        file_hash: fileHash
    })));
};

reader.readAsDataURL(file);
}

function getOnlineUsers() {
socket.send(encrypt(JSON.stringify({
    type: 'get_online_users'
})));
}

function displayMessage(sender, content) {
const messagesDiv = document.getElementById('messages');
messagesDiv.innerHTML += `<p><strong>${sender}:</strong> ${content}</p>`;
messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function displayOnlineUsers(users) {
const onlineUsersDiv = document.getElementById('onlineUsers');
onlineUsersDiv.innerHTML = '<h3>Online Users:</h3>';
users.forEach(user => {
    onlineUsersDiv.innerHTML += `<p>${user}</p>`;
});
}

function saveFile(filename, content) {
const link = document.createElement('a');
link.href = content;
link.download = filename;
link.click();
}

function encrypt(message) {
return CryptoJS.AES.encrypt(message, encryptionKey).toString();
}

function decrypt(ciphertext) {
return CryptoJS.AES.decrypt(ciphertext, encryptionKey).toString(CryptoJS.enc.Utf8);
}

// File resume functionality
let currentFileUpload = null;

function resumeFileUpload() {
if (currentFileUpload) {
    const { file, startByte } = currentFileUpload;
    const reader = new FileReader();

    reader.onload = function(e) {
        const content = e.target.result;
        const fileHash = CryptoJS.SHA256(content).toString();

        socket.send(encrypt(JSON.stringify({
            type: 'resume_transfer',
            filename: file.name,
            content: content,
            start_byte: startByte,
            file_hash: fileHash
        })));
    };

    reader.readAsDataURL(file.slice(startByte));
}
}

socket.onclose = function(event) {
if (!event.wasClean) {
    displayMessage('System', 'Connection lost. Attempting to reconnect...');
    setTimeout(login, 5000);  // Attempt to reconnect after 5 seconds
}
};

// Periodic check for online users
setInterval(getOnlineUsers, 60000);  // Check every minute