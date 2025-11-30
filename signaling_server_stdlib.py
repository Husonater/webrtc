#!/usr/bin/env python3
"""
WebRTC Signalisierungsserver (Standard Library Version)
Implementiert ein minimales WebSocket-Protokoll ohne externe Abhängigkeiten.
"""

import socket
import threading
import struct
import hashlib
import base64
import json
import logging
from datetime import datetime

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketHandler(threading.Thread):
    def __init__(self, conn, addr, server):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.server = server
        self.handshake_done = False
        self.running = True

    def run(self):
        try:
            if self.do_handshake():
                self.server.add_client(self)
                while self.running:
                    data = self.recv_frame()
                    if data:
                        self.handle_message(data)
                    else:
                        break
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            self.server.remove_client(self)
            self.conn.close()

    def do_handshake(self):
        data = self.conn.recv(4096).decode('utf-8', errors='ignore')
        headers = {}
        lines = data.split('\r\n')
        for line in lines[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value

        if 'Sec-WebSocket-Key' not in headers:
            return False

        key = headers['Sec-WebSocket-Key']
        magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        accept_key = base64.b64encode(hashlib.sha1((key + magic_string).encode()).digest()).decode()

        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
        )
        self.conn.send(response.encode())
        self.handshake_done = True
        return True

    def recv_frame(self):
        # Read header
        data = self.conn.recv(2)
        if not data: return None
        
        byte1, byte2 = struct.unpack('!BB', data)
        
        opcode = byte1 & 0x0F
        if opcode == 8: # Close
            return None
            
        masked = (byte2 & 0x80) >> 7
        payload_len = byte2 & 0x7F
        
        if payload_len == 126:
            data = self.conn.recv(2)
            payload_len = struct.unpack('!H', data)[0]
        elif payload_len == 127:
            data = self.conn.recv(8)
            payload_len = struct.unpack('!Q', data)[0]
            
        masks = None
        if masked:
            masks = self.conn.recv(4)
            
        payload = b""
        while len(payload) < payload_len:
            chunk = self.conn.recv(payload_len - len(payload))
            if not chunk: return None
            payload += chunk
            
        if masked:
            decoded = bytearray()
            for i in range(len(payload)):
                decoded.append(payload[i] ^ masks[i % 4])
            payload = decoded
            
        return payload.decode('utf-8')

    def send_frame(self, message):
        payload = message.encode('utf-8')
        payload_len = len(payload)
        
        frame = bytearray()
        frame.append(0x81) # Text frame, FIN
        
        if payload_len <= 125:
            frame.append(payload_len)
        elif payload_len <= 65535:
            frame.append(126)
            frame.extend(struct.pack('!H', payload_len))
        else:
            frame.append(127)
            frame.extend(struct.pack('!Q', payload_len))
            
        frame.extend(payload)
        try:
            self.conn.send(frame)
        except:
            self.running = False

    def handle_message(self, message):
        try:
            data = json.loads(message)
            self.server.broadcast(message, self)
            
            # Security Logging
            msg_type = data.get('type')
            if msg_type == 'offer':
                logger.warning("🔓 SDP OFFER received (contains Fingerprints)")
            elif msg_type == 'ice-candidate':
                cand = data.get('candidate', '')
                if 'typ host' in cand:
                    logger.warning(f"⚠️  Local IP exposed: {cand.split()[4]}")
                elif 'typ srflx' in cand:
                    logger.warning(f"⚠️  Public IP exposed: {cand.split()[4]}")
                    
        except json.JSONDecodeError:
            pass

class SignalingServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.clients = []
        self.lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        logger.info(f"Signaling Server listening on ws://{self.host}:{self.port}")
        
        while True:
            conn, addr = self.sock.accept()
            handler = WebSocketHandler(conn, addr, self)
            handler.start()

    def add_client(self, handler):
        with self.lock:
            self.clients.append(handler)
            logger.info(f"Client connected. Total: {len(self.clients)}")

    def remove_client(self, handler):
        with self.lock:
            if handler in self.clients:
                self.clients.remove(handler)
                logger.info(f"Client disconnected. Total: {len(self.clients)}")

    def broadcast(self, message, sender):
        with self.lock:
            for client in self.clients:
                if client != sender:
                    client.send_frame(message)

if __name__ == "__main__":
    server = SignalingServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Server stopped")
