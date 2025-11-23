# Remote Shell C2 Framework

> [!WARNING]
> **Educational Purpose Only**: This tool is intended for authorized security research and education. The authors are not responsible for misuse.

A lightweight, educational Command & Control (C2) framework written in Python. Designed for defensive analysis and understanding C2 architectures.

## Features

*   **Cross-Platform Agents**: Full support for **Windows** and **Linux** targets.
*   **Shell**:
    *   **Autocomplete**: Tab completion for commands and filenames (both local and remote).
    *   **Commands**: `ls`, `cat`, `pwd` works across platforms (Windows `ls` auto-translates to `dir`).
*   **Post-Exploitation Tools**:
    *   **Keylogger**: Capture keystrokes in real-time.
    *   **Screenshot**: Capture high-quality screenshots.
    *   **File Transfer**: Reliable `upload` and `download`.
    *   **System Info**: Quick reconnaissance (`sysinfo`).
*   **Stealth**: Ephemeral agents (no persistence mechanisms) - they vanish when closed.

## Components

1.  **`C2Server.py`**: The central listener and control console.
2.  **`LinuxAgent.py`**: Python agent for Linux systems.
3.  **`WindowsAgent.py`**: Python agent for Windows systems.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Mr1llusion/RemoteShell.git
    cd RemoteShell
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies: `pynput`, `Pillow`, `pyreadline3` (Windows only)*

## Usage

### 1. Start the Server
Run the listener on your attacking machine (e.g., Kali Linux):
```bash
python3 C2Server.py
```
*The server listens on `0.0.0.0:5555` by default.*

### 2. Start an Agent
Run the agent on the target machine:

**Linux:**
```bash
python3 LinuxAgent.py
```

**Windows:**
```powershell
python WindowsAgent.py
```

### 3. Control
Once a connection is established, you will see a shell prompt. Type `help` to see available commands.

```text
Shell> help

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
```

## License
This project is licensed under the MIT License.
