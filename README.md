# 🛒 Supershop Bangladesh Management System

The system models the operations of a multi-city supershop chain in Bangladesh, supporting branch management, customers, employees, products, memberships, sales, online orders, and inventory activities. The project includes database design, normalization, SQL implementation, analytical queries, and a web-based interface.

## 📖 Project Overview

The objective of this project is to design and implement a relational database system for a large supershop chain operating across multiple cities in Bangladesh.

The system supports:

- Multi-city and multi-branch operations
- Customer and membership management
- Employee administration
- Product and category management
- Sales transaction processing
- Online order management
- Inventory tracking
- Business reporting through SQL queries
- Web-based interaction with the database

## 1. INSTALL THESE FIRST (one time only)

- Python 3.11+ → https://python.org/downloads
- VS Code      → https://code.visualstudio.com
- Git          → https://git-scm.com

### VS Code Extensions to install
Open VS Code → press Ctrl+Shift+X → search and install:
- Python (by Microsoft)
- Pylance (by Microsoft)
- Thunder Client   ← test your API without Postman
- HTML CSS Support
- Auto Rename Tag
- Prettier – Code formatter
- GitLens


## 2. FOLDER STRUCTURE

Create a folder called `supershop-web` anywhere on your PC.
Inside it, create exactly this layout:

```
supershop-web/
│
├── main.py              ← FastAPI app (all backend code)
├── database.py          ← PostgreSQL connection helper
├── requirements.txt     ← Python packages
├── Procfile             ← tells Railway how to start the app
├── .env                 ← your secret DB password (never upload)
├── .gitignore           ← files Git should ignore
│
├── templates/           ← HTML pages (Jinja2)
│   ├── base.html        ← shared navbar + layout
│   ├── index.html       ← dashboard / home
│   ├── products.html
│   ├── sales.html
│   ├── customers.html
│   └── branches.html
│
└── static/
    └── js/
        └── utils.js     ← shared JS helpers
```

Open this folder in VS Code:
File → Open Folder → select supershop-web



## 3. FILE CONTENTS (copy each one exactly)



### requirements.txt

```
fastapi
uvicorn
jinja2
aiofiles
psycopg2-binary
python-dotenv
python-multipart
bcrypt
itsdangerous
```



### .gitignore

```
.env
__pycache__/
*.pyc
.venv/
venv/
```


### .env  (replace with YOUR actual PostgreSQL credentials)

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/supershop
```

When deployed on Railway, you delete this line and Railway injects
DATABASE_URL automatically.


### Procfile

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 4. RUNNING LOCALLY (VS Code terminal)

Open VS Code terminal (Ctrl + ` backtick), then run these commands
one by one — only do the venv steps once:

```bash
# Step 1: create virtual environment (only once)
python -m venv venv

# Step 2: activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Step 3: install packages (only once, or after requirements.txt changes)
pip install -r requirements.txt

# Step 4: start the server
uvicorn main:app --reload
```

Then open browser:
- http://localhost:8000          → Dashboard
- http://localhost:8000/products → Products page
- http://localhost:8000/docs     → Auto API documentation  ← show this in presentation!

The `--reload` flag means the server restarts automatically every time
you save a file. You don't need to stop and restart manually.



## 5. DEPLOY ON RAILWAY (step by step)

### 5a. Push to GitHub

```bash
# In VS Code terminal:
git init
git add .
git commit -m "first commit"
```

Go to github.com → New repository → name it `supershop-web`
→ copy the commands GitHub shows you (they look like):

```bash
git remote add origin https://github.com/YOUR_USERNAME/supershop-web.git
git branch -M main
git push -u origin main
```

### 5b. Deploy on Railway

1. Go to https://railway.app → Sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `supershop-web` repository
4. Railway detects Python automatically and starts building

### 5c. Add PostgreSQL on Railway

1. Inside your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway creates a PostgreSQL instance for you

### 5d. Import your database

1. Click the PostgreSQL service → "Data" tab → "Connect"
2. Copy the connection string (looks like postgresql://...)
3. Use pgAdmin or psql to run your DDL and INSERT scripts on this URL:

```bash
psql "postgresql://postgres:xxxx@xxx.railway.app:5432/railway" -f schema.sql
psql "postgresql://postgres:xxxx@xxx.railway.app:5432/railway" -f data.sql
```

### 5e. Link DATABASE_URL

1. Click your Flask/FastAPI service in Railway
2. Go to "Variables" tab
3. Railway should already show DATABASE_URL from the linked PostgreSQL
4. If not: click "Add Variable" → DATABASE_URL → paste the connection string

### 5f. Get your live URL

Railway gives you a free domain like:
`https://supershop-web-production.up.railway.app`

Every time you `git push`, Railway redeploys automatically.



## 6. CHEATSHEET — Most Common Mistakes

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: fastapi` | Did you activate venv? Run `venv\Scripts\activate` first |
| `address already in use` | Port 8000 is busy. Run `uvicorn main:app --reload --port 8001` |
| Templates not found | Make sure folder is named `templates` (lowercase), not `Templates` |
| `.env` not working | Make sure `load_dotenv()` is called at the top of `database.py` |
| Railway deploy fails | Check that `Procfile` has no typos and `requirements.txt` is complete |
| Blank page on Railway | DATABASE_URL variable missing — check Railway Variables tab |



## 7. WHAT TO SHOW IN PRESENTATION

1. Open the live Railway URL — show the Dashboard with stat cards
2. Go to /products — demo the live search box
3. Go to /sales — demo the filter dropdowns
4. Go to /branches — show the card layout
5. **Go to /docs** — this is the most impressive part.
   FastAPI auto-generates an interactive API page. Click any endpoint,
   click "Try it out", click "Execute" — it runs the SQL live.
   This proves your database queries work.

## 📄 License
This repository is intended for academic and educational purposes only.
