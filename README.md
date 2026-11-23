# JARVIS-6 — fork locale italiano

Questa variante usa Ollama per il ragionamento e per la visione. Non richiede chiavi API Gemini o OpenAI.

## Modelli richiesti

- Conversazione: `qwen3:4b`
- Visione: `qwen3-vl:4b`

Ollama deve rispondere su `http://127.0.0.1:11434`.

## Avvio Windows 11

1. Installa Python 3.12, Ollama e un driver NVIDIA aggiornato.
2. Apri la cartella del repository.
3. Esegui `run.bat`.
4. Il launcher crea l'ambiente virtuale, installa i pacchetti, verifica i modelli Qwen, prepara i modelli vocali e Chromium.
5. Alla prima esecuzione registra il profilo vocale quando richiesto.
6. La console HUD è disponibile su `http://127.0.0.1:8765`.

Non creare un file `.env` e non inserire chiavi API.

## Lingua

- Faster-Whisper: lingua italiana (`it`).
- Kokoro-ONNX: voce italiana `if_sara`, lingua `it`; alternativa `im_nicola`.
- Wake word: modello preaddestrato `hey_jarvis`. La frase di attivazione è addestrata in inglese; pronuncia "Hey Jarvis". Le richieste successive sono riconosciute in italiano.

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
- `web/index.html`: HUD WebGL originale.

Questa è una prima integrazione del backend locale. Wake word, tool calling, audio, visione e automazioni devono essere testati sul computer reale prima di considerare il programma completo.
