# Walkthrough - SentryText Cyberbullying Detection & Prevention Platform

We have successfully designed, implemented, and verified **SentryText**, a proactive machine learning-based content moderation web application built with **FastAPI (Backend)**, **ReactJS + Tailwind CSS (Frontend)**, and **local MySQL (`sentryText_db`)**.

---

## 1. Accomplishments & Latest Refactorings

### A. Dedicated Single-Vote Likes & Dislikes Relationship Tables
* **Relational Database Design (`api/app/models.py`):**
  - Created two new relationship tables: `post_reactions` and `comment_reactions` with a composite unique constraint `(UserId, PostId)` and `(UserId, CommentId)` respectively.
  - This guarantees that a user can only perform one reaction type per post or comment (it is either a like or a dislike, not both).
* **Toxicity/Safety Dynamic Reactions (`api/app/routes/feed.py`):**
  - Refactored `POST /feed/posts/{id}/like` and `POST /feed/posts/{id}/dislike` to perform reaction toggling:
    - Liking a post that is already liked will remove/toggle off the reaction.
    - Liking a post that was disliked switches the reaction to a like.
    - Otherwise, a new reaction is added.
  - Implemented the identical reaction toggling logic for comments via `POST /feed/comments/{id}/like` and `POST /feed/comments/{id}/dislike`.
  - Maintained high-performance caching by storing counts on `posts` and `comments` table columns, which are updated automatically whenever a user reacts.
* **Axios API Client Refactoring (`spa/src/services/api.js`):**
  - Added `likeComment` and `dislikeComment` endpoints under `feedService`.
* **Frontend React Enhancement (`Feed.jsx`):**
  - Integrated click handlers for comment likes and dislikes.
  - Renders thumbs-up and thumbs-down reaction counts on comments, updating the local UI state dynamically.

### B. Removed LocalStorage Vulnerability (State-Based Cookie Sessions)
* **Backend Refactoring (`api/app/routes/auth.py`):**
  - Configured login/registration endpoints to issue access tokens in secure, `HttpOnly`, `SameSite="Lax"` browser cookies rather than JSON payloads.
  - Implemented `/auth/me` to safely decode session cookies and return active actor profile details (id, name, email, role).
  - Implemented `/auth/logout` to delete the session cookie.
* **Axios API Client Refactoring (`spa/src/services/api.js`):**
  - Enabled `withCredentials: true` globally to allow the browser to include cookies automatically on cross-origin requests.
  - Purged all token request interceptors and `localStorage` mutations.
* **React State Management (`spa/src/context/AuthContext.jsx`):**
  - Created a global `AuthContext` wrapper and `useAuth` hook to store active user profiles in React state rather than the browser storage.
  - Automatically queries `/auth/me` on application load or refresh, displaying a clean glassmorphic spinner while validating.
  - Updated standard/admin routing and pages (such as `Chat.jsx`) to resolve user identities directly from context state.

### C. Admin User Management Directory (`AdminDashboard.jsx`)
* **API Endpoints (`api/app/routes/admin.py`):**
  - Added `GET /admin/users` to return all registered users along with their post counts, comment counts, and safety violation stats.
  - Added `DELETE /admin/users/{user_id}` to purge user profiles. Cascades to remove related posts, comments, direct messages, and prediction audit logs.
* **UI Directory Grid (`AdminDashboard.jsx`):**
  - Integrated tabbed navigation to switch between **Telemetry & Audit Logs** and the **User Directory**.
  - Built an administrative User Directory table displaying user statistics and safety violations (highlighted with color-coded warning badges).
  - Implemented a "Purge User" action opening a modal with detailed confirmation warnings before committing.

### D. System-Wide Dark & Light Mode Theme Toggle & Readability Enhancements
* **Dynamic Styling Variables (`spa/src/index.css`):**
  - Transitioned the Tailwind CSS v4 design system to adapt using CSS custom properties (`--val-dark-50` through `--val-dark-950`).
  - Swapping theme variables (dark background to slate gray, white card container with clean soft shadows) upon toggling the `.light` class on the root element.
  - Configured smooth ease-out CSS transitions for background colors, borders, and shadows to prevent jarring switches.
* **Theme Switching Components (`NavBar`, `LoginRegister`, `AdminLogin`):**
  - Renders a Sun icon when in dark mode (switching to light mode) and a Moon icon when in light mode (switching to dark mode), persisting the preference across refreshes.
* **Contrast & Readability Adjustments:**
  - Removed all hardcoded `text-white` classes from main text elements and headers in [App.jsx](file:///c:/work/CyberBullying-Detector/spa/src/App.jsx), [Chat.jsx](file:///c:/work/CyberBullying-Detector/spa/src/pages/Chat.jsx), [AdminDashboard.jsx](file:///c:/work/CyberBullying-Detector/spa/src/pages/AdminDashboard.jsx), [SafetyCenter.jsx](file:///c:/work/CyberBullying-Detector/spa/src/pages/SafetyCenter.jsx), [Auditor.jsx](file:///c:/work/CyberBullying-Detector/spa/src/pages/Auditor.jsx), [LoginRegister.jsx](file:///c:/work/CyberBullying-Detector/spa/src/pages/LoginRegister.jsx), and [AdminLogin.jsx](file:///c:/work/CyberBullying-Detector/spa/src/pages/AdminLogin.jsx).
  - Replaced these hardcoded white texts with `text-dark-100` and changed hover states from `hover:text-white` to `hover:text-dark-100` so that headings are perfectly readable and adapt dynamically when switching between light and dark themes.
  - Redesigned outgoing message bubbles (`isMe`) in [Chat.jsx](file:///c:/work/CyberBullying-Detector/spa/src/pages/Chat.jsx) to utilize a solid, high-contrast brand background (`bg-brand-600 text-white border-transparent`) instead of a semi-transparent/low-contrast layout, guaranteeing readability on light screens.

### E. Enhanced User Feedback & Blocked Placeholders
* **Global Button Cursor Styling (`index.css`):**
  - Added a global interactive cursor stylesheet setting `cursor: pointer` on all standard buttons, anchor links, select dropdowns, and items with `role="button"`.
  - Configured `cursor: not-allowed !important` for disabled interactive elements to clearly signal non-clickable states.
* **Safe Blocked Content Placeholders (`feed.py` & `chat.py`):**
  - Refactored message, post, and comment API retrieval endpoints to fetch blocked items as well.
  - Implemented strict content-scrubbing rules on the server side: if an item is marked as `Blocked`, its raw content text is replaced with a standard warning placeholder (`🚫 Message blocked by SentryText.`) before being sent to the client, preventing any leakage of cyberbullying texts.
* **Red Warn Layout Style Rendering (`Feed.jsx` & `Chat.jsx`):**
  - Configured feed cards, comment containers, and chat bubbles to detect `ModerationStatus === 'Blocked'`.
  - Renders blocked elements in distinct, light-red alert layouts with color-coded status badges and italicized font-mono text to indicate guidelines violations.

---

## 2. Verification & Automated Test Outputs

We verified SentryText's compilation and build integrity.

* **Vite Compile Verification:**
  - Running `npm.cmd run build` compiled without a single syntax, type, or styling warning.
  - Generated output bundles under `dist/` successfully (Vite v8).
* **FastAPI Server Compilation:**
  - Verified syntax compatibility of python files (`app/routes/admin.py`, `app/routes/feed.py`, `app/routes/chat.py` and `app/main.py`) which compiled with exit code 0.
