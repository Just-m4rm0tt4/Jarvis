"""Acquisizione locale dello schermo e analisi col modello visivo configurato."""
from pathlib import Path
import base64, mimetypes
from tools.registry import tool
from core.bus import BUS


def _capture(path):
    import pyautogui
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pyautogui.screenshot(path)
    return path


@tool("vision.analyze_screen", "Acquisisce lo schermo e descrive elementi, errori, testo e disposizione delle finestre.",
      {"question": {"type": "string", "required": False}}, privileged=True)
def analyze_screen(question="Describe the current screen and identify actionable UI elements, visible errors, and the next useful step.", ctx=None):
    if not (ctx or {}).get("config", {}).get("tools", {}).get("vision", {}).get("enabled", True):
        return "screen vision disabled in config.yaml"
    path = (ctx or {}).get("config", {}).get("tools", {}).get("vision", {}).get("screenshot_path", "data/screen.png")
    path = _capture(path)
    llm = (ctx or {}).get("llm")
    if llm is None:
        return f"screen captured at {path}; vision brain unavailable"
    model = (ctx or {}).get("config", {}).get("tools", {}).get("vision", {}).get("model")
    result = llm.analyze_image(path, question, model=model)
    BUS.emit("vision", result[:500])
    return result[:8000]
