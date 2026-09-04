# Covoiturage

Plateforme de covoiturage (API Django + Frontend + Admin métier).

## Stack
- Django 5 + DRF + SimpleJWT
- PostgreSQL + Redis + Celery
- Frontend templates (Tailwind)
- Admin métier custom

## Démarrage rapide

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ou créer .env
sudo docker compose up -d   # Postgres + Redis
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver