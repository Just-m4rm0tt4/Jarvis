# JARVIS-6 — fork locale italiano

Questa variante usa Ollama per il ragionamento e per la visione. Non richiede chiavi API Gemini o OpenAI.

## Modelli richiesti

- Conversazione: `qwen3:4b`
- Visione: `qwen3-vl:4b`

Ollama deve rispondere su `http://127.0.0.1:11434`.

## Avvio Windows 11

1. Installa Python 3.12, Ollama e un driver NVIDIA aggiornato.
2. Scarica lo ZIP del ramo `ollama-local-italian` ed estrailo in una cartella senza caratteri speciali nel percorso.
3. Avvia Ollama dal menu Start di Windows.
4. Fai doppio clic su `run.bat`.
5. Il launcher crea l'ambiente virtuale, installa i pacchetti compatibili con Windows/Python 3.12, verifica i modelli Qwen, prepara i modelli vocali e Chromium.
6. Alla prima esecuzione registra il profilo vocale quando richiesto.
7. La HUD è disponibile su `http://127.0.0.1:8765`.

Non creare un file `.env` e non inserire chiavi API.

## Dipendenze Windows

La memoria e l'indicizzazione dei documenti usano SQLite incluso in Python. Non serve ChromaDB, hnswlib, sentence-transformers o compilare estensioni C++ per queste funzioni. Il VAD WebRTC usa il pacchetto `webrtcvad-wheels`, con wheel precompilate per Windows.

## Lingua

- Faster-Whisper: lingua italiana (`it`).
- Kokoro-ONNX: voce italiana `if_sara`, lingua `it`; alternativa `im_nicola`.
- Wake word: modello preaddestrato `hey_jarvis`. La frase di attivazione è stata addestrata principalmente in inglese; pronuncia "Hey Jarvis". Le richieste successive sono riconosciute in italiano.

## Memoria e documenti

- Memoria principale: `data/core_memory.json`.
- Cronologia conversazioni: SQLite in `data/recall.sqlite3`.
- Memoria a lungo termine: tabella SQLite nello stesso database.
- Indicizzazione locale dei documenti: `data/rag.sqlite3`.

Il recupero dei ricordi e dei documenti usa corrispondenza lessicale locale in SQLite, non embeddings semantici. L'indicizzazione dei documenti è disattivata all'avvio per evitare scansioni automatiche non richieste; può essere avviata dal codice quando abilitata.

## Privacy e rete

Ragionamento e analisi delle immagini avvengono localmente tramite Ollama. Ricerca web, navigazione, download e installazione dei modelli usano servizi Internet esterni. In questa configurazione JARVIS non invia audio o screenshot a un modello AI cloud.

## Sicurezza

Le operazioni privilegiate richiedono un profilo vocale registrato. Eliminazioni, comandi shell, spegnimento e azioni domotiche richiedono conferma. Non aggirare CAPTCHA, MFA o controlli di accesso. Il monitoraggio dello schermo deve essere visibile e disattivabile.

## Componenti

- `core/llm.py`: client Ollama e chiamate agli strumenti.
- `tools/vision.py`: screenshot e analisi Qwen3-VL.
- `core/stt.py`: riconoscimento vocale locale.
- `core/tts.py`: sintesi vocale Kokoro.
- `core/orchestrator.py`: orchestrazione e autorizzazioni.
- `core/memory.py`: memoria persistente SQLite.
- `core/rag.py`: ricerca locale nei documenti SQLite.
- `web/index.html`: HUD WebGL originale.

Questa è una prima integrazione del backend locale. Wake word, tool calling, audio, visione e automazioni devono essere testati sul computer reale prima di considerare il programma completo.
