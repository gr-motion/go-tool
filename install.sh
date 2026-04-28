#!/bin/zsh

# Define a dedicated directory for go-tool's core files in the main user directory
GO_TOOL_INSTALL_DIR="$HOME/.go-tool-files"
GO_WRAPPER_PATH="$HOME/bin/go"
# Determine the directory where install.sh is located
SCRIPT_SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)" 

# --- Create necessary directories ---
mkdir -p "$GO_TOOL_INSTALL_DIR"
mkdir -p "$HOME/bin"

# --- Copy the main Python script to the dedicated directory ---
cp "$SCRIPT_SOURCE_DIR/go_script.py" "$GO_TOOL_INSTALL_DIR/go_script.py"
echo "Copied go_script.py to $GO_TOOL_INSTALL_DIR/"

# --- Create the wrapper script ---
# This wrapper executes the Python script from its dedicated installation directory
printf '#!/bin/zsh
python3 "%s/go_script.py" "$@"
' "$GO_TOOL_INSTALL_DIR" > "$GO_WRAPPER_PATH"
chmod +x "$GO_WRAPPER_PATH"
echo "Created wrapper script at $GO_WRAPPER_PATH"

# --- Update shell profile to ensure ~/bin is in PATH ---
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
    # Check if the specific PATH export line already exists to avoid duplicates
    if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$SHELL_PROFILE"; then
        echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_PROFILE"
        echo "Added ~/bin to PATH in $SHELL_PROFILE."
        echo "Please restart your terminal or run 'source "$SHELL_PROFILE"' for changes to take effect."
    else
        echo "~/bin is already in your PATH in $SHELL_PROFILE."
    fi
else
    echo "Could not determine your shell profile. Please ensure ~/bin is in your PATH manually."
fi

echo "
go-tool installation complete!"
echo "You can now use the 'go' command from any directory."
echo "To uninstall, run: go /uninstall"