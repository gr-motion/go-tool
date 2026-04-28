import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import base64
import shutil # Import shutil for rmtree

# --- Configuration ---
CONFIG_PATH = os.path.expanduser("~/.go_config.json")
VERSION = "2.2" # Version incremented for clarity

# Define the dedicated installation directory in the main user directory
# This must match the directory used in install.sh for consistent uninstallation.
GO_TOOL_INSTALL_DIR = os.path.expanduser("~/.go-tool-files")

# --- Helper Functions ---
def save_config(config):
    """Saves the configuration to disk."""
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4) # Use indent for readability
    except IOError as e:
        print(f"Error saving configuration to {CONFIG_PATH}: {e}")

def load_config():
    """Loads the configuration from disk, with defaults."""
    if not os.path.exists(CONFIG_PATH):
        return {"api_key": None, "model": "flash", "gen_count": 0}
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            # Ensure gen_count exists for backward compatibility
            if "gen_count" not in config:
                config["gen_count"] = 0
            return config
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading configuration from {CONFIG_PATH}: {e}")
        print("Using default configuration.")
        return {"api_key": None, "model": "flash", "gen_count": 0}

def generate_image(img_config, api_key, config):
    """Generates an image using the Gemini API."""
    model_name = "gemini-3.1-flash-image-preview"
    prompt = img_config.get("prompt")
    res = (img_config.get("resolution") or "1K").upper()
    ar = img_config.get("aspect_ratio") or "1:1"
    seed = img_config.get("seed")

    config["gen_count"] += 1
    gen_num = config["gen_count"]
    save_config(config) # Save config after incrementing gen_count

    print(f"[Go v{VERSION} generating {res} image ({ar}) using {model_name}]")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    gen_cfg = {
        "responseModalities": ["IMAGE"],
        "imageConfig": {
            "aspectRatio": ar,
            "imageSize": res
        }
    }

    if seed is not None:
        gen_cfg["seed"] = seed
    else:
        # Generate a random seed if not provided, useful for consistency if script is re-run without seed
        import random
        seed = random.randint(0, 2**32 - 1) 
        gen_cfg["seed"] = seed # Use generated seed for consistency

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_cfg
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            if "error" in res_data:
                print(f"API Error: {res_data['error']['message']}")
                return

            parts = res_data["candidates"][0]["content"]["parts"]
            img_part = next((p for p in parts if "inlineData" in p or "image" in p), None)
            
            if img_part:
                img_data = img_part.get("inlineData", {}).get("data") or img_part.get("image", {}).get("imageBytes")
                # Use a more descriptive filename, incorporating prompt snippet if possible, and seed
                safe_prompt_part = "".join(c if c.isalnum() else "_" for c in prompt[:20])
                filename = f"go_img_{safe_prompt_part}_seed{seed}_gen{gen_num}.png"
                
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"Image saved as '{filename}'")
                
                # Open image using default system viewer
                try:
                    subprocess.run(["open", filename], check=True)
                except FileNotFoundError:
                    print(f"Could not automatically open '{filename}'. Please open it manually.")
                except Exception as e:
                    print(f"Error opening '{filename}': {e}")
            else:
                print("Error: No image data found in response.")
    except urllib.error.HTTPError as e:
        print(f"Image Generation Error (HTTP {e.code}): {e.read().decode()}")
    except Exception as e:
        print(f"An unexpected error occurred during image generation: {str(e)}")

def get_gemini_response(prompt, api_key, model_pref, config):
    """Gets a JSON response from Gemini API to classify user intent."""
    intent_model = "gemini-flash-latest"
    
    # Improved system instruction for clearer JSON output and risk assessment
    system_instr = (
        "You are an AI assistant that interprets user requests. "
        "Determine if the user wants to execute a system command OR generate an image. "
        "Return ONLY a JSON object with the following structure:
"
        "{
"
        "  "type": "command" | "image",
"
        "  "command_content": "<bash command to execute>" (if type is 'command'),
"
        "  "image_config": {
"
        "    "prompt": "<user's image prompt>",
"
        "    "resolution": "1K" | "2K" | "4K" | "auto",
"
        "    "aspect_ratio": "1:1" | "16:9" | "...",
"
        "    "seed": <integer> (optional, for reproducible generations)
"
        "  } (if type is 'image'),
"
        "  "destructive": boolean (true if the command could cause data loss or significant system change),
"
        "  "risk": "<brief description of risk, e.g., 'deletes files', 'modifies system settings'>" (if destructive is true)
"
        "}

"
        "If the user asks to uninstall, classify it as a 'command' with type 'uninstall'.
"
        "Extract resolution, aspect ratio, and seed from the user's prompt if mentioned."
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{intent_model}:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": f"{system_instr}

User Request: {prompt}"}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            if "error" in res_data:
                print(f"API Error: {res_data['error']['message']}")
                return None
                
            # Ensure the response part is treated as text and is valid JSON
            response_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            try:
                res = json.loads(response_text)
                return res
            except json.JSONDecodeError:
                print(f"Error: Received non-JSON response from API: {response_text}")
                return None
                
    except urllib.error.HTTPError as e:
        print(f"API Request Error (HTTP {e.code}): {e.read().decode()}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API request: {str(e)}")
        return None

# --- Uninstall Function ---
def remove_path_from_profile(profile_path):
    """Removes the specific PATH export line for ~/bin from a shell profile file."""
    if not os.path.exists(profile_path):
        return False
    
    # The exact line added by the install script for go-tool
    target_line = 'export PATH="$HOME/bin:$PATH"
' 
    
    try:
        with open(profile_path, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        removed_line = False
        for line in lines:
            if line == target_line:
                removed_line = True
                continue # Skip adding this line to new_lines
            new_lines.append(line)
        
        if removed_line:
            with open(profile_path, "w") as f:
                f.writelines(new_lines)
            return True
        return False
    except IOError as e:
        print(f"Error modifying {profile_path}: {e}")
        return False

def uninstall():
    """Uninstalls go-tool by removing files and cleaning up PATH."""
    print("Starting go-tool uninstallation...")

    # 1. Remove the go executable wrapper from ~/bin
    go_executable_path = os.path.expanduser("~/bin/go")
    if os.path.exists(go_executable_path):
        try:
            os.remove(go_executable_path)
            print(f"Successfully removed: {go_executable_path}")
        except OSError as e:
            print(f"Error removing {go_executable_path}: {e}")
    else:
        print(f"Executable {go_executable_path} not found, skipping.")

    # 2. Remove the dedicated installation directory and its contents
    if os.path.exists(GO_TOOL_INSTALL_DIR):
        try:
            shutil.rmtree(GO_TOOL_INSTALL_DIR)
            print(f"Successfully removed installation directory: {GO_TOOL_INSTALL_DIR}")
        except OSError as e:
            print(f"Error removing directory {GO_TOOL_INSTALL_DIR}: {e}")
    else:
        print(f"Installation directory {GO_TOOL_INSTALL_DIR} not found, skipping.")

    # 3. Remove the configuration file
    if os.path.exists(CONFIG_PATH):
        try:
            os.remove(CONFIG_PATH)
            print(f"Successfully removed config file: {CONFIG_PATH}")
        except OSError as e:
            print(f"Error removing {CONFIG_PATH}: {e}")
    else:
        print(f"Config file {CONFIG_PATH} not found, skipping.")

    # 4. Remove PATH entry from the shell profile
    shell = os.environ.get('SHELL')
    profile_path = None
    if shell and "/zsh" in shell:
        profile_path = os.path.expanduser("~/.zshrc")
    elif shell and "/bash" in shell:
        # Prefer .bash_profile if it exists, otherwise .bashrc
        if os.path.exists(os.path.expanduser("~/.bash_profile")):
            profile_path = os.path.expanduser("~/.bash_profile")
        else:
            profile_path = os.path.expanduser("~/.bashrc")

    if profile_path:
        if remove_path_from_profile(profile_path):
            print(f"Removed PATH entry from {profile_path}.")
            print("Please restart your terminal or run 'source "$SHELL_PROFILE"' for PATH changes to fully apply.")
        else:
            print(f"PATH entry related to ~/bin was not found or could not be removed from {profile_path}.")
    else:
        print("Could not determine your shell profile to modify PATH.")

    print("
go-tool uninstallation process finished.")


# --- Main Execution Logic ---
def main():
    """Handles command-line arguments and orchestrates tool actions."""
    if len(sys.argv) < 2:
        # Updated usage message to include /uninstall
        print("Usage: go [instruction] | go /api [key] | go /model [flash/pro] | go /uninstall")
        return

    config = load_config()
    cmd_type = sys.argv[1] # The first argument determines the command type

    # --- Handle special commands ---
    if cmd_type == "/api":
        if len(sys.argv) < 3:
            print("Error: Please provide your Gemini API key.")
            print("Usage: go /api [your_api_key]")
            return
        api_key = sys.argv[2]
        config["api_key"] = api_key
        save_config(config)
        print("Gemini API key successfully saved.")
        return

    if cmd_type == "/model":
        if len(sys.argv) < 3 or sys.argv[2] not in ["flash", "pro"]:
            print("Error: Invalid model specified.")
            print("Usage: go /model [flash | pro]")
            return
        config["model"] = sys.argv[2]
        save_config(config)
        print(f"Model set to '{sys.argv[2]}'.")
        return
        
    if cmd_type == "/uninstall":
        uninstall() # Call the uninstallation function
        return

    # --- General Command/Image Generation ---
    if not config.get("api_key"):
        print("Error: Gemini API key is not set.")
        print("Please set it first using: go /api [your_api_key]")
        return

    # Join all arguments after the command type to form the prompt
    prompt = " ".join(sys.argv[1:])
    
    # Get Gemini's interpretation of the prompt
    response = get_gemini_response(prompt, config["api_key"], config.get("model", "flash"), config)
    
    if response is None:
        # get_gemini_response prints its own errors
        return

    # --- Process Gemini's Response ---
    response_type = response.get("type")

    if response_type == "image":
        image_config = response.get("image_config")
        if image_config:
            generate_image(image_config, config["api_key"], config)
        else:
            print("Error: Image generation requested, but image configuration is missing.")
        return # Exit after handling image generation

    elif response_type == "command":
        command = response.get("command_content")
        if not command:
            print("Error: Command requested, but no command content was provided.")
            return
        
        destructive = response.get("destructive", False)
        risk_description = response.get("risk", "No specific risk mentioned.")

        # --- Execute Command with Confirmation for Destructive Actions ---
        if destructive:
            print(f"Warning: This command is marked as destructive.")
            print(f"Risk: {risk_description}")
            print(f"Command to execute: {command}")
            
            # Prompt user for confirmation
            choice = input("Are you sure you want to run this command? [y/n]: ").lower().strip()
            if choice == 'y':
                print("Executing command...")
                try:
                    os.system(command)
                    print("Command execution finished.")
                except Exception as e:
                    print(f"Error executing command: {e}")
            else:
                print("Command execution cancelled by user.")
        else:
            # Non-destructive command
            print(f"Executing command: {command}")
            try:
                os.system(command)
                print("Command execution finished.")
            except Exception as e:
                print(f"Error executing command: {e}")
        return # Exit after handling command execution

    else:
        print(f"Error: Unknown response type from Gemini: '{response_type}'.")
        print("Response received:", response)
        return

if __name__ == "__main__":
    main()
