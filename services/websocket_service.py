import asyncio
import websockets
import json
import threading
from queue import Queue
from utils.logger import logger

# Shared queue for messages to be sent to clients
message_queue = Queue()

# Store active connections
active_connections = set()

async def notify_clients(message):
    """Send message to all connected clients"""
    if active_connections:
        await asyncio.gather(
            *[connection.send(json.dumps(message)) for connection in active_connections]
        )

async def register(websocket):
    """Register a new client connection"""
    active_connections.add(websocket)
    logger.info(f"Client connected. Total connections: {len(active_connections)}")
    
    try:
        await websocket.send(json.dumps({"type": "connection", "status": "connected"}))
        
        # Keep connection alive and handle incoming messages
        async for message in websocket:
            # You can handle client messages here if needed
            pass
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client connection closed")
    finally:
        active_connections.remove(websocket)

async def websocket_server(host="0.0.0.0", port=8765):
    """Start WebSocket server"""
    server = await websockets.serve(register, host, port)
    logger.info(f"WebSocket server started on {host}:{port}")
    
    # Process messages from the queue and broadcast them
    while True:
        while not message_queue.empty():
            message = message_queue.get()
            await notify_clients(message)
            message_queue.task_done()
        await asyncio.sleep(0.1)

def broadcast_status_update(username, status_data):
    """Add status update to queue for broadcasting"""
    message_queue.put({
        "type": "status_update",
        "username": username,
        "data": status_data
    })
    logger.info(f"Status update queued for broadcast: {status_data.get('status')}")

def start_websocket_server():
    """Start WebSocket server in a separate thread"""
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websocket_server())
        loop.run_forever()
    
    websocket_thread = threading.Thread(target=run_server, daemon=True)
    websocket_thread.start()
    logger.info("WebSocket server thread started")
    return websocket_thread