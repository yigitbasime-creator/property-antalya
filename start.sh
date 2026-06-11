#!/bin/bash
set -e

echo "==> Creating tables..."
uv run python -c "
from app.database import engine
from app import models
models.Base.metadata.create_all(bind=engine)
print('Tables ready.')
"

echo "==> Checking if database needs seeding..."
uv run python -c "
from app.database import SessionLocal
from app.models import User
db = SessionLocal()
count = db.query(User).count()
db.close()
import sys
sys.exit(0 if count > 0 else 1)
" && echo "==> Database already seeded, skipping." || (echo "==> Seeding database..." && uv run python seed.py)

echo "==> Starting server on port ${PORT:-8000}..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
