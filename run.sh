#!/usr/bin/env bash
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
uvicorn app.main:app --reload --port 8001
