# 🚀 Go Tool

Convert your plain text to system commands using Gemini.

## 📋 Prerequisites

Before installing, make sure you have the following installed. On macOS, the easiest way is using [Homebrew](https://brew.sh/):

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install requirements
brew install git python ffmpeg
```

## 📦 Installation

The `go-tool` script is installed using the provided `install.sh` script. This script will:
1.  Place the core script files (`go_script.py`) into a dedicated directory: `~/.go-tool-files/`.
2.  Create a `go` executable wrapper in `~/bin/`.
3.  Add `~/bin` to your system's PATH environment variable if it's not already there.

To install, clone the repository and run the install script:
```bash
git clone https://github.com/gr-motion/go-tool.git
cd go-tool
chmod +x install.sh
./install.sh
```
After running `./install.sh`, please **restart your terminal** or run `source ~/.zshrc` (or your respective shell profile) for the PATH changes to take effect.

## ⚙️ Setup

1.  **Set your API Key** (you can find it on the Google AI Studio website):
    ```bash
    go /api [YOUR_GEMINI_API_KEY]
    ```
2.  **(Optional) Set your Model:**
    ```bash
    go /model [flash/pro]
    ```

## 🛠 Usage

Simply type `go` followed by your request:
- `go create a folder called test`
- `go convert all videos in this folder to mp4`
- `go create an image of a banana in 2k, 16:9 aspect ratio`

If a command is destructive (e.g., `rm`), it will show you the command with a description of the risk and ask for your confirmation before execution.

## 🪒 Uninstall

To uninstall `go-tool` and remove all its associated files:
1.  Ensure you are in the `go-tool` directory where you cloned the repository.
2.  Run the uninstall command:
    ```bash
    go /uninstall
    ```
This command will:
*   Remove the `go` executable from `~/bin/`.
*   Remove the installation directory `~/.go-tool-files/` and all its contents.
*   Remove the configuration file `~/.go-config.json`.
*   Attempt to remove the `~/bin` directory from your PATH in your shell profile (`.zshrc` or `.bashrc`).

**Please restart your terminal** after uninstallation for the PATH changes to fully apply.

# go-tool
