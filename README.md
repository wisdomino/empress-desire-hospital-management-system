# Empress Desire Hospital Management System

A Django-based hospital management web application covering patient registration, visits/vitals, consultations, prescriptions, lab requests/results, pharmacy workflow, billing, and HMO claims.

## Features
- Patient registration & profile (with passport photo)
- Visits and vitals capture
- Consultation and prescriptions
- Lab requests and results
- Pharmacy workflow
- Billing and HMO claims management

## Tech Stack
- Python (Django)
- HTML/CSS/JS
- SQLite (development)

## Local Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
