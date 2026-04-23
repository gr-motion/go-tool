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

## 📦 Simple Installation

Run this command in your terminal:

```bash
git clone https://github.com/gr-motion/go-tool.git && cd go-tool && chmod +x install.sh && ./install.sh
```

## ⚙️ Setup

1. **Set your API Key (you can find it on google AI studio website):**
   ```bash
   go /api [YOUR_GEMINI_API_KEY]
   ```
2. **(Optional) Set your Model:**
   ```bash
   go /model [flash/pro]
   ```

## 🛠 Usage

Simply type `go` followed by your request:
- `go create a folder called test`
- `go convert all videos in this folder to mp4`
- `go list all files larger than 10MB`

If a command is destructive (e.g., `rm`), it will show you the command with description and ask for your confirmation.
# go-tool
