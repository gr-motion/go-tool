import os
import sys
import json
import subprocess
import urllib.request
import urllib.error

CONFIG_PATH = os.path.expanduser("~/.go_config.json")

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"api_key": None, "model": "flash"}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

VERSION = "1.3"

def get_gemini_response(prompt, api_key, model_pref):
    model_map = {"flash": "gemini-flash-latest", "pro": "gemini-pro-latest"}
    model_name = model_map.get(model_pref, "gemini-flash-latest")
    
    print(f"[Go v{VERSION} using {model_name}]")
    
    system_instr = (
        "Convert instruction to a single bash command. If multiple, use '&&'. "
        "Flag if destructive (deletes/overwrites/modifies files). "
        "Return ONLY JSON: {\"command\": \"...\", \"destructive\": bool, \"risk\": \"...\"}"
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": f"{system_instr}\n\nInstruction: {prompt}"}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return json.loads(res_data["candidates"][0]["content"]["parts"][0]["text"]), model_name
    except urllib.error.HTTPError as e:
        if model_pref == "pro":
            print("Pro model limit reached or unavailable. Falling back to Flash.")
            return get_gemini_response(prompt, api_key, "flash")
        print(f"Error: {e.read().decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: go [instruction] or go /api [key] or go /model [flash/pro]")
        return

    config = load_config()
    cmd_type = sys.argv[1]

    if cmd_type == "/api":
        if len(sys.argv) < 3:
            print("Provide API key.")
            return
        config["api_key"] = sys.argv[2]
        save_config(config)
        print("API key saved.")
        return

    if cmd_type == "/model":
        if len(sys.argv) < 3 or sys.argv[2] not in ["flash", "pro"]:
            print("Usage: go /model [flash/pro]")
            return
        config["model"] = sys.argv[2]
        save_config(config)
        print(f"Model set to {sys.argv[2]}.")
        return

    if not config["api_key"]:
        print("Set API key first: go /api [key]")
        return

    prompt = " ".join(sys.argv[1:])
    res, used_model = get_gemini_response(prompt, config["api_key"], config["model"])
    
    command = res.get("command")
    destructive = res.get("destructive", False)
    risk = res.get("risk", "")

    if destructive:
        print(f"Risk: {risk}")
        print(f"Command: {command}")
        choice = input("Run this command? [y/n]: ").lower()
        if choice != 'y':
            print("Cancelled.")
            return
    else:
        print(f"Command: {command}")

    os.system(command)

if __name__ == "__main__":
    main()
