#!/usr/bin/env python3
"""
TCP Listener Script for Port 19301
Listens for incoming TCP connections and prints received data.
Commonly used for robot communication protocols.
"""

import socket
import threading
import time
import sys

class TCPListener:
    def __init__(self, host='0.0.0.0', port=19301):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.client_threads = []
    
    def handle_client(self, client_socket, client_address):
        """Handle incoming client connection"""
        print(f"[{time.strftime('%H:%M:%S')}] New connection from {client_address}")
        
        try:
            while self.running:
                # Receive data from client
                data = client_socket.recv(1024)
                
                if not data:
                    print(f"[{time.strftime('%H:%M:%S')}] Client {client_address} disconnected")
                    break
                
                # Print received data in multiple formats
                timestamp = time.strftime('%H:%M:%S')
                print(f"\n[{timestamp}] Received from {client_address}:")
                print(f"  Raw bytes: {data}")
                print(f"  Length: {len(data)} bytes")
                print(f"  Hex: {data.hex()}")
                
                # Try to decode as UTF-8 text
                try:
                    text = data.decode('utf-8')
                    print(f"  Text: '{text}'")
                except UnicodeDecodeError:
                    print(f"  Text: <not valid UTF-8>")
                
                # Try to decode as ASCII (common for robot protocols)
                try:
                    ascii_text = data.decode('ascii')
                    print(f"  ASCII: '{ascii_text}'")
                except UnicodeDecodeError:
                    print(f"  ASCII: <not valid ASCII>")
                
                print("-" * 60)
                
        except ConnectionResetError:
            print(f"[{time.strftime('%H:%M:%S')}] Connection reset by {client_address}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"[{time.strftime('%H:%M:%S')}] Connection to {client_address} closed")
    
    def start(self):
        """Start the TCP listener"""
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address and port
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            
            print(f"TCP Listener started on {self.host}:{self.port}")
            print(f"Waiting for connections... (Press Ctrl+C to stop)")
            print("=" * 60)
            
            while self.running:
                try:
                    # Accept incoming connection
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Create thread to handle client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    self.client_threads.append(client_thread)
                    
                except OSError:
                    if self.running:
                        print("Socket error occurred")
                    break
                    
        except Exception as e:
            print(f"Error starting server: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the TCP listener"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"\n[{time.strftime('%H:%M:%S')}] TCP Listener stopped")

def main():
    """Main function"""
    # Default settings
    host = '0.0.0.0'  # Listen on all interfaces
    port = 19301
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 19301.")
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    # Create and start listener
    listener = TCPListener(host, port)
    
    try:
        listener.start()
    except KeyboardInterrupt:
        print(f"\n[{time.strftime('%H:%M:%S')}] Received interrupt signal")
        listener.stop()
    except Exception as e:
        print(f"Unexpected error: {e}")
        listener.stop()

if __name__ == "__main__":
    main()
