@echo off
echo Starting Ollama server...
start /B "" ollama serve
echo Ollama started in background
timeout /t 2 /nobreak >nul
exit
