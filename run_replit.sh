#!/usr/bin/env bash
set -e

echo "=== CareDose AI — Starting Replit Deployment ==="

# 1. Install Python dependencies
pip install -r backend/requirements.txt

# 2. Build React Frontend if npm is available
if command -v npm >/dev/null 2>&1; then
  echo "Building React Frontend..."
  cd frontend
  npm install
  npm run build
  cd ..
fi

# 3. Start FastAPI Backend (serves API on /api and React build on /)
echo "Starting CareDose AI FastAPI Server on port 8000..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
