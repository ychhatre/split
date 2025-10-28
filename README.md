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

- **Backend**: FastAPI (Python) - Hosted on Render
- **Frontend**: Next.js 14 with TypeScript - Deploy on Vercel
- **Database**: Supabase PostgreSQL (for both local and production)
- **Storage**: AWS S3 for receipt images
- **AI**: OpenAI GPT-4 Vision for receipt parsing

## Local Development

### Backend Setup

1. **Set up Supabase Database**
   - Create a free account at [Supabase](https://supabase.com)
   - Create a new project
   - Go to Settings → Database and copy your connection string
   - Update the connection string to use direct connection (not pooler) for local development

2. **Install and Run Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your Supabase connection string (see below)

# Run database migrations to create tables
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Frontend Setup

```bash
cd frontend
npm install

# Create .env.local file with required variables
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)

Create a `.env` file in the `backend/` directory:

```bash
# Database - Supabase PostgreSQL Connection String
# Get this from Supabase: Settings → Database → Connection String (Direct)
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-us-west-1.pooler.supabase.com:5432/postgres

# OpenAI API Key for receipt parsing
OPENAI_API_KEY=sk-...

# AWS S3 Credentials for receipt storage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-1

# Application Settings
ENVIRONMENT=development  # or 'production'
FRONTEND_URL=http://localhost:3000
```

**Note**: For local development, use the "Direct" connection string from Supabase, not the "Pooler" connection string.

### Frontend (.env.local)

Create a `.env.local` file in the `frontend/` directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Your backend URL
```

## Deployment

### Backend Deployment on Render

1. **Use Your Supabase Database**
   - Use the same Supabase project (or create a separate production project)
   - Get the connection string from Settings → Database → Connection String
   - For production, you can use either Direct or Pooler connection

2. **Deploy to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - Runtime: Python 3
     - Branch: main
     - Root Directory: backend
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - Enable "Auto deploy on push to main"

3. **Set Environment Variables in Render**
   ```
   DATABASE_URL=[Your Supabase connection string]
   OPENAI_API_KEY=[Your OpenAI API key]
   AWS_ACCESS_KEY_ID=[Your AWS access key]
   AWS_SECRET_ACCESS_KEY=[Your AWS secret key]
   AWS_REGION=us-west-1
   ENVIRONMENT=production
   FRONTEND_URL=[Your deployed frontend URL]
   ```

4. **Run Database Migrations** (if needed)
   ```bash
   # SSH into Render or use Render shell
   alembic upgrade head
   ```

### Frontend Deployment on Vercel

1. **Deploy to Vercel**
   ```bash
   cd frontend
   vercel --prod
   ```

2. **Set Environment Variables in Vercel**
   ```
   NEXT_PUBLIC_API_URL=[Your Render backend URL]
   ```

## Monitoring and Debugging

### Viewing Logs on Render

Logs are automatically sent to stdout/stderr and are visible in the Render dashboard:
- Go to your service in Render dashboard
- Click on "Logs" tab
- All application logs will appear here in real-time

The application uses structured logging with clear indicators:
- ✓ Success indicators
- ✗ Error indicators
- 📤 Upload indicators
- 🚀 Startup indicators

### Health Check Endpoint

Monitor your backend health:
```bash
curl https://your-app.onrender.com/health
```

Returns:
```json
{
  "status": "healthy",
  "service": "split-api",
  "environment": "production",
  "database": "connected"
}
```

### Debug Endpoint

Check configuration (be careful in production):
```bash
curl https://your-app.onrender.com/debug
```

## API Documentation

Once deployed, visit:
- **Swagger UI**: `https://your-app.onrender.com/docs`
- **ReDoc**: `https://your-app.onrender.com/redoc`

## Database Migrations with Alembic

### Apply Migrations to Supabase

The easiest way to get your Supabase database up to date:

```bash
cd backend
alembic upgrade head
```

Or use the helper scripts:
```bash
# Mac/Linux
./migrate.sh

# Windows
python migrate.py
```

### Create New Migrations

When you modify database models:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
# Review the generated file in alembic/versions/
alembic upgrade head
```

### View Migration Status

```bash
# Check current version
alembic current

# View migration history
alembic history

# See detailed info
alembic history --verbose
```


## S3 Setup

1. Create two S3 buckets:
   - `split-receipts-dev` (development)
   - `split-receipts-prod` (production)

2. Configure bucket permissions to allow public read access for receipt images

3. Create IAM user with S3 access and note the credentials

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **boto3** - AWS S3 integration
- **OpenAI** - Receipt parsing with GPT-4 Vision
- **qrcode** - QR code generation

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS

## Project Structure

```
split/
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   ├── models.py         # Database models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── database.py       # Database configuration
│   │   ├── config.py         # App configuration
│   │   ├── receipt_parser.py # OpenAI integration
│   │   ├── storage_client.py # S3 integration
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── Dockerfile            # Container configuration
│   ├── render.yaml           # Render deployment config
│   └── requirements.txt      # Python dependencies
└── frontend/
    ├── src/
    │   └── app/              # Next.js pages
    ├── lib/                  # Utilities
    └── package.json          # Node dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License
