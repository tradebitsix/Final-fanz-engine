# Fans of the One Engine — Piece 4 (Production Deploy Glue)

This is the **integration repo** that connects everything:
- Backend (FastAPI) + Postgres + migrations (Alembic)
- Frontend (React/Vite) wired to backend
- Token-based ZIP download (works even when API-key auth is enabled)
- Railway + Vercel config files

## Local run (full stack)
```bash
docker-compose up --build
```
- Backend: http://localhost:8000/health
- Frontend: http://localhost:5173

## Production deploy (Railway + Vercel)
### Railway (backend + Postgres)
1. Create Railway project
2. Add a Postgres plugin → copy `DATABASE_URL`
3. Deploy backend from `backend/` (Dockerfile)
4. Set env vars:
   - `DATABASE_URL` = Railway Postgres URL
   - `FANS_OF_THE_ONE_API_KEY` = set to enable auth (optional)
5. Run migrations once:
   - Railway shell: `cd /app && alembic -c alembic.ini upgrade head`

### Vercel (frontend)
1. Import repo to Vercel
2. Root directory: `frontend`
3. Set env:
   - `VITE_API_BASE_URL` = Railway backend public URL
   - `VITE_API_KEY` = same as backend key (optional)
4. Deploy

## Why Piece 4 exists
Direct file downloads cannot send auth headers. Piece 4 solves this by:
- `POST /engine/export-token` (authorized) → returns a short-lived token
- Browser navigates to `/engine/download/{token}` → downloads ZIP without headers

Endpoints added:
- `POST /engine/export-token`
- `GET /engine/download/{token}`
