@echo off
set /p SERVER=Enter your hosted HTTPS URL (example https://your-site.onrender.com):
set /p TOKEN=Enter your AGENT_TOKEN:
set PRINT_SERVER_URL=%SERVER%
set AGENT_TOKEN=%TOKEN%
py agent.py
pause
