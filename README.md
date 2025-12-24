🏥 Empress Desire Hospital Management System (EDHMS)

A full-stack, production-oriented Hospital Management Web Application designed to digitize and streamline hospital operations in resource-constrained and emerging healthcare environments, with extensibility for global use.

This project demonstrates end-to-end system design, business-driven workflows, and clean backend architecture using Django.

🚀 Key Capabilities
Patient & Clinical Operations

Patient registration and profile management (with passport photo)

Visit lifecycle management (check-in → vitals → consultation → closure)

Structured vitals capture and clinical history tracking

Doctor consultation notes and diagnoses

Digital prescriptions workflow

Laboratory & Pharmacy

Lab test requests and results management

Pharmacy dispensing workflow tied to prescriptions

Role-based access for lab scientists and pharmacists

Billing & HMO Management

Patient billing (private and HMO)

HMO enrolment and claims tracking

Separation of clinical care from revenue processes (best practice)

System Design Highlights

Modular Django app architecture (accounts, patients, visits, lab, pharmacy, billing, HMO)

Clean separation of concerns (views, forms, models, templates)

Designed for scalability to PostgreSQL and production hosting

Secure handling of secrets via environment variables

🛠️ Technology Stack
Backend

Python

Django (MVC / MTV architecture)

Django ORM

Frontend

Django Templates

HTML, CSS, JavaScript

Database

SQLite (development)

PostgreSQL-ready (production)

Tooling & Practices

Git & GitHub (clean commit history, proper .gitignore)

Environment-based configuration

Production-ready project structure

📂 Project Structure (Simplified)
empress_desire_hospital/
│
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── accounts/
├── patients/
├── visits/
├── lab/
├── pharmacy/
├── billing/
├── hmo/
│
├── templates/
└── config/


Each module is implemented as an independent Django app to support maintainability and future expansion.

⚙️ Local Development Setup
1️⃣ Clone the repository
git clone https://github.com/wisdomino/empress-desire-hospital-management-system.git
cd empress-desire-hospital-management-system

2️⃣ Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Run migrations
python manage.py migrate

5️⃣ Start development server
python manage.py runserver


Access the app at:

http://127.0.0.1:8000/

🔐 Security & Best Practices

Sensitive data (SECRET_KEY, credentials, .env) are excluded from version control

Virtual environments, databases, and media files are ignored via .gitignore

Project follows GitHub-ready hygiene expected by professional teams

🎯 Use Case

This system is suitable for:

Small to mid-size hospitals

Clinics transitioning from paper-based workflows

Health startups seeking a modular Django foundation

Demonstrating real-world healthcare software design to recruiters

👨‍💻 Author

Lucky Ejakpovi
Electrical Engineer | Business Analyst | Full-Stack Developer

Specialist in:

Healthcare systems

Utility & revenue protection platforms

Business-driven software architecture

📌 Notes for Recruiters

This project demonstrates:

Applied Django beyond tutorials

Domain-specific workflow modeling

Secure, maintainable backend design

Ability to translate real-world operations into software systems