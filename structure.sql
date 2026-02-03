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

