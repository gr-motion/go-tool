import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import base64

CONFIG_PATH = os.path.expanduser("~/.go_config.json")
VERSION = "2.0"

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"api_key": None, "model": "flash", "gen_count": 0}
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        if "gen_count" not in config:
            config["gen_count"] = 0
        return config

def generate_image(img_config, api_key, config):
    model_name = "gemini-3.1-flash-image-preview"
    prompt = img_config.get("prompt")
    res = (img_config.get("resolution") or "1K").upper()
    ar = img_config.get("aspect_ratio") or "1:1"
    seed = img_config.get("seed")

    config["gen_count"] += 1
    gen_num = config["gen_count"]
    save_config(config)

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
        seed = 0

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_cfg
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            parts = res_data["candidates"][0]["content"]["parts"]
            img_part = next((p for p in parts if "inlineData" in p or "image" in p), None)
            
            if img_part:
                img_data = img_part.get("inlineData", {}).get("data") or img_part.get("image", {}).get("imageBytes")
                filename = f"imgGen_{seed}_{gen_num}.png"
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"Image saved as {filename}")
                os.system(f"open {filename}")
            else:
                print("Error: No image data found in response.")
    except urllib.error.HTTPError as e:
        print(f"Image Error (HTTP {e.code}): {e.read().decode()}")
    except Exception as e:
        print(f"Image Error: {str(e)}")

def get_gemini_response(prompt, api_key, model_pref, config):
    intent_model = "gemini-flash-latest"
    
    system_instr = (
        "Decide if user wants a system command OR an image. "
        "Return ONLY JSON: {"
        "\"type\": \"command\"|\"image\", "
        "\"command_content\": \"bash command\", "
        "\"image_config\": {\"prompt\": \"...\", \"resolution\": \"1K|2K|4K\", \"aspect_ratio\": \"1:1|16:9|...\", \"seed\": int}, "
        "\"destructive\": bool, \"risk\": \"...\""
        "}. For image_config, extract resolution, aspect ratio (e.g. 16:9), and seed if mentioned."
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{intent_model}:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": f"{system_instr}\n\nInstruction: {prompt}"}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            res = json.loads(res_data["candidates"][0]["content"]["parts"][0]["text"])
            
            if res.get("type") == "image":
                generate_image(res.get("image_config"), api_key, config)
                return None
                
            return res
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
    res = get_gemini_response(prompt, config["api_key"], config["model"], config)
    
    if res is None:
        return

    command = res.get("command_content")
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
