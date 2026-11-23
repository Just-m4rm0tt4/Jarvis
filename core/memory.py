"""Persistent local memory using JSON and SQLite only (no vector database required)."""
import json
import os
import re
import sqlite3
import time

from core.bus import BUS

DEFAULT_CORE = {
    "persona": "Sono JARVIS, un assistente personale locale. Rispondo in italiano, con precisione e senza inventare informazioni.",
    "user": "L'operatore si chiama Edoardo. Le preferenze vengono memorizzate quando sono utili e durevoli.",
}


def _terms(value: str):
    return list(dict.fromkeys(re.findall(r"[^\\W_]+", (value or "").casefold(), flags=re.UNICODE)))[:12]


def _ranked_rows(db, table: str, query: str, limit: int):
    terms = _terms(query)
    if not terms:
        return []
    where = " OR ".join("lower(text) LIKE ?" for _ in terms)
    params = [f"%{term}%" for term in terms]
    rows = db.execute(
        f"SELECT text, ts FROM {table} WHERE {where} ORDER BY ts DESC LIMIT ?",
        (*params, max(limit * 20, 100)),
    ).fetchall()
    scored = []
    for text, ts in rows:
        folded = text.casefold()
        score = sum(folded.count(term) for term in terms)
        if score:
            scored.append((score, ts, text))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [text for _score, _ts, text in scored[:limit]]


class Memory:
    def __init__(self, cfg: dict):
        m = cfg["memory"]
        self.core_path = m["core_blocks_path"]
        self.top_k = int(m.get("archival_top_k", 4))
        os.makedirs(os.path.dirname(self.core_path) or ".", exist_ok=True)

        if os.path.exists(self.core_path):
            with open(self.core_path, encoding="utf-8") as f:
                self.core = json.load(f)
        else:
            self.core = dict(DEFAULT_CORE)

        db_path = m["recall_path"]
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS recall(ts REAL, role TEXT, text TEXT)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS archival(ts REAL, text TEXT)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_recall_ts ON recall(ts)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_archival_ts ON archival(ts)")
        self.db.commit()
        self._save()

    # --- core memory ---
    def core_memory_replace(self, block: str, value: str):
        self.core[block] = value
        self._save()
        BUS.emit("mem", f"core_memory_replace({block})")
        return "ok"

    def core_memory_append(self, block: str, value: str):
        self.core[block] = (self.core.get(block, "") + " " + value).strip()
        self._save()
        BUS.emit("mem", f"core_memory_append({block})")
        return "ok"

    def _save(self):
        with open(self.core_path, "w", encoding="utf-8") as f:
            json.dump(self.core, f, ensure_ascii=False, indent=2)

    def block_text(self) -> str:
        return "\\n".join(f"<{k}>{v}</{k}>" for k, v in self.core.items())

    # --- chronological recall ---
    def log(self, role: str, text: str):
        self.db.execute(
            "INSERT INTO recall(ts, role, text) VALUES(?,?,?)",
            (time.time(), role, text),
        )
        self.db.commit()

    def recall_memory_search(self, query: str, limit: int = 5):
        terms = _terms(query)
        if not terms:
            return []
        where = " OR ".join("lower(text) LIKE ?" for _ in terms)
        rows = self.db.execute(
            f"SELECT role, text FROM recall WHERE {where} ORDER BY ts DESC LIMIT ?",
            (*[f"%{term}%" for term in terms], max(limit * 20, 100)),
        ).fetchall()
        scored = sorted(
            rows,
            key=lambda row: sum(row[1].casefold().count(t) for t in terms),
            reverse=True,
        )[:limit]
        BUS.emit("mem", f"recall_memory_search('{query[:48]}') → {len(scored)} hits")
        return [{"role": role, "text": text} for role, text in scored]

    # --- long-term archival memory ---
    def archival_insert(self, text: str):
        if not text or not text.strip():
            return "ignored: empty memory"
        self.db.execute(
            "INSERT INTO archival(ts, text) VALUES(?,?)",
            (time.time(), text[:12000]),
        )
        self.db.commit()
        BUS.emit("mem", "archival_insert(1 chunk)")
        return "ok"

    def archival_search(self, query: str):
        docs = _ranked_rows(self.db, "archival", query, self.top_k)
        BUS.emit("mem", f"archival_search('{query[:48]}') → {len(docs)} chunks")
        return docs
