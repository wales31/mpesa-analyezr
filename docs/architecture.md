1. Architecture Overview

The system follows a 3-layer architecture:

Presentation Layer (Frontend)
        ↓
Application Layer (Backend API)
        ↓
Data Layer (Database)

2. Components
2.1 Frontend (Presentation Layer)

Purpose:
Handles user interaction and displays financial insights.

Responsibilities:

Accept transaction message input

Send data to backend API

Display categorized spending

Render charts and summaries

Technologies:

HTML

CSS

JavaScript

Chart.js (visualizations)

2.2 Backend API (Application Layer)

Purpose:
Acts as the system brain. Handles processing, logic, and communication with the database.

Built using FastAPI (Python).

Core Backend Modules
Module	Responsibility
main.py	API entry point
parser.py	Extracts financial details from SMS text
categorizer.py	Assigns transactions to spending categories
insights.py	Generates summaries and financial warnings
models.py	Database table definitions
database.py	Database connection and session handling

2.3 Database Layer

Stores structured financial data.

Development: SQLite
Production-ready: PostgreSQL

Main Table: Transactions

Field	Description
id	Unique transaction ID
amount	Transaction value
category	Spending classification
recipient	Payee or entity
transaction_type	Sent / Received / Paybill
date	Transaction timestamp

3. Data Processing Flow

User submits transaction message
        ↓
Frontend sends request to API
        ↓
parser.py extracts structured data
        ↓
categorizer.py determines spending category
        ↓
Transaction stored in database
        ↓
insights.py analyzes stored data
        ↓
Backend returns financial summary
        ↓
Frontend displays results and charts

4. System Design Principles

Modular Structure — Each function isolated in its own module

Scalable Database Layer — Easy migration from SQLite → PostgreSQL

API-Driven — Frontend and backend communicate via REST

Extensible Categorization — Keywords and logic can be expanded

Privacy-Oriented — Processes financial data locally in development

5. Future Architecture Extensions

User authentication layer

Mobile app integration

Machine learning for smarter categorization

Cloud deployment

Real-time analytics dashboard

6. Repository Structure Mapping
frontend/  → Presentation layer
backend/   → Application logic
database   → Data storage
docs/      → System documentation
tests/     → Validation of core logic
 
mpesa-spending-analyzer/
│
├── README.md
├── CONTRIBUTING.md
├── .gitignore
├── requirements.txt
│
├── docs/
│   ├── architecture.md
│   ├── database.md
│   └── api.md
│
├── backend/
│   ├── main.py            → API entry
│   ├── models.py          → DB tables
│   ├── parser.py          → SMS extraction
│   ├── categorizer.py     → Spending logic
│   ├── insights.py        → Warnings + analysis
│   └── database.db
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── data/
│   ├── betting_keywords.txt
│   ├── food_keywords.txt
│   └── transport_keywords.txt
│
└── tests/
    └── test_parser.py

