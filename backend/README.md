# DocuChat Backend (MVP)

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create .env from sample and adjust values
cp .env.sample .env

# Run DB (expects Postgres+Redis reachable)
python manage.py migrate
python manage.py createsuperuser  # optional
daphne -b 0.0.0.0 -p 8000 backend.asgi:application  # or `python manage.py runserver` for dev
```
HTTP: `http://localhost:8000/api/`  
WS: `ws://localhost:8000/ws/progress?sub=mock-user`
