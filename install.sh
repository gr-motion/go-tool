#!/bin/zsh

# Create target directories
mkdir -p "$HOME/bin"

# Download the script (assumes this script is in the repo)
# In the actual GitHub repo, you'd use curl to download go_script.py
# For now, we'll assume the files are in the same folder during install

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Copy the python script
cp "$SCRIPT_DIR/go_script.py" "$HOME/.go_script.py"

# Create the wrapper
printf '#!/bin/zsh\npython3 ~/.go_script.py "$@"\n' > "$HOME/bin/go"
chmod +x "$HOME/bin/go"

# Update shell profile
SHELL_PROFILE=""
if [[ "$SHELL" == */zsh ]]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    if [ -f "$HOME/.bash_profile" ]; then
        SHELL_PROFILE="$HOME/.bash_profile"
    else
        SHELL_PROFILE="$HOME/.bashrc"
    fi
fi

if [ -n "$SHELL_PROFILE" ]; then
    if ! grep -q "$HOME/bin" "$SHELL_PROFILE"; then
        echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_PROFILE"
        echo "Added ~/bin to $SHELL_PROFILE. Please restart terminal."
    else
        echo "~/bin already in $SHELL_PROFILE."
    fi
fi

echo "Installation complete! Use 'go /api [key]' to set up."
