import socket
import base64
import os

def test_websocket():
    host = 'localhost'
    port = 8080
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        print(f"Connected to {host}:{port}")
        
        # Send Handshake
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET / HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.send(request.encode())
        
        response = sock.recv(4096).decode()
        print("Response received:")
        print(response)
        
        if "101 Switching Protocols" in response:
            print("SUCCESS: WebSocket Handshake completed!")
        else:
            print("FAILURE: Invalid response")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    test_websocket()
