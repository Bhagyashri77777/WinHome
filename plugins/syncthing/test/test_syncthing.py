import json
import subprocess
import sys
from pathlib import Path

# This tells our tests exactly where to find your main plugin code! 🗺️
PLUGIN_PATH = Path(__file__).parent.parent / "src" / "plugin.py"

def run_plugin(input_data):
    """Helper function to run the plugin exactly like WinHome will do it!"""
    result = subprocess.run(
        [sys.executable, str(PLUGIN_PATH)],
        input=input_data,
        text=True,
        capture_output=True
    )
    return result.stdout.strip()

def test_empty_input():
    """Security Guard 1: Make sure it handles total silence safely."""
    stdout = run_plugin("")
    response = json.loads(stdout)
    assert "error" in response
    assert response["error"] == "Empty input"

def test_invalid_json():
    """Security Guard 2: Make sure it handles gibberish safely."""
    stdout = run_plugin("this is not json!")
    response = json.loads(stdout)
    assert "error" in response
    assert response["error"] == "Invalid JSON"

def test_unknown_command():
    """Security Guard 3: Make sure it handles weird commands safely."""
    request = {"requestId": "123", "command": "dance"}
    stdout = run_plugin(json.dumps(request))
    response = json.loads(stdout)
    assert "error" in response
    assert "Unknown command: dance" in response["error"]