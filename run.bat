@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title JARVIS-6 - Assistente locale Ollama

if not exist ".venv\\Scripts\\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto :error
)
set "PY=.venv\\Scripts\\python.exe"

if not exist ".venv\\jarvis-deps.ok" (
  echo [1/5] Installazione dipendenze compatibili con Windows...
  "%PY%" -m pip install --upgrade pip
  if errorlevel 1 goto :error
  "%PY%" -m pip install -r requirements.txt
  if errorlevel 1 goto :error
  echo ok> ".venv\\jarvis-deps.ok"
) else (
  echo [1/5] Dipendenze gia' installate.
)

echo [2/5] Verifica Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
  echo Ollama non trovato nel PATH. Installa Ollama e riprova.
  goto :error
)
curl.exe -fsS http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo Il server Ollama non risponde. Avvia Ollama dal menu Start.
  goto :error
)

echo [3/5] Verifica modelli locali...
ollama list | findstr /I /C:"qwen3:4b" >nul
if errorlevel 1 (
  ollama pull qwen3:4b
  if errorlevel 1 goto :error
)
ollama list | findstr /I /C:"qwen3-vl:4b" >nul
if errorlevel 1 (
  ollama pull qwen3-vl:4b
  if errorlevel 1 goto :error
)

echo [4/5] Preparazione modelli vocali...
if not exist "models" mkdir "models"
"%PY%" -c "from openwakeword import utils; utils.download_models(['hey_jarvis'])"
if errorlevel 1 goto :error
if not exist "models\\kokoro-v1.0.onnx" (
  curl.exe -fL --retry 3 -o "models\\kokoro-v1.0.onnx" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
  if errorlevel 1 goto :error
)
if not exist "models\\voices-v1.0.bin" (
  curl.exe -fL --retry 3 -o "models\\voices-v1.0.bin" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
  if errorlevel 1 goto :error
)
"%PY%" -m playwright install chromium
if errorlevel 1 goto :error

echo [5/5] Preparazione profilo vocale...
if not exist "data\\voiceprint.json" (
  "%PY%" "scripts\\enroll_voice.py"
  if errorlevel 1 goto :error
)

echo Avvio HUD e assistente...
start "" "http://127.0.0.1:8765"
"%PY%" main.py
if errorlevel 1 goto :error
goto :eof

:error
echo.
echo Avvio interrotto. Controlla il messaggio precedente.
pause
exit /b 1
