@echo off
cd /d F:\nanoCAD\server
py -m src.presentation.server --transport sse --port 8081 --host 0.0.0.0
