# SentryText - Proactive Cyberbullying Screening & Prevention Web Application

SentryText is an intelligent, web-based content moderation and digital safety platform. Unlike legacy systems that classify toxic text retrospectively (after publication), SentryText integrates a proactive Machine Learning (ML) and Natural Language Processing (NLP) pipeline that intercept user-generated content **before** it is stored in the database or rendered to the public.

---

## Key Features

1. **Proactive Submission Interception:** Halts text propagation for posts, comments, and direct chat messages, analyzing the payload and prompting users with warnings before publishing.
2. **Dual-Model Classifier Engine:** Simultaneously evaluates text using **Logistic Regression** and **Support Vector Machine (SVM)** models, applying a conservative consensus safety rule.
3. **Local Slang & Dialect Recognition:** Custom structural NLP adaptations trained to detect regional African and Nigerian Pidgin slangs/insults (e.g., "mumu", "olodo", "maga", "thunder fire you") which are absent in standard Western datasets.
4. **Third-Party Content Auditor:** A dedicated auditing workspace where users paste messages from external networks (e.g., WhatsApp, Instagram, Facebook) to run a pre-sharing toxicity audit.
5. **Personal Safety Center:** Displays digital safety guidelines and tracks users' personal historical moderation flags.
6. **Administrative Operations Dashboard:** Live monitoring panel displaying platform telemetry counters (total users, global posts, approved feeds, and blocked violations) alongside a granular searchable log grid.

---

## Technology Stack

* **Backend API Framework:** FastAPI (Python)
* **Frontend SPA Framework:** ReactJS (bootstrapped with Vite)
* **Styling Framework:** Tailwind CSS (utility-first styling with glassmorphism)
* **Database System:** Local MySQL (Database Name: `sentryText_db` with SQLite fallback)
* **Machine Learning Libraries:** Scikit-Learn, NLTK, Joblib

---

## Relational Database Schema (`sentryText_db`)

All tables use `Id` as their primary key. Relational integrity is enforced using explicit foreign key constraints:

* **`users`:** Stores profile handles, emails, gender, and hashed passwords.
* **`posts`:** Tracks user social feed posts and their active moderation state.
* **`comments`:** Stores replies to specific posts.
* **`messages`:** Logs sender-recipient direct messages and delivery safety states.
* **`prediction_results`:** Telemetry log storing model classification labels, confidence percentages, and final actions taken.
* **`admin`:** Stores administrator accounts.

---

## Directory Layout

```
SentryText/
│
├── api/                      # FastAPI Backend
│   ├── app/                  # Main application package
│   │   ├── main.py           # FastAPI entry point
│   │   ├── database.py       # SQLAlchemy setup with SQLite fallback
│   │   ├── models.py         # SQLAlchemy MySQL DB models
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── ml_engine/        # Preprocessing & dual-model classifier
│   │   └── routes/           # Auth, Feed, Chat, Auditor, & Admin routes
│   │
│   ├── scripts/              # Training, seeding, and verification scripts
│   ├── models/               # Serialized .joblib model files
│   ├── venv/                 # Python virtual environment
│   └── requirements.txt      # Backend requirements
│
├── spa/                      # ReactJS + Tailwind CSS Frontend
│   ├── src/                  # Component tree & views
│   │   ├── components/       # Shared UI widgets
│   │   ├── pages/            # View layouts (Feed, Chat, Admin, Safety, etc.)
│   │   └── services/         # Axios API backend connector
│   │
│   ├── tailwind.config.js    # Tailwind configuration
│   ├── postcss.config.js     # PostCSS processing setup
│   └── package.json          # Frontend packages
│
└── README.md
```

---

## Setup & Running Locally

### Prerequisites
* **Python 3.13+** installed locally.
* **Node.js (v18+)** and `npm` installed.
* **MySQL server** running locally.

### 1. Database Creation
Create the database in your local MySQL instance:
```sql
CREATE DATABASE sentryText_db;
```

### 2. Backend Installation & Launch
1. Open a terminal in the `api/` folder.
2. Create and activate the virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Copy `.env.template` to `.env` and adjust your local MySQL credentials:
   ```powershell
   copy .env.template .env
   ```
4. Install packages:
   ```powershell
   pip install -r requirements.txt
   ```
5. Train the ML models and serialize the weights:
   ```powershell
   python scripts/train_model.py
   ```
6. Seed the MySQL database schemas and default profiles (including admin credentials):
   ```powershell
   python scripts/seed_db.py
   ```
7. Start the FastAPI development server:
   ```powershell
   python run.py
   ```
   The backend API will run on **`http://localhost:8000`** (Swagger docs available at `/docs`).

### 3. Frontend Installation & Launch
1. Open a terminal in the `spa/` folder.
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
   The React SPA will open on **`http://localhost:5173`** (or another port outputted in the terminal).

---

## Administrator Login
To access the Operations Dashboard:
* **Email:** `admin@sentrytext.com`
* **Password:** `SentryTextAdmin2026!`
