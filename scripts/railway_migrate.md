# Railway migration (one-time)
After deploy:
1) Open Railway service → Shell
2) Run:
```bash
cd /app
alembic -c alembic.ini upgrade head
```
