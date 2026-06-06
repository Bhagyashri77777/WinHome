import sys
import json
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

def check_installed():
    """Check if syncthing.exe is installed and in the system PATH."""
    return shutil.which("syncthing.exe") is not None

def get_config_path():
    """Find where Syncthing hides its secret config file."""
    if os.name == 'nt': # If we are on Windows!
        base = os.environ.get('LOCALAPPDATA', '~\\AppData\\Local')
        return Path(base) / "Syncthing" / "config.xml"
    else: # If we are on Linux/Mac (just in case!)
        return Path("~/.config/syncthing/config.xml").expanduser()

def update_element(parent, tag, new_data):
    """Helper ninja to safely update an XML element without breaking it."""
    changed = False
    elem = parent.find(tag)
    if elem is None:
        elem = ET.SubElement(parent, tag)
        changed = True
        
    for key, value in new_data.items():
        # XML likes text, so we convert booleans (True/False) to lowercase text
        str_value = str(value).lower() if isinstance(value, bool) else str(value)
        
        child = elem.find(key)
        if child is not None:
            if child.text != str_value:
                child.text = str_value
                changed = True
        else:
            new_child = ET.SubElement(elem, key)
            new_child.text = str_value
            changed = True
            
    return changed

def process_command(request):
    """Handle the incoming JSON request."""
    request_id = request.get("requestId") or "unknown"
    command = request.get("command")
    args = request.get("args", {})
    
    if command == "check_installed":
        return {"requestId": request_id, "installed": check_installed()}
        
    elif command == "apply":
        dry_run = args.get("dryRun", False)
        config_path = get_config_path()
        
        # 1. Read existing XML, or create a brand new one if it's missing!
        if config_path.exists():
            tree = ET.parse(config_path)
            root = tree.getroot()
        else:
            root = ET.Element("configuration", version="37")
            tree = ET.ElementTree(root)
            
        changed = False
        
        # 2. Merge the magical settings!
        if "gui" in args and update_element(root, "gui", args["gui"]):
            changed = True
        if "options" in args and update_element(root, "options", args["options"]):
            changed = True
                
        # 3. Safe Atomic Write! 🛡️ (Only if things changed and it's not a dry run)
        if changed and not dry_run:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to a safe temporary file first
            fd, temp_path = tempfile.mkstemp(dir=config_path.parent, suffix=".xml")
            with os.fdopen(fd, 'wb') as f:
                tree.write(f, encoding="utf-8", xml_declaration=True)
            
            # Swap them instantly!
            os.replace(temp_path, config_path)

        return {"requestId": request_id, "changed": changed}
        
    else:
        return {"requestId": request_id, "error": f"Unknown command: {command}"}

def main():
    """Read JSON from the standard input like a good listener."""
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            print(json.dumps({"error": "Empty input"}))
            return
            
        request = json.loads(input_data)
        response = process_command(request)
        print(json.dumps(response))
        
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON"}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()