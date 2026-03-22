# 🕵️ DetectiveOS

> *The world's first AI-powered mystery-solving platform. Interrogate suspects. Pin evidence. Solve the case.*

---

## What You Have

A fully working SaaS platform built with:

- **Frontend** — Vanilla HTML + CSS + JavaScript (open in a browser, no build step needed)
- **Backend** — Python + FastAPI (one command to run)
- **Database** — PostgreSQL (free, runs on your computer)
- **AI** — Anthropic Claude API (powers suspect interrogation and theory scoring)

---

## Project Structure

```
detectiveos/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py               ← register, login, /me endpoints
│   │   │   ├── cases.py              ← list cases, get case, start, save board
│   │   │   ├── interrogation.py      ← AI suspect chat endpoint
│   │   │   ├── solutions.py          ← submit theory + get score
│   │   │   └── leaderboard.py        ← global + weekly rankings
│   │   ├── db/
│   │   │   ├── database.py           ← SQLAlchemy engine + session
│   │   │   └── seed.py               ← loads all 6 cases into the database
│   │   ├── models/
│   │   │   └── __init__.py           ← User, Case, Suspect, Evidence, Progress, Solution
│   │   ├── schemas/
│   │   │   └── __init__.py           ← Pydantic request/response shapes
│   │   ├── services/
│   │   │   ├── ai_interrogation.py   ← Claude API suspect dialogue engine
│   │   │   └── scoring_engine.py     ← 100-point scoring system
│   │   ├── utils/
│   │   │   └── auth.py               ← JWT creation + bcrypt password hashing
│   │   ├── config.py                 ← reads your .env file
│   │   └── main.py                   ← FastAPI app, all routers registered
│   ├── alembic/                      ← database migration files
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   └── test_main.py              ← auth + cases + health tests
│   ├── alembic.ini                   ← alembic config
│   ├── requirements.txt              ← all Python packages
│   └── .env.example                  ← template for your .env file
│
├── frontend/
│   ├── index.html                    ← landing page (hero, features, pricing)
│   ├── login.html                    ← login + register with avatar picker
│   ├── cases.html                    ← browse all 6 cases with filters
│   ├── case.html                     ← the full game: case file / board / interrogation / solve
│   ├── leaderboard.html              ← global + weekly rankings
│   ├── profile.html                  ← your profile, XP, achievements
│   ├── css/
│   │   └── global.css                ← full noir design system (tokens, animations, grain)
│   └── js/
│       ├── api.js                    ← all API calls + auth state management
│       └── board.js                  ← drag-drop evidence board with SVG wire connections
│
├── case-templates/                   ← 6 complete mystery cases in JSON
│   ├── midnight-manor.json           ← MASTERMIND · poisoned Scotch + CCTV loop
│   ├── harbor-street-blackout.json   ← DETECTIVE · corporate blackout abduction
│   ├── redwood-inheritance.json      ← ROOKIE · inheritance drowning
│   ├── double-exposure.json          ← DETECTIVE · gallery ricin poisoning
│   ├── zodiac-protocol.json          ← MASTERMIND · DARPA lab murder
│   └── glass-garden.json             ← DETECTIVE · botanical alkaloid poisoning
│
└── README.md                         ← this file
```

---

## Setup — Step by Step

### Step 1 · Install PostgreSQL

**Mac:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download the installer from https://www.postgresql.org/download/windows/ and run it. During setup, remember the password you set for the `postgres` user — you'll need it below.

---

### Step 2 · Create the Database

Open your terminal and run:

```bash
psql -U postgres
```

Then paste these lines inside the PostgreSQL prompt:

```sql
CREATE DATABASE detectiveos;
CREATE USER detective WITH PASSWORD 'secret';
GRANT ALL PRIVILEGES ON DATABASE detectiveos TO detective;
\q
```

> **Windows tip:** Search for "psql" in your Start menu, or open pgAdmin and run the SQL above in the Query Tool.

---

### Step 3 · Set Up Python

```bash
# Move into the backend folder
cd detectiveos/backend

# Create a virtual environment
python -m venv venv

# Activate it
# Mac / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Install all packages
pip install -r requirements.txt
```

You should see packages installing. This takes about a minute.

---

### Step 4 · Create Your .env File

```bash
# Copy the template
cp .env.example .env
```

Now open `.env` in any text editor and fill it in:

```env
DATABASE_URL=postgresql://detective:secret@localhost:5432/detectiveos
ANTHROPIC_API_KEY=sk-ant-api03-put-your-real-key-here
JWT_SECRET=any-long-random-string-you-choose-abc123xyz789
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500
```

**Where to get your Anthropic API key:**
1. Go to https://console.anthropic.com
2. Click "API Keys" → "Create Key"
3. Copy it and paste it as `ANTHROPIC_API_KuEY`

**JWT_SECRET:** Type any long random string. It just needs to be secret. Example: `detective-os-secret-key-2026-xyz-abc-999`

**REDIS_URL:** Redis is optional in development. If you don't have Redis installed, nothing breaks — just leave it as-is.

---

### Step 5 · Run Database Migrations

```bash
# Make sure you're inside backend/ and venv is active
alembic upgrade head
```

This creates all tables in your database. You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial schema
```

---

### Step 6 · Seed the Database

```bash
python -m app.db.seed
```

Expected output:
```
✓ Created demo user: detective@demo.com / password123
✓ Seeded case: The Midnight Manor Incident [WEEKLY]
✓ Seeded case: Harbor Street Blackout
✓ Seeded case: The Redwood Inheritance
✓ Seeded case: Double Exposure
✓ Seeded case: The Zodiac Protocol
✓ Seeded case: The Glass Garden
✅ Database seeded successfully.
```

---

### Step 7 · Start the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Your API is live. Keep this terminal running.

**Useful URLs:**
| URL | What |
|-----|------|
| http://localhost:8000/api/health | Health check (should return `{"status":"ok"}`) |
| http://localhost:8000/api/docs | Interactive API docs (Swagger UI) |
| http://localhost:8000/api/cases | List all cases (JSON) |

---

### Step 8 · Open the Frontend

Open a **new terminal** (keep the backend running in the first one).

**Option A — VS Code Live Server (easiest):**
1. Open the `detectiveos` folder in VS Code
2. Install the "Live Server" extension (search in Extensions panel)
3. Right-click `frontend/index.html` → **"Open with Live Server"**
4. Your browser opens at `http://127.0.0.1:5500`

**Option B — Python server:**
```bash
cd detectiveos/frontend
python -m http.server 3000
```
Then open http://localhost:3000

**Option C — Just double-click:**
Open `frontend/index.html` directly. Some API calls may fail due to browser security with `file://` URLs — use Option A or B if you see errors.

---

## Demo Account

Log in immediately without registering:

| | |
|---|---|
| **Email** | `detective@demo.com` |
| **Password** | `password123` |
| **Tier** | Pro (unlimited AI questions) |

---

## How to Play

1. **Browse Cases** (`cases.html`) — Six mysteries, three difficulty levels
2. **Open a Case** — Read the background story, victim profile, and timeline
3. **Examine Evidence** — Click each card to read forensic reports, phone logs, CCTV analysis
4. **Interrogate Suspects** — Ask any question. The AI plays each character. Guilty ones lie strategically. Innocent ones sometimes reveal things under pressure.
5. **Build Your Board** — Drag pins onto the canvas, draw wire connections between evidence and suspects
6. **Submit Your Theory** — Choose the culprit, write your motive and method, cite the evidence
7. **Get Your Score** — See the breakdown and where you fell short

---

## Scoring System

| Category | Max Points | How It Works |
|----------|-----------|--------------|
| Culprit | 40 | Exact match with the true culprit's name |
| Motive | 20 | Claude grades your reasoning semantically against the true motive |
| Evidence | 25 | 8 pts per required evidence piece you correctly cited |
| Speed | 15 | Under 30 min = 15 pts, under 1 hr = 12 pts, under 2 hr = 8 pts |
| **Total** | **100** | |

XP earned = (score × 2) + 100 bonus if you got the culprit right

---

## The 6 Cases

| # | Title | Difficulty | Victim | Setting |
|---|-------|-----------|--------|---------|
| 1 | The Midnight Manor Incident ⚡ | Mastermind | Victor Harrington | Cotswolds, UK |
| 2 | Harbor Street Blackout | Detective | Dana Morse | San Francisco |
| 3 | The Redwood Inheritance | Rookie | Isabelle Calloway | Napa Valley |
| 4 | Double Exposure | Detective | Felix Crane | New York City |
| 5 | The Zodiac Protocol | Mastermind | Dr. Asha Rao | Austin, TX |
| 6 | The Glass Garden | Detective | Prof. Emil Voss | Vienna, Austria |

⚡ = Weekly Challenge (marked with a red banner on the cases page)

---

## API Quick Reference

All endpoints live at `http://localhost:8000`

**Auth**
```
POST /api/auth/register    body: { email, username, password, avatar }
POST /api/auth/login       body: { email, password }
GET  /api/auth/me          header: Authorization: Bearer <token>
```

**Cases**
```
GET  /api/cases                          → list all cases
GET  /api/cases/{slug}                   → full case (suspects + evidence)
POST /api/cases/{slug}/start             → begin a case, creates your progress record
GET  /api/cases/{slug}/progress          → your board state, interrogations so far
PUT  /api/cases/{slug}/board             → save board state (pins + connections)
```

**Interrogation**
```
POST /api/interrogate/{suspect_id}
  body: { message: "your question", history: [...] }
  → { reply, suspect_name, questions_remaining }
```

**Solutions**
```
POST /api/cases/{slug}/solve
  body: { culprit_name, motive, method, evidence_cited: ["id1", "id2"] }
  → { is_correct, score, breakdown, true_culprit, verdict_message, xp_earned }

GET /api/cases/{slug}/solution           → reveals true answer (only after submitting)
```

**Leaderboard**
```
GET /api/leaderboard/global
GET /api/leaderboard/weekly
GET /api/leaderboard/case/{slug}
```

---

## Database Tables

```sql
users            id, email, username, password_hash, tier, xp, cases_solved, avatar
cases            id, title, slug, difficulty, background, victim_name, true_culprit_name, true_motive, true_method
suspects         id, case_id, name, occupation, personality, alibi, secrets, is_culprit
evidence         id, case_id, type, title, description, content, icon, is_hidden, unlock_condition
case_progress    id, user_id, case_id, started_at, board_state, interrogated_suspects, interrogation_history
player_solutions id, user_id, case_id, culprit_name, motive, method, evidence_cited, score, is_correct
leaderboard      id, user_id, week, score
```

---

## Tier Limits

| Feature | Free | Pro ($9.99/mo) | Creator ($24.99/mo) |
|---------|------|----------------|----------------------|
| Cases per month | 1 | Unlimited | Unlimited |
| AI interrogation questions | 10 total | Unlimited | Unlimited |
| Evidence board | ✓ | ✓ | ✓ |
| Weekly challenge | ✓ | ✓ | ✓ |
| Case creation tools | ✗ | ✗ | ✓ |

---

## Running Tests

```bash
cd backend
# venv must be active
pytest tests/ -v
```

---

## Common Problems & Fixes

**`ModuleNotFoundError: No module named 'fastapi'`**
Your virtual environment isn't active.
```bash
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

**`could not connect to server: Connection refused` (PostgreSQL)**
PostgreSQL isn't running. Start it:
```bash
brew services start postgresql@15    # Mac
sudo systemctl start postgresql      # Linux
```

**`ANTHROPIC_API_KEY not set` or interrogation returns an error**
Check that your `.env` file exists inside `backend/` and contains the key. Make sure you're running `uvicorn` from inside the `backend/` directory, not from the project root.

**Frontend API calls fail with CORS error**
You opened `index.html` directly with `file://`. Use VS Code Live Server or `python -m http.server 3000` instead.

**`alembic: command not found`**
Alembic didn't install, or venv isn't active. Run:
```bash
pip install alembic
```

**`relation "users" does not exist`**
You haven't run the migrations yet.
```bash
alembic upgrade head
```

**Seed script fails with duplicate key error**
The database was already seeded. That's fine — just start the backend. If you want to reseed from scratch:
```bash
psql -U postgres -c "DROP DATABASE detectiveos;"
psql -U postgres -c "CREATE DATABASE detectiveos;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE detectiveos TO detective;"
alembic upgrade head
python -m app.db.seed
```

---

## How Everything Connects

```
Your Browser
  ↕  HTTP requests (fetch API)
frontend/js/api.js
  ↕
http://localhost:8000  ← uvicorn running your FastAPI app
  ↕
PostgreSQL on port 5432  ← your local database
  ↕
Anthropic Claude API  ← for suspect dialogue and motive scoring
  (internet required for this part)
```

---

## Files You Should Know

| File | What to edit |
|------|-------------|
| `backend/.env` | API keys, database URL |
| `backend/app/services/ai_interrogation.py` | Change how suspects respond |
| `backend/app/services/scoring_engine.py` | Change the scoring formula |
| `case-templates/*.json` | Edit or create mystery cases |
| `frontend/css/global.css` | Change the design/colours |
| `frontend/case.html` | The main game page |

---

*Built with noir aesthetics and a burning obsession for the truth.*
