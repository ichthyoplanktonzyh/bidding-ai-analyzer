#!/bin/bash
# One-time project setup script

set -e

echo "=== Bidding AI Analyzer Setup ==="

# Backend setup
echo ""
echo "[1/3] Setting up backend..."
cd "$(dirname "$0")/../backend"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created backend/.env from template — please edit it with your API keys"
fi

python3 -m venv venv
source venv/bin/activate
pip install -e .
echo "  Backend dependencies installed"

# Frontend setup
echo ""
echo "[2/3] Setting up frontend..."
cd ../frontend
npm install
echo "  Frontend dependencies installed"

# Done
echo ""
echo "[3/3] Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your DeepSeek API key"
echo "  2. Run 'scripts/dev.sh' to start development"
echo "  3. Open http://localhost:3000"
