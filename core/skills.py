"""Comandi rapidi deterministici in italiano e inglese."""
import datetime as _dt
import re
from typing import Callable, Optional
from core.bus import BUS

_SKILLS: list[tuple[re.Pattern, Callable]] = []

def skill(pattern: str):
    def deco(fn):
        _SKILLS.append((re.compile(pattern, re.I), fn))
        return fn
    return deco

@skill(r"\b(che ore sono|dimmi l'ora|ora attuale|what'?s the time|what time is it)\b")
def _time(m, ctx):
    return "Sono le " + _dt.datetime.now().strftime("%H:%M") + "."

@skill(r"\b(che giorno è|che data è oggi|data di oggi|what'?s today'?s date|what day is it)\b")
def _date(m, ctx):
    now = _dt.datetime.now()
    weekdays = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    months = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return f"Oggi è {weekdays[now.weekday()]} {now.day} {months[now.month - 1]} {now.year}."

@skill(r"\b(fermati|silenzio|smetti di parlare|annulla tutto|stop|quiet|shut up|cancel that)\b")
def _stop(m, ctx):
    tts = ctx.get("tts") if isinstance(ctx, dict) else getattr(ctx, "tts", None)
    if tts and hasattr(tts, "stop"):
        tts.stop()
    return ""

@skill(r"\b(imposta|avvia|metti|set|start) (?:un )?timer (?:di |for )?(\d+) (secondi?|second|seconds?|minuti?|minutes?|ore?|hours?)\b")
def _timer(m, ctx):
    n, unit = int(m.group(2)), m.group(3).lower()
    if unit.startswith("second"):
        secs, label = n, "secondi"
    elif unit.startswith(("minut", "minute")):
        secs, label = n * 60, "minuti"
    else:
        secs, label = n * 3600, "ore"
    pro = ctx.get("proactive") if isinstance(ctx, dict) else getattr(ctx, "proactive", None)
    if pro:
        pro.schedule_in(secs, f"Il timer di {n} {label} è terminato.")
    return f"Timer impostato per {n} {label}."

@skill(r"\b(alza il volume|aumenta il volume|abbassa il volume|riduci il volume|silenzia|metti muto|louder|quieter|mute)\b")
def _volume(m, ctx):
    from tools.registry import call
    word = m.group(1).lower()
    key = {"alza il volume":"volumeup","aumenta il volume":"volumeup",
           "abbassa il volume":"volumedown","riduci il volume":"volumedown",
           "silenzia":"volumemute","metti muto":"volumemute",
           "louder":"volumeup","quieter":"volumedown","mute":"volumemute"}.get(word)
    if not key:
        return None
    call("desktop.hotkey", {"keys": key}, ctx)
    return ""

def try_fast_path(text: str, ctx) -> Optional[str]:
    for pat, fn in _SKILLS:
        m = pat.search(text)
        if m:
            out = fn(m, ctx)
            if out is not None:
                BUS.emit("skill", f"comando rapido · {fn.__name__}")
                return out
    return None
