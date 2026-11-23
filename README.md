# Smart Campus Complaint Management System
React (Vite) + Flask + MySQL. Students file complaints; admins assign departments, update status, and every change is logged in `complaint_updates`.

## Setup (Windows PowerShell)
1. MySQL: in Workbench run
   `CREATE DATABASE campus_complaints CHARACTER SET utf8mb4; CREATE USER 'campus_user'@'localhost' IDENTIFIED BY 'your_password'; GRANT ALL ON campus_complaints.* TO 'campus_user'@'localhost';`
2. Backend (Python 3.10+):
   ```
   cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env      # edit SECRET_KEY and DATABASE_URL
   python seed.py --demo       # creates tables, departments, first admin (prompts for email/password), demo data
   python run.py               # http://localhost:5000
   ```
3. Frontend (Node 18+): `cd frontend; npm install; npm run dev` then open http://localhost:5173
4. Tests: `cd backend; python -m pytest` (uses in-memory SQLite, no MySQL needed)

Demo student: `demo.student@example.com` / `DemoPass123` (only with `--demo`). Admin: the credentials you typed into `seed.py`.

## Security design
Passwords hashed (Werkzeug); server-side sessions in HttpOnly SameSite=Lax cookies; CSRF token (`/api/auth/csrf` + `X-CSRF-Token` header) on all POST/PATCH; CORS limited to `FRONTEND_ORIGIN`; role checks on every endpoint; students get 404 for other students' complaints; ORM parameterized queries; in-memory login rate limit (5 failures / 5 min per IP); 64 KB request cap. Set `SESSION_COOKIE_SECURE=true` behind HTTPS.

## Database
students 1─* complaints *─1 departments (nullable); complaints 1─* complaint_updates *─1 admins. Tables are created by `db.create_all()` in `seed.py`; re-running never deletes data.

## Workflow transitions
Pending → In Progress/Resolved/Rejected; In Progress → Pending/Resolved/Rejected; Resolved → In Progress (reopen, remarks required); Rejected → Pending. Rejecting/resolving requires remarks; resolving requires resolution details.

## Run for everyone (one URL, Docker)
```
copy .env.example .env      # fill in the four secrets
docker compose up --build   # app + MySQL at http://localhost:5000
```
Flask serves the built React app and the API from the same origin, so the deployment is one URL. To put it online, run the same image on a VPS or a host that runs Docker (Render, Railway, Fly.io, a college server) with a managed MySQL, set `DATABASE_URL`, `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and use HTTPS with `SESSION_COOKIE_SECURE=true`. `database/schema.sql` is the full MySQL schema (regenerate with `python make_schema.py`).

## Accounts
Students self-register. Admins are never self-registered: the first comes from `seed.py`/`ADMIN_EMAIL`, further admins are added by a logged-in admin on the Profile page. Everyone can change their password on Profile.
