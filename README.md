# Split - Receipt Splitting App

A receipt scanning and bill splitting application that allows groups to split restaurant bills by item.

## Features

- 📸 Receipt scanning with OpenAI Vision API
- 💰 Item-by-item bill splitting with unique item claiming
- 📱 QR code sharing for sessions
- 💳 Venmo deep link integration for payments
- 📊 Real-time payment tracking
- 🚫 Prevents duplicate item selection across users

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 14 with TypeScript
- **Database**: SQLite (development)
- **AI**: OpenAI GPT-4 Vision for receipt parsing

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create `.env` files in both backend and frontend directories with required keys.
