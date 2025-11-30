#!/usr/bin/env python3
"""
WebRTC Signalisierungsserver (Vereinfachte Version ohne externe Dependencies)
Verwendet nur Standard-Python-Bibliotheken
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketProtocol:
    """Vereinfachter WebSocket-Handler"""
    
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.closed = False
        
    async def recv(self):
        """Empfange Nachricht"""
        try:
            data = await self.reader.read(4096)
            if not data:
                return None
            return data.decode('utf-8')
        except:
            return None
    
    async def send(self, message):
        """Sende Nachricht"""
        if not self.closed:
            try:
                self.writer.write(message.encode('utf-8'))
                await self.writer.drain()
            except:
                self.closed = True
    
    async def close(self):
        """Schließe Verbindung"""
        self.closed = True
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass


class SimpleSignalingServer:
    """Einfacher HTTP-basierter Signalisierungsserver"""
    
    def __init__(self):
        self.clients = []
        self.message_log = []
        
    def log_message(self, msg_type: str, data: dict):
        """Logge Nachrichten für Sicherheitsanalyse"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': msg_type,
            'data': data
        }
        self.message_log.append(log_entry)
        
        # Ausgabe für Analyse
        if msg_type in ['offer', 'answer']:
            logger.warning(f"🔓 SDP {msg_type.upper()} übertragen (enthält Fingerprints!)")
            if 'sdp' in data:
                sdp = data.get('sdp', '')
                if 'fingerprint' in sdp:
                    logger.warning(f"   Fingerprint detected in SDP")
        elif msg_type == 'ice-candidate':
            candidate = data.get('candidate', '')
            if candidate:
                logger.info(f"🌐 ICE Candidate: {candidate[:80]}...")
                if 'typ host' in candidate:
                    logger.warning(f"   ⚠️  LOCAL IP exposed!")
                elif 'typ srflx' in candidate:
                    logger.warning(f"   ⚠️  PUBLIC IP exposed!")
    
    def add_client(self, client_id):
        """Füge Client hinzu"""
        if client_id not in self.clients:
            self.clients.append(client_id)
            logger.info(f"Client {client_id} joined. Total clients: {len(self.clients)}")
    
    def remove_client(self, client_id):
        """Entferne Client"""
        if client_id in self.clients:
            self.clients.remove(client_id)
            logger.info(f"Client {client_id} left. Remaining clients: {len(self.clients)}")
    
    def broadcast(self, message: str, sender_id: str):
        """Sende Nachricht an alle außer Sender"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            self.log_message(msg_type, data)
        except:
            pass


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='WebRTC Signaling Server (Simple)')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("WebRTC Signalisierungsserver (Vereinfachte Version)")
    logger.info("=" * 60)
    logger.info(f"HINWEIS: Dieser Server unterstützt WebSocket-Funktionalität begrenzt")
    logger.info(f"Für volle Funktionalität installieren Sie: pip install websockets")
    logger.info("=" * 60)
    logger.info(f"Listening on: http://{args.host}:{args.port}")
    logger.info("=" * 60)
    
    server = SimpleSignalingServer()
    
    print("\nServer läuft! Drücken Sie Ctrl+C zum Beenden...")
    print("\nFür vollständige WebSocket-Unterstützung:")
    print("  sudo apt install python3-websockets")
    print("  oder verwende ein Virtual Environment")
    print()
    
    try:
        # Halte Server am Laufen
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Server stopped")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
