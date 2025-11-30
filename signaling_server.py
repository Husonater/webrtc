#!/usr/bin/env python3
"""
WebRTC Signalisierungsserver
Demonstriert Sicherheitsrisiken bei unverschlüsselter Signalisierung
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
import websockets
from websockets.server import WebSocketServerProtocol

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verbindungsverwaltung
class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.clients: Set[WebSocketServerProtocol] = set()
        
    def add_client(self, websocket: WebSocketServerProtocol):
        self.clients.add(websocket)
        logger.info(f"Client joined room {self.room_id}. Total clients: {len(self.clients)}")
        
    def remove_client(self, websocket: WebSocketServerProtocol):
        self.clients.discard(websocket)
        logger.info(f"Client left room {self.room_id}. Remaining clients: {len(self.clients)}")
        
    async def broadcast(self, message: str, sender: WebSocketServerProtocol):
        """Sende Nachricht an alle Clients außer dem Sender"""
        disconnected = set()
        for client in self.clients:
            if client != sender:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
        
        # Entferne getrennte Clients
        for client in disconnected:
            self.remove_client(client)


class SignalingServer:
    def __init__(self, encrypted: bool = False):
        self.rooms: Dict[str, Room] = {}
        self.encrypted = encrypted
        self.message_log = []
        
    def get_room(self, room_id: str) -> Room:
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id)
        return self.rooms[room_id]
    
    def log_message(self, msg_type: str, room_id: str, data: dict):
        """Logge Nachrichten für Sicherheitsanalyse"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': msg_type,
            'room': room_id,
            'data': data
        }
        self.message_log.append(log_entry)
        
        # Ausgabe für Analyse
        if msg_type in ['offer', 'answer']:
            logger.warning(f"🔓 SDP {msg_type.upper()} übertragen (enthält Fingerprints!)")
            if 'sdp' in data:
                # Zeige Fingerprint falls vorhanden
                sdp = data.get('sdp', '')
                if 'fingerprint' in sdp:
                    logger.warning(f"   Fingerprint detected in SDP")
        elif msg_type == 'ice-candidate':
            candidate = data.get('candidate', '')
            if candidate:
                logger.info(f"🌐 ICE Candidate: {candidate[:80]}...")
                # Zeige IP-Adressen
                if 'typ host' in candidate:
                    logger.warning(f"   ⚠️  LOCAL IP exposed!")
                elif 'typ srflx' in candidate:
                    logger.warning(f"   ⚠️  PUBLIC IP exposed!")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handler für WebSocket-Verbindungen"""
        room_id = "default"
        room = self.get_room(room_id)
        room.add_client(websocket)
        
        try:
            # Willkommensnachricht
            await websocket.send(json.dumps({
                'type': 'welcome',
                'encrypted': self.encrypted,
                'clients_in_room': len(room.clients)
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    logger.info(f"Received: {msg_type}")
                    
                    # Log für Sicherheitsanalyse
                    self.log_message(msg_type, room_id, data)
                    
                    # Weiterleitung an andere Clients
                    await room.broadcast(message, websocket)
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        finally:
            room.remove_client(websocket)
    
    async def start(self, host: str = "localhost", port: int = 8080):
        """Starte den Signalisierungsserver"""
        mode = "VERSCHLÜSSELT (WSS)" if self.encrypted else "⚠️  UNVERSCHLÜSSELT (WS)"
        logger.info(f"=" * 60)
        logger.info(f"WebRTC Signalisierungsserver - {mode}")
        logger.info(f"=" * 60)
        logger.info(f"Listening on: ws://{host}:{port}")
        logger.info(f"Encryption: {'TLS' if self.encrypted else 'NONE (Sicherheitsrisiko!)'}")
        logger.info(f"=" * 60)
        
        async with websockets.serve(self.handle_client, host, port):
            await asyncio.Future()  # Run forever


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='WebRTC Signaling Server')
    parser.add_argument('--encrypted', action='store_true', 
                       help='Enable TLS encryption (requires cert/key)')
    parser.add_argument('--host', default='localhost', 
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, 
                       help='Port to listen on (default: 8080)')
    
    args = parser.parse_args()
    
    if args.encrypted:
        logger.warning("TLS mode requested but not implemented in this demo")
        logger.warning("For production, use wss:// with proper certificates")
    
    server = SignalingServer(encrypted=args.encrypted)
    
    try:
        await server.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Server stopped")
        logger.info(f"Total messages logged: {len(server.message_log)}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
