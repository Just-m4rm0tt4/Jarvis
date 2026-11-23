"""Local document retrieval using SQLite keyword search; no vector DB or model download."""
import hashlib
import os
import re
import sqlite3
import time
from typing import List

from core.bus import BUS

TEXT_EXT = {".txt", ".md", ".py", ".json", ".csv", ".yaml", ".yml", ".log", ".ts", ".tsx"}


def _chunks(text: str, size: int = 900, overlap: int = 120) -> List[str]:
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


def _terms(value: str):
    return list(dict.fromkeys(re.findall(r"[^\\W_]+", (value or "").casefold(), flags=re.UNICODE)))[:12]


class DocRAG:
    def __init__(self, cfg: dict):
        r = cfg.get("rag", {})
        self.roots = r.get("roots", [])
        self.top_k = int(r.get("top_k", 5))
        self.max_mb = float(r.get("max_file_mb", 2))
        db_path = r.get("db_path", "data/rag.sqlite3")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, path TEXT NOT NULL, chunk INTEGER NOT NULL, content TEXT NOT NULL)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path)")
        self.db.commit()
        BUS.emit("rag", "SQLite document index ready (keyword retrieval; no embedding model required)")

    def available(self) -> bool:
        return self.db is not None

    def index(self, roots: List[str] | None = None) -> int:
        n, t0 = 0, time.time()
        for root in (roots if roots is not None else self.roots):
            root = os.path.expandvars(os.path.expanduser(root))
            if not os.path.isdir(root):
                continue
            for dirpath, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv", ".venv"}]
                for filename in files:
                    path = os.path.join(dirpath, filename)
                    if os.path.splitext(filename)[1].lower() not in TEXT_EXT:
                        continue
                    try:
                        if os.path.getsize(path) > self.max_mb * 1024 * 1024:
                            continue
                        with open(path, encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    except OSError:
                        continue

                    self.db.execute("DELETE FROM documents WHERE path=?", (path,))
                    for i, chunk in enumerate(_chunks(content)):
                        chunk_id = hashlib.sha1(f"{path}:{i}".encode("utf-8")).hexdigest()
                        self.db.execute(
                            "INSERT OR REPLACE INTO documents(id, path, chunk, content) VALUES(?,?,?,?)",
                            (chunk_id, path, i, chunk),
                        )
                        n += 1
        self.db.commit()
        BUS.emit("rag", f"indexed {n} chunks in {time.time() - t0:.1f}s")
        return n

    def search(self, query: str, k: int | None = None):
        terms = _terms(query)
        if not terms:
            return []
        where = " OR ".join("lower(content) LIKE ?" for _ in terms)
        rows = self.db.execute(
            f"SELECT path, content FROM documents WHERE {where} LIMIT 500",
            tuple(f"%{term}%" for term in terms),
        ).fetchall()
        ranked = []
        for path, content in rows:
            folded = content.casefold()
            score = sum(folded.count(term) for term in terms)
            if score:
                ranked.append((score, path, content))
        ranked.sort(key=lambda item: item[0], reverse=True)
        hits = [{"text": content, "path": path} for _score, path, content in ranked[:(k or self.top_k)]]
        BUS.emit("rag", f"doc_search('{query[:32]}') → {len(hits)} chunks")
        return hits
