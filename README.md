# 🚀 Go Tool

Convert your plain text to system commands using Gemini.

## 📦 Simple Installation

Run this command in your terminal:

```bash
git clone https://github.com/[YOUR_USERNAME]/go-tool.git && cd go-tool && chmod +x install.sh && ./install.sh
```

## ⚙️ Setup

1. **Set your API Key:**
   ```bash
   go /api [YOUR_GEMINI_API_KEY]
   ```
2. **(Optional) Set your Model:**
   ```bash
   go /model pro  # Options: flash (default), pro
   ```

## 🛠 Usage

Simply type `go` followed by your request:
- `go create a folder called test`
- `go convert all videos in this folder to mp4`
- `go list all files larger than 10MB`

If a command is destructive (e.g., `rm`), it will show you the command and ask for your confirmation.
