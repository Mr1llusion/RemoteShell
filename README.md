# Remote Shell

![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview
<img src="https://github.com/Mr1llusion/RemoteShell/assets/144902381/a0a1e265-a205-4682-8bb7-a20ad9e8bb98" alt="Shell Terminal" width="800" height="400"/>

Welcome to the Remote Shell Project! This project consists of 3 main components: 
* `Server.py`  - (should be on Linux systems)
* `Linux payload.py`
* `Windows payload.py`
  
These scripts are designed for **educational purposes only** and provide the ability to establish a remote shell connection with a target machine, allowing for
* **command execution**
* **file operations**
* **keylogger feature**
* **screenshot feature**

**As a junior ethical hacker**, I'm sharing this project with the community to learn and collaborate together.

<img src="https://lh5.googleusercontent.com/Rz77dewOcHOhOcj3bNmgPR0tBkCE5jFM4HzjY30wmNcjY8nCIXo516UDOHG066Goc3uSgWthqWgCF2ti5S2bqhkRqkOw1xXJ_ck_H0j55Q4Q4CVrLBv9CMuuoXIGaGg1-C5_hYiG" alt="Project Logo" width="100" height="100"/>

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
## Contributing

I welcome contributions from the community. If you have ideas for improvements, bug fixes, or new features, please open an issue or submit a pull request. I appreciate your help in making this project better.

## License

This project is licensed under the [MIT License](LICENSE), which grants you the freedom to use, modify, and distribute the code as long as you include the original copyright notice. See the [LICENSE](LICENSE) file for more details.

**IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY** in accordance with the MIT License.

## Contact

<a href="https://www.linkedin.com/in/david-saransev-103214245/" rel="nofollow"><img src="https://camo.githubusercontent.com/6e6f6848e97889deea2787cef6b145fbf444956ff08df59cc05a0783c7580c0a/68747470733a2f2f696d672e69636f6e73382e636f6d2f627562626c65732f3130302f3030303030302f6c696e6b6564696e2e706e67" title="LinkedIn" data-canonical-src="https://img.icons8.com/bubbles/100/000000/linkedin.png" style="max-width: 100%;"></a>

If you have any questions, suggestions, or concerns, please don't hesitate to reach out.

Thank you for your interest in the Remote Shell Project!
