#!/bin/bash
# Meeting Minute Chatbot - Quick Start
# Run this script, then copy the commands to 3 separate terminals

cd /teamspace/studios/this_studio/meeting_minutes

echo "================================================"
echo "  Meeting Minute Chatbot - Startup"
echo "================================================"
echo ""

# Start PostgreSQL
echo "[1/3] Starting PostgreSQL..."
sudo service postgresql start
sudo -u postgres createdb meeting_chatbot
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"

# Activate virtual environment
echo "[2/3] Activating virtual environment..."
cd /teamspace/studios/this_studio/meeting_minutes && source .venv/bin/activate && python scripts/seed_db.py
source .venv/bin/activate

echo "[3/3] Verifying setup..."
python -c "from backend.app.config import settings; print('Config loaded OK')"

echo ""
echo "================================================"
echo "  Setup Ready! Now open 3 terminals:"
echo "================================================"
echo ""
echo "TERMINAL 1 - Backend (copy this):"
echo "  cd /teamspace/studios/this_studio/meeting_minutes && source .venv/bin/activate && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "TERMINAL 2 - Streamlit (copy this):"
echo "  cd /teamspace/studios/this_studio/meeting_minutes && source .venv/bin/activate && streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501"
echo ""
echo "TERMINAL 3 - Tunnel (copy this):"
echo "  cd /teamspace/studios/this_studio/meeting_minutes && ./bore local 8501 --to bore.pub"
echo ""
echo "================================================"

# run this in the terminal: 
# bash /teamspace/studios/this_studio/meeting_minutes/start_all.sh
# sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"