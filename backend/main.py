from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import aioredis

app = FastAPI()

redis = aioredis.from_url("redis://localhost", decode_responses=True)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    channel_name = f"chat_{client_id}"

    async with redis.subscribe(channel_name) as subscriber:
        while await subscriber.wait_message():
            message = await subscriber.get(encoding="utf-8")
            await websocket.send_text(message)

@app.post("/send/{client_id}")
async def send_message(client_id: str, message: str):
    channel_name = f"chat_{client_id}"
    await redis.publish(channel_name, message)
    return {"status": "Message sent"}

@app.get("/")
async def read_root():
    html_content = """
    <html>
        <head>
            <title>Chat App</title>
            <link rel="stylesheet" type="text/css" href="/static/style.css">
        </head>
        <body>
            <h1>FastAPI Chat App</h1>
            <div id="messages"></div>
            <textarea id="messageInput" placeholder="Type your message..."></textarea>
            <button onclick="sendMessage()">Send</button>
            <script>
                var client_id = prompt("Enter your client ID:");
                var ws = new WebSocket("ws://localhost:8000/ws/" + client_id);
                ws.onmessage = function(event) {
                    var messages = document.getElementById("messages");
                    messages.innerHTML += '<p>' + event.data + '</p>';
                };
                function sendMessage() {
                    var messageInput = document.getElementById("messageInput");
                    ws.send(messageInput.value);
                    messageInput.value = '';
                }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
