# Remote Shell

![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview
<img src="https://github.com/Mr1llusion/RemoteShell/assets/144902381/a0a1e265-a205-4682-8bb7-a20ad9e8bb98" alt="Shell Terminal" width="800" height="400"/>

Welcome to the Remote Shell Project! This project consists of 3 main components: 
* `Server.py`  - (Recommended to run on linux)
* `Linux payload.py`
* `Windows payload.py`
  
These scripts are designed for **educational purposes only** and provide the ability to establish a remote shell connection with a target machine, allowing for
* **command execution**
* **file operations**
* **keylogger feature**
* **screenshot feature**
  
## Usage

To use the Remote Shell Project, you'll need to set up the server and client components with appropriate configurations. Detailed instructions and usage guides can be found in the project's documentation.

## Installtion

**Quick install**
* `git clone https://github.com/Mr1llusion/RemoteShell.git`
* `cd RemoteShell`
* `pip install -r requirements.txt` 

# Important Note

* **win_payload.py**: This Windows payload is designed to duplicate itself with a different name in the temporary directory (MicrosoftAddonsys.exe).
* **lin_payload.py**: This Linux payload is designed to duplicate itself with a different name in the temporary directory (/tmp/.system_lock) and then delete itself.

## Instructions for win_payload

Before using this payload, you need to configure it and convert it into an executable (exe). Follow these steps:

### Prerequisites

Make sure you have [PyInstaller](https://www.pyinstaller.org/) installed. If not, you can install it using pip:

```bash
pip install pyinstaller
```
To build the executable, open the Command Prompt (cmd) in the same directory as the payload and run:
```bash
PyInstaller win_payload.py --onefile --noconsole
```

## License

This project is licensed under the [MIT License](LICENSE), which grants you the freedom to use, modify, and distribute the code as long as you include the original copyright notice. See the [LICENSE](LICENSE) file for more details.

**IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY** in accordance with the MIT License.
