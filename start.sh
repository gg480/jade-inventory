#!/bin/bash
cd /home/z/my-project/jade-inventory/backend
source ../venv/bin/activate
exec python -m uvicorn main:app --host 127.0.0.1 --port 8001
