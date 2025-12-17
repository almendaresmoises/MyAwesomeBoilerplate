Prerequisites:
Installed python 3.14
Installed uv
Installed postgresql (running)

rename .env.sample to .env

update .env

uv sync

uv run alembic upgrade head

uv run uvicorn app.main:app --reload

visit-> http://localhost:8000/docs