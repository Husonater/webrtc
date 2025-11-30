#!/usr/bin/env python3
"""
WebRTC Signalisierungsserver - Alternative Implementierung
Verwendet aiohttp für WebSocket ohne externe websockets-Bibliothek
"""

from aiohttp import web
import json
import logging
from datetime import datetime
from typing import Set

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SignalingServer:
    def __init__(self):
        self.clients: Set[web.WebSocketResponse] = set()
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
    
    async def websocket_handler(self, request):
        """WebSocket-Verbindungs-Handler"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.clients.add(ws)
        logger.info(f"Client verbunden. Total clients: {len(self.clients)}")
        
        # Willkommensnachricht
        await ws.send_json({
            'type': 'welcome',
            'encrypted': False,
            'clients_in_room': len(self.clients)
        })
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        msg_type = data.get('type')
                        
                        logger.info(f"Received: {msg_type}")
                        self.log_message(msg_type, data)
                        
                        # Broadcast an alle anderen Clients
                        for client in self.clients:
                            if client != ws and not client.closed:
                                try:
                                    await client.send_str(msg.data)
                                except:
                                    pass
                                    
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON received")
                        
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    
        except Exception as e:
            logger.error(f"Error in websocket handler: {e}")
        finally:
            self.clients.discard(ws)
            logger.info(f"Client getrennt. Remaining clients: {len(self.clients)}")
            
        return ws


async def create_app():
    """Erstelle aiohttp Application"""
    server = SignalingServer()
    app = web.Application()
    app.router.add_get('/ws', server.websocket_handler)
    app.router.add_get('/', lambda r: web.Response(text="WebRTC Signaling Server"))
    return app


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='WebRTC Signaling Server (aiohttp)')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("WebRTC Signalisierungsserver - aiohttp WebSocket")
    logger.info("=" * 60)
    logger.info(f"Listening on: ws://{args.host}:{args.port}/ws")
    logger.info(f"HTTP Status: http://{args.host}:{args.port}/")
    logger.info("=" * 60)
    
    app = create_app()
    web.run_app(app, host=args.host, port=args.port, print=lambda x: None)


if __name__ == "__main__":
    main()
