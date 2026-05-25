# Implementation Plan - SentryText Cyberbullying Detection & Prevention Web Application

We have updated the schemas and implementation plan for **SentryText** to ensure that the primary key of every table is named **`Id`**.

---

## User Review Required

Please review the revised database schemas and directory layout before approving.

### 1. Technology Stack
* **Project Name:** SentryText
* **Backend Framework:** **FastAPI** (Python) under the **`api`** folder. Isolated dependencies inside a Python virtual environment (`venv`).
* **Frontend Framework:** **ReactJS** (bootstrapped with Vite) under the **`spa`** folder, styled using **Tailwind CSS**.
* **Database System:** **Local MySQL** (Database Name: `sentryText_db`).
* **Authentication:** **JWT (JSON Web Tokens)** for secure, stateless user/admin login.

### 2. Database Schema Corrections (Applied to PRD)
* **Table Primary Keys:** All tables use **`Id`** as their primary key.
* **Direct Messages Moderation:** Implemented the `messages` table with `SenderId`, `ReceiverId`, and `ModerationStatus` (Approved/Blocked) to support proactive chat moderation.
* **Telemetry Correlation:** Added a `ContentType` column (`'post'`, `'comment'`, or `'message'`) to the `prediction_results` table to avoid ID collisions in logs.
* **Hashed Passwords Storage:** Set password sizes to `VARCHAR(255)` to support cryptographic password hashing (bcrypt).

### 3. Machine Learning & Preprocessing
* **Preprocessing:** Standard Python data-cleaning pipeline (lowercasing, tokenization, punctuation removal, stop-word filtering, and Porter stemming).
* **Model Pipeline:** A training script (`scripts/train_model.py`) will fit and evaluate Logistic Regression and SVM classifiers on the combined datasets (incorporating local African/Nigerian slang terms), saving the models as serialized `.joblib` files.
* **Consensus Resolution:** If *either* classifier flags the content as harmful, it is blocked.

---

## Proposed Database Schema (MySQL - `sentryText_db`)

### 1. `users` Table
```sql
CREATE TABLE users (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL,
    Gender VARCHAR(10) NULL,
    DateRegistered DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. `posts` Table
```sql
CREATE TABLE posts (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    PostContent TEXT NOT NULL,
    ModerationStatus VARCHAR(20) NOT NULL DEFAULT 'Pending', -- Approved, Blocked, Flagged
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserId) REFERENCES users(Id) ON DELETE CASCADE
);
```

### 3. `comments` Table
```sql
CREATE TABLE comments (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    PostId INT NOT NULL,
    UserId INT NOT NULL,
    CommentText TEXT NOT NULL,
    ModerationStatus VARCHAR(20) NOT NULL DEFAULT 'Pending', -- Approved, Blocked, Flagged
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PostId) REFERENCES posts(Id) ON DELETE CASCADE,
    FOREIGN KEY (UserId) REFERENCES users(Id) ON DELETE CASCADE
);
```

### 4. `messages` Table (Revised)
```sql
CREATE TABLE messages (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    SenderId INT NOT NULL,
    ReceiverId INT NOT NULL,
    MessageText TEXT NOT NULL,
    ModerationStatus VARCHAR(20) NOT NULL DEFAULT 'Approved', -- Approved, Blocked, Flagged
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SenderId) REFERENCES users(Id) ON DELETE CASCADE,
    FOREIGN KEY (ReceiverId) REFERENCES users(Id) ON DELETE CASCADE
);
```

### 5. `prediction_results` Table (Revised)
```sql
CREATE TABLE prediction_results (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    ContentId INT NOT NULL,                                   -- References posts(Id), comments(Id), or messages(Id)
    ContentType VARCHAR(20) NOT NULL,                         -- 'post', 'comment', or 'message'
    Classification VARCHAR(20) NOT NULL,                     -- Harmful, Non-Harmful
    ConfidenceScore FLOAT NOT NULL,                           -- Model confidence percentage (0.0 - 100.0)
    ModerationStatus VARCHAR(20) NOT NULL,                    -- Approved, Blocked, Flagged
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6. `admin` Table
```sql
CREATE TABLE admin (
    Id INT AUTO_INCREMENT PRIMARY KEY,
    AdminName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL
);
```

---

## Proposed Directory Structure

```
SentryText/ (root)
│
├── api/                      # FastAPI Backend application (folder "api")
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # Application entry point & router aggregation
│   │   ├── config.py         # Reads configuration from environment
│   │   ├── database.py       # SQLAlchemy engine & session configurations
│   │   ├── models.py         # DB models representing target MySQL tables
│   │   ├── schemas.py        # Pydantic validation schemas (requests/responses)
│   │   │
│   │   ├── ml_engine/
│   │   │   ├── __init__.py
│   │   │   ├── preprocessor.py # Text preprocessing pipeline (Stemming, lowercasing, etc.)
│   │   │   └── classifier.py   # TF-IDF, Logistic Regression & SVM dual classification
│   │   │
│   │   └── routes/
│   │       ├── auth.py       # Register & login APIs (JWT-based)
│   │       ├── feed.py       # Post creation, reading feed, commenting APIs
│   │       ├── chat.py       # Messaging APIs
│   │       ├── auditor.py    # Third-party copy-paste auditing APIs
│   │       └── admin.py      # Telemetry summary and Audit log grid data endpoints
│   │
│   ├── scripts/
│   │   ├── train_model.py    # Pipeline to compile datasets and output classifiers
│   │   ├── seed_db.py        # Creates database structure and inserts initial records
│   │   └── slang_dictionary.py # Curated dictionary of Nigerian/African Pidgin terms
│   │
│   ├── models/               # Serialized model directory
│   │   ├── lr_model.joblib
│   │   ├── svm_model.joblib
│   │   └── tfidf_vectorizer.joblib
│   │
│   ├── venv/                 # Python Virtual Environment
│   ├── requirements.txt      # fastapi, uvicorn, sqlalchemy, scikit-learn, joblib, bcrypt, PyJWT, aiomysql, cryptography
│   └── .env.template         # DB host, port, credentials (sentryText_db), and JWT secrets
│
├── spa/                      # ReactJS Frontend application (folder "spa", Vite + Tailwind CSS)
│   ├── src/
│   │   ├── assets/
│   │   ├── components/       # UI components (PostCard, CommentInput, AlertModal, etc.)
│   │   ├── pages/            # Page layouts (LoginRegister, Feed, Chat, SafetyCenter, AdminDashboard, Auditor)
│   │   ├── services/
│   │   │   └── api.js        # Axios/Fetch integration with backend endpoints
│   │   ├── styles/
│   │   │   └── index.css     # Tailwind directives (@tailwind base; etc.) and custom theme rules
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── tailwind.config.js    # Tailwind configuration (content paths, colors, theme extension)
│   ├── postcss.config.js     # PostCSS setup for Tailwind CSS
│   ├── package.json          # React, react-router-dom, tailwindcss, autoprefixer, postcss, lucide-react, axios
│   ├── vite.config.js
│   └── index.html
│
└── README.md
```

---

## Verification Plan

### Automated Verification
* **Model Endpoint Tests:** Use FastAPI's `TestClient` (running inside virtual environment context) to send mock requests (e.g. POST to `/api/posts/create` with clean and toxic inputs) and verify that the API returns the correct classification and database state.
* **Preprocessing Validation:** Check text cleaning pipelines against target Nigerian slang inputs to verify stemming and stopwords removal.

### Manual Verification
1. **Virtual Environment Setup:** Activate `api/venv` and run `pip install -r requirements.txt`. Run `uvicorn` and verify the server starts on `http://localhost:8000`.
2. **User Sign Up & Login:** Test React input states, submit registration, and verify JWT token cookies.
3. **Post/Comment Submission:** Confirm that toxic content displays a warning alert styled beautifully with Tailwind (red border, glass shadow, warning icon) and is blocked before feed insertion.
4. **External Auditor Interface:** Verify copy-pasted abuse displays classification percentages from both classifiers clearly in a Tailwind dashboard grid.
5. **Admin Dashboard:** Access `/admin` page and check that stats, graphs, and the audit log table render correctly in Tailwind CSS.
