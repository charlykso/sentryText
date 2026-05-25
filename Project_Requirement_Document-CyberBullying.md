# PROJECT REQUIREMENTS DOCUMENT (PRD) - SentryText

**Project Name:** SentryText
**Project Topic:** Design and Implementation of a Machine Learning–Based Web Application for Detecting Cyberbullying in Online Text Comments.
**Document Version:** 1.2 (Updated with Project Name, Tailwind CSS, & MySQL Database Specifications)

**Target Database System:** Local MySQL (Database Name: `sentryText_db`)
**Backend Framework:** FastAPI (Python)
**Frontend Framework:** ReactJS (Styled with Tailwind CSS)

---

## 1. Project Overview & Objectives

The purpose of this project is to develop a web-based, interactive mini social media application integrated with a proactive Natural Language Processing (NLP) and Machine Learning (ML) moderation engine. Unlike legacy systems that classify content retrospectively (after submission), this system automatically analyzes user-generated content **before publication**. Harmful content is blocked or flagged instantly, while safe content is allowed to be posted.

### Core Project Objectives:

- Design an interactive social media-style web interface for user post creation, commenting, messaging, and real-time prediction feedback.

- Implement automatic text preprocessing and feature extraction modules for textual data analysis.

- Integrate Logistic Regression and Support Vector Machine (SVM) algorithms for cyberbullying classification.

- Develop a proactive moderation engine capable of allowing, blocking, flagging, or warning users based on prediction outcomes before text publication.

- Provide an administrative dashboard for monitoring live prediction activities, flagged content, and system operations.

---

## 2. System Architecture & Methodology

The system development follows a **hybrid methodology** combining software engineering principles with data science standards:

- **Decoupled Client-Server Architecture:**
  - **Frontend:** Built with **ReactJS** (using Vite for development and bundling) to provide a responsive, components-driven, dynamic Single-Page Application (SPA) user interface.
  - **Backend:** Built with **FastAPI** (Python), exposing high-performance, asynchronous REST APIs for authentication, feed moderation, direct messaging, external text auditing, and admin operations.
  - **Communication:** Decoupled JSON data exchange via asynchronous HTTP fetch requests.

- **Object-Oriented Analysis and Design Methodology (OOADM):** Used for the analysis, structuring, modular design, and frontend-backend connectivity of the web application components.

- **Cross-Industry Standard Process for Data Mining (CRISP-DM):** Drives the machine learning lifecycle, specifically managing data collection, data preparation (preprocessing), feature extraction, modeling, evaluation, and deployment loops.

---

## 3. Functional Requirements

### 3.1 User Interaction Module

- **Account Management:** Users must be able to register an account and log in securely.

- **Content Creation Interface:** Users can input text comments via specific UI elements: text areas for post creation, commenting modules under posts, and a chat message window.

- **External Text Auditing Area:** Provide an interactive input block where users can manually type or paste text content copied from external social networks (e.g., WhatsApp, Facebook, Instagram) to run a cyberbullying analysis before manually sharing it.

- **Proactive Interception Flow:** Upon clicking "Post", "Comment", or "Send", the interface must pause text propagation, route the payload to the preprocessing/ML module, and await the moderation verdict before modifying the feed state.

- **Personal Safety Center:** A dedicated history view rendering platform guidelines (safety tips) and a personalized log tracking the user's historical account interaction flags.

### 3.2 Automated NLP Preprocessing Module

All user-submitted text strings must pass sequentially through an automated data-cleaning pipeline:

1.  **Lowercasing:** Standardizes all incoming characters into lowercase format to remove case variance.

2.  **Tokenization:** Segments character rows into standalone word units (tokens).

3.  **Stop-word Removal:** Discards non-semantic structural anchors (e.g., "is", "the", "and") that carry no contextual weight.

4.  **Punctuation Removal:** Filters out structural URLs, specialized symbols, and punctuation noise.

5.  **Stemming:** Truncates derived word variations to their base linguistic roots to reduce vector space dimensionality.

### 3.3 Feature Extraction & Machine Learning Module

- **Vectorization Engine:** Implements **TF-IDF (Term Frequency-Inverse Document Frequency) Vectorization** to map cleaned tokens into distinct weighted numerical feature vectors.

- **Dual-Classifier Pipeline:** Evaluates the generated feature space simultaneously using two supervised algorithms:

1.  **Logistic Regression**

2.  **Support Vector Machine (SVM)**

- **Binary Target Classification:** Categorizes inputs explicitly into two predefined class labels:

- `Cyberbullying (Harmful)`

- `Non-Cyberbullying (Non-Harmful)`

### 3.4 Moderation & Guardrail Engine

Evaluates classification outputs and executes automated status resolutions in real time:

- **Automated Content Approval:** If content is classified as non-harmful, the engine updates its database state to `Approved`, successfully publishes the post/message, and renders it to the feed.

- **Automated Interdiction (Block):** If cyberbullying expressions are detected, the system blocks or flags the content from public view, logs the violation, and triggers a warning pop-up requesting the user to edit their text (e.g., _"Warning: Harmful Content Detected. Please modify your message before posting."_).

### 3.5 Administrative Dashboard Module

- **Privileged Access Gate:** A secure, isolated login portal for administrators.

- **Operations Telemetry Panel:** A live monitoring layout tracking global platform metrics: total users, global post counts, total flagged violations, and active system reports.

- **Granular Moderation Review Grid:** A tabular display showing the raw submitted text, the machine learning classification label, model confidence probabilities ($\%$ scores), automated actions taken, and explicit generation timestamps.

---

## 4. Data Requirements & Schema Specifications

### 4.1 Data Sourcing Strategy

The modeling and training pipeline uses a hybrid dataset approach:

- **Public Secondary Sources:** Jigsaw Toxic Comment Classification Dataset, Kaggle Toxic Comment Dataset, and the Twitter Hate Speech Dataset (Davidson et al., 2017).

- **Localized Context Samples:** Manually collected text inputs explicitly adapted to capture African and Nigerian linguistic expressions, local idioms, abbreviations, and regional online slang patterns.

### 4.2 Database Design (MySQL Layout)

Data consistency and relational integrity must be maintained using explicit primary key (PK) and foreign key (FK) constraints.

#### Table 4.1: `users`

| Field | Data Type | Null | Key | Default          | Description                              |
| ----- | --------- | ---- | --- | ---------------- | ---------------------------------------- |
| `Id`  | `int(11)` | No   | PRI | _auto_increment_ | Unique identifier assigned to each user. |

|
| `Username` | `varchar(50)` | No | | | Unique profile name of the registered user.

|
| `Email` | `varchar(100)` | No | | | User account contact email address.

|
| `Password` | `varchar(255)` | No | | | Cryptographically secured user password (length increased to support secure password hashing like bcrypt).

|
| `Gender` | `varchar(10)` | Yes | | `NULL` | Optional gender profile assignment.

|
| `DateRegistered` | `datetime` | No | | `CURRENT_TIMESTAMP` | Date and time the user account was registered.

|

#### Table 4.2: `posts`

| Field | Data Type | Null | Key | Default          | Description                                   |
| ----- | --------- | ---- | --- | ---------------- | --------------------------------------------- |
| `Id`  | `int(11)` | No   | PRI | _auto_increment_ | Unique identifier assigned to each user post. |

|
| `UserID` | `int(11)` | No | FK | | Maps back to origin user profile via `users(UserID)`.

|
| `PostContent` | `text` | No | | | Raw body text submitted by the post author.

|
| `ModerationStatus` | `varchar(20)` | No | | `'Pending'` | Status indicator: Approved, Blocked, or Flagged.

|
| `Timestamp` | `datetime` | No | | `CURRENT_TIMESTAMP` | Date and time the post entry was generated.

|

#### Table 4.3: `comments`

| Field | Data Type | Null | Key | Default          | Description                                 |
| ----- | --------- | ---- | --- | ---------------- | ------------------------------------------- |
| `Id`  | `int(11)` | No   | PRI | _auto_increment_ | Unique identifier tracking comment entries. |

|
| `PostID` | `int(11)` | No | FK | | Maps to target post identifier via `posts(PostID)`.

|
| `UserID` | `int(11)` | No | FK | | Maps to commenting user profile via `users(UserID)`.

|
| `CommentText` | `text` | No | | | Raw text content of the submitted comment.

|
| `ModerationStatus` | `varchar(20)` | No | | `'Pending'` | Automated tracking resolution outcome state.

|
| `Timestamp` | `datetime` | No | | `CURRENT_TIMESTAMP` | System tracking event timeline timestamp.

|

#### Table 4.4: `messages`

| Field | Data Type | Null | Key | Default          | Description                                     |
| ----- | --------- | ---- | --- | ---------------- | ----------------------------------------------- |
| `Id`  | `int(11)` | No   | PRI | _auto_increment_ | Unique identifier for each direct chat message. |

|
| `SenderId` | `int(11)` | No | FK | | Maps to sending user profile via `users(UserID)`.

|
| `ReceiverID` | `int(11)` | No | FK | | Maps to receiver user profile via `users(ReceiverID)`.
|
| `MessageText` | `text` | No | | | Raw body text content of the chat message.

|
| `ModerationStatus` | `varchar(20)` | No | | `'Approved'` | Automated tracking resolution outcome: Approved, Blocked, or Flagged.

|
| `Timestamp` | `datetime` | No | | `CURRENT_TIMESTAMP` | Date and time the chat message was sent.

|

#### Table 4.5: `prediction_results`

| Field | Data Type | Null | Key | Default          | Description                                    |
| ----- | --------- | ---- | --- | ---------------- | ---------------------------------------------- |
| `Id`  | `int(11)` | No   | PRI | _auto_increment_ | Primary key indexing tracking event instances. |

|
| `ContentID` | `int(11)` | No | | | Reference mapping tracking original post, comment, or message ID.

|
| `ContentType` | `varchar(20)` | No | | | Type of audited content: post, comment, or message (added for clarity).

|
| `Classification` | `varchar(20)` | No | | | Resolution class: Harmful or Non-Harmful.

|
| `ConfidenceScore` | `float` | No | | | Mathematical probability metric generated by the model.

|
| `ModerationStatus` | `varchar(20)` | No | | | Final structural action: Approved, Blocked, or Flagged.

|
| `Timestamp` | `datetime` | No | | `CURRENT_TIMESTAMP` | Log timestamp tracking evaluation moment.

|

#### Table 4.6: `admin`

| Field | Data Type | Null | Key | Default          | Description                                      |
| ----- | --------- | ---- | --- | ---------------- | ------------------------------------------------ |
| `Id`  | `int(11)` | No   | PRI | _auto_increment_ | Unique identifier for the administrator account. |

|
| `Name` | `varchar(50)` | No | | | Profile name of the system administrator.

|
| `Email` | `varchar(100)` | No | | | Administrator email registration target.

|
| `Password` | `varchar(255)` | No | | | Cryptographically secured admin password (length increased for security).

|

---

## 5. Non-Functional Requirements

### 5.1 Performance & Compute Constraints

- **Computational Efficiency:** The machine learning components must prioritize lightweight, resource-efficient algorithms (Logistic Regression and SVM) rather than deep learning or heavy transformer architectures. This keeps the hardware profile low and suitable for practical deployment in resource-constrained hosting environments.

- **Low-Latency Operational Window:** Text preprocessing, vector space conversion, and dual-model text classification must execute within a tight sub-second processing window so that proactive text filtering does not create visual delay or degrade user interaction.

### 5.2 Usability & System Interaction

- **Frictionless Background Audits:** Standard messaging, posting, and commenting feeds must run text moderation scanning completely in the background without requiring manual "Analyze" confirmation steps from the user.

- **Clear Visual Indicators:** Front-end layouts must be responsive and present immediate, descriptive system warning notifications whenever a comment is blocked by a cyberbullying violation.

### 5.3 Reliability & Scalability

- **Relational Database Constraints:** The schema must implement explicit relational mapping rules via primary and foreign key definitions to safeguard data consistency across the application ecosystem.

- **Decoupled Program Modules:** The functional codebase blocks (UI Presentation, Preprocessing Module, ML Classification Engine, Database Management Module) must be designed as independent, decoupled program units. This ensures that underlying model adjustments or parameter updates can be applied smoothly without rewriting the core business layers.

---

## 6. Success & Evaluation Metrics

The diagnostic performance of the supervised models will be rigorously evaluated against divided test arrays (split into validation datasets) using the following four standard metrics:

- **Accuracy:** Measures the overarching proportion of correctly predicted safe and harmful text instances relative to the entire evaluation pool.

- **Precision:** Tracks model reliability by measuring the exact proportion of true cyberbullying occurrences against the cumulative total flagged by the engine.

- **Recall (Sensitivity):** Judges the system's capacity to successfully identify true malicious offenses, ensuring implicit or explicit cyberbullying content is not missed.

- **F1-Score:** Calculates the harmonic mean of Precision and Recall, providing a stable, unified performance balance metric over unbalanced dataset target classifications.
