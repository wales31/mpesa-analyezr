# DESIGN AND IMPLEMENTATION OF AN M-PESA SMS SPENDING ANALYZER FOR PERSONAL FINANCIAL MANAGEMENT

STUDENT NAME: [INSERT FULL NAME]

REGISTRATION NUMBER: [INSERT REG. NUMBER]

A project report submitted in partial fulfillment of the requirements for the award of the degree of Bachelor of Science in [INSERT DEGREE PROGRAM] of Kabarak University.

Department of Computer Science and Information Technology

Kabarak University

February 2026

<<<PAGE_BREAK>>>

# DECLARATION

I declare that this project report is my original work and has not been submitted to this or any other institution for award of a degree, diploma, or certificate.

Student Name: _______________________________

Registration Number: _________________________

Signature: _________________________________

Date: _____________________________________

<<<PAGE_BREAK>>>

# RECOMMENDATION

This project report has been submitted for examination with my approval as the university supervisor.

Supervisor Name: _____________________________

Signature: __________________________________

Date: ______________________________________

Department: Computer Science and Information Technology

Kabarak University

<<<PAGE_BREAK>>>

# COPYRIGHT

Copyright © 2026 [INSERT FULL NAME]

No part of this project report may be reproduced, stored in a retrieval system, or transmitted in any form or by any means without prior written permission of the author or Kabarak University, except for brief quotations in scholarly review.

<<<PAGE_BREAK>>>

# ACKNOWLEDGEMENT

I thank God for the strength and wisdom throughout this project period. I sincerely appreciate my supervisor for the guidance, technical direction, and continuous feedback that shaped this work from proposal to implementation.

I also appreciate the lecturers in the Department of Computer Science and Information Technology for the knowledge and support offered during the course of study. Special thanks go to my classmates and friends for peer reviews, testing assistance, and constructive suggestions during system development.

Finally, I thank my family for moral, emotional, and financial support, which made completion of this project possible.

<<<PAGE_BREAK>>>

# DEDICATION

This report is dedicated to my family for their unwavering support and encouragement, and to all students and young professionals seeking practical technology solutions to improve personal financial management.

<<<PAGE_BREAK>>>

# ABSTRACT

Mobile money has become the dominant transaction channel for many households in Kenya, yet personal spending analysis remains mostly manual and inconsistent. This project presents the design and implementation of an M-PESA SMS Spending Analyzer that converts raw M-PESA confirmation messages into structured transaction records, automatically categorizes expenses, and presents real-time spending summaries through a lightweight web dashboard and an API-driven mobile app foundation. The system was developed using FastAPI for backend services, SQLAlchemy for data persistence, a static HTML/CSS/JavaScript web frontend, and an Expo React Native prototype that prepares the solution for future app-based delivery.

The project adopted an iterative Agile-oriented development approach with mixed methods of requirement gathering, including document analysis, observation of user pain points, and scenario-based validation. Core modules implemented include user authentication, SMS parsing and normalization, hybrid transaction categorization, budget limit management, spending insights, notification generation, and cross-client API access. The system supports single and bulk message analysis, transaction history retrieval, summary visualization, and monthly spending-tracker workflows, while the mobile client currently provides account access, API configuration, and authenticated summary retrieval.

Results show that the prototype effectively reduces manual bookkeeping effort, improves visibility into spending patterns, and supports faster monthly financial reflection. The project demonstrates that simple, explainable analytics built on existing SMS data can provide immediate personal finance value without requiring expensive integrations. Future work will extend the current platform into a fuller spending tracker application with richer mobile workflows, offline synchronization, improved budgeting, and broader message-format coverage.

Keywords: API, budgeting, categorization, financial analytics, M-PESA, mobile app, mobile money, SMS parsing, spending tracker.

<<<PAGE_BREAK>>>

# TABLE OF CONTENTS

DECLARATION ................................................................................. ii

RECOMMENDATION ........................................................................ iii

COPYRIGHT .................................................................................... iv

ACKNOWLEDGEMENT .................................................................... v

DEDICATION ................................................................................... vi

ABSTRACT ...................................................................................... vii

LIST OF TABLES ............................................................................. viii

LIST OF FIGURES ........................................................................... ix

LIST OF ABBREVIATIONS ............................................................... x

CHAPTER ONE: INTRODUCTION .................................................... 1

1.1 Introduction ............................................................................... 1

1.2 Background of the Study ............................................................ 2

1.3 Problem Statement .................................................................... 3

1.4 Objectives ................................................................................. 4

1.5 Research Questions ................................................................... 5

1.6 Significance of the Study ........................................................... 5

1.7 Scope and Limitation of the Study .............................................. 6

1.8 Proposed Modules ..................................................................... 7

CHAPTER TWO: LITERATURE REVIEW .......................................... 8

2.1 Introduction ............................................................................... 8

2.2 Review of Objective One ............................................................ 9

2.3 Review of Objective Two ............................................................ 11

2.4 Review of Objective Three ......................................................... 13

2.5 Review of Objective Four ........................................................... 15

2.6 Conceptual Framework .............................................................. 17

2.7 Literature Gap Summary ............................................................ 18

CHAPTER THREE: METHODOLOGY ............................................... 19

3.1 Introduction ............................................................................... 19

3.2 Research Design ....................................................................... 20

3.2.1 Development Methodology ..................................................... 21

3.3 Data Collection Methods ........................................................... 23

3.4 System Analysis and Design ...................................................... 24

3.5 Research Ethics ........................................................................ 30

CHAPTER FOUR: SYSTEM IMPLEMENTATION AND DEPLOYMENT ... 31

4.1 Introduction ............................................................................... 31

4.2 Development Environment Setup ............................................... 32

4.3 Implementation Steps ................................................................ 34

4.4 Testing and Quality Assurance ................................................... 39

4.5 Deployment Plan ....................................................................... 43

4.6 Go-Live Plan .............................................................................. 45

4.7 Maintenance and Support .......................................................... 46

4.8 Chapter Summary ...................................................................... 48

CHAPTER FIVE: CONCLUSION, RECOMMENDATIONS AND FUTURE WORK ... 49

5.1 Summary of the Study ............................................................... 49

5.2 Key Contributions ...................................................................... 50

5.3 Limitations ................................................................................. 51

5.4 Recommendations ..................................................................... 52

5.5 Future Work ............................................................................... 53

REFERENCES .................................................................................. 54

APPENDICES ................................................................................... 56

<<<PAGE_BREAK>>>

# LIST OF TABLES

Table 3.1 Functional Requirements of the Proposed System

Table 3.2 Non-Functional Requirements of the Proposed System

Table 3.3 Feasibility Analysis Summary

Table 4.1 Development Tools and Environment

Table 4.2 Functional Test Cases and Outcomes

Table 4.3 Deployment and Rollback Checklist

Table A1 Project Budget Estimate

Table C1 Project Schedule

<<<PAGE_BREAK>>>

# LIST OF FIGURES

Figure 2.1 Conceptual Framework for the M-PESA Spending Analyzer

Figure 3.1 High-Level System Architecture

Figure 3.2 Data Flow for Message Analysis and Dashboard Update

Figure 3.3 Use-Case Summary Diagram (Narrative Form)

Figure 4.1 Authentication and Session Flow

Figure 4.2 Transaction Processing Pipeline

Figure 4.3 Dashboard Summary and Notification Workflow

Figure 4.4 Budget Planning and Actual Comparison Flow

<<<PAGE_BREAK>>>

# LIST OF ABBREVIATIONS

API - Application Programming Interface

DB - Database

ERD - Entity Relationship Diagram

HTML - HyperText Markup Language

HTTP - HyperText Transfer Protocol

IDE - Integrated Development Environment

JSON - JavaScript Object Notation

KES - Kenyan Shilling

MVP - Minimum Viable Product

NLP - Natural Language Processing

ORM - Object Relational Mapping

QA - Quality Assurance

REST - Representational State Transfer

SMS - Short Message Service

SQL - Structured Query Language

UAT - User Acceptance Testing

UI - User Interface

UML - Unified Modeling Language

<<<PAGE_BREAK>>>

# CHAPTER ONE

# INTRODUCTION

## 1.1 Introduction

Financial discipline depends heavily on a person’s ability to track cash flow accurately and frequently. In Kenya, M-PESA is one of the most widely used channels for sending, receiving, paying, and withdrawing money. Every transaction usually generates an SMS confirmation that contains useful details such as amount, date, recipient, and transaction reference. Although this data is readily available in users’ message inboxes, many users still struggle to transform the raw SMS records into meaningful monthly spending insights.

This project addresses that challenge by developing an M-PESA SMS Spending Analyzer that converts semi-structured SMS text into normalized transaction data, categorizes expenses, stores records securely per user, and presents analysis through a dashboard-oriented spending tracker platform. The system reduces manual effort and improves visibility into spending behavior. It is designed for local deployment and practical usability, with an API-first structure that supports both the current web client and a future full mobile app experience.

This chapter introduces the study context, defines the project problem, states objectives and research questions, and presents the significance, scope, limitations, and core modules of the developed system.

## 1.2 Background of the Study

Mobile money has transformed financial activity in East Africa by making digital transactions possible without requiring traditional banking infrastructure for every interaction. In Kenya, M-PESA is used across income levels for daily activities including fare payments, airtime purchase, utility bills, peer-to-peer transfers, and merchant payments. The large transaction volume creates a rich digital trail that can support personal budgeting and decision-making.

Despite this opportunity, many users still rely on memory, handwritten notes, or end-month guesswork to estimate where money was spent. Existing finance tools may require manual entry, external bank integration, or paid subscriptions, which reduce adoption among students and low-to-middle income users. Since M-PESA users already receive transaction messages, a lightweight analyzer that works directly from SMS text can provide immediate value with minimal setup.

Within this context, the present study designed and implemented a practical API-driven system that ingests M-PESA messages, extracts key transaction fields, applies category logic, and visualizes spending behavior through a web interface while also laying the foundation for a mobile spending tracker application. The system also introduces user-scoped authentication, budget limit monitoring, and basic notification generation to strengthen financial awareness and accountability.

## 1.3 Problem Statement

Although M-PESA users receive transaction confirmations for nearly every financial action, the messages remain in unstructured form and are difficult to use for meaningful spending analysis. The following problems were identified:

1. Users lack an automated and reliable way to convert raw M-PESA SMS messages into structured expense records.

2. Spending categories are not consistently tracked, making it difficult to determine where money is being consumed most.

3. Many users do not receive timely warnings when spending approaches or exceeds planned monthly limits.

4. Available alternatives may require expensive integrations, heavy setup, or manual input, which discourages regular use.

These operational gaps reduce the quality of personal financial decisions and limit the ability of users to plan, control, and improve monthly expenditure.

## 1.4 Objectives

### 1.4.1 Main Objective

To design and implement an M-PESA SMS Spending Analyzer that automatically structures transaction messages, categorizes spending, and provides actionable financial insights through a web dashboard and app-ready client architecture.

### 1.4.2 Specific Objectives

(i) To investigate limitations of manual and existing digital spending tracking methods used by M-PESA users.

(ii) To develop a secure and lightweight backend service that parses M-PESA SMS messages and stores normalized transactions per authenticated user.

(iii) To design and implement user-facing clients, beginning with a web dashboard and mobile app foundation, that present transaction history, category summaries, insights, and budget-related indicators.

(iv) To evaluate system functionality and usability through scenario-based testing of parsing, categorization, analytics, and notification workflows.

## 1.5 Research Questions

1. What key limitations do M-PESA users face when tracking spending manually or with existing tools?

2. How can raw M-PESA SMS messages be parsed and normalized into accurate transaction records for analysis?

3. How effective is a lightweight categorization and spending-tracker interface model in improving user visibility of monthly spending patterns?

4. To what extent does budget limit and notification support improve timely financial awareness for users?

## 1.6 Significance of the Study

The study contributes practical and academic value in several ways. First, it demonstrates a low-cost approach to personal finance analytics using already available SMS data, reducing dependency on complex external integrations. Second, it provides an implementable architecture combining FastAPI, SQLAlchemy, static web components, and an emerging mobile client layer, which can be replicated in similar academic and community projects.

For users, the system improves transparency in daily transactions by showing total spending, top spending categories, and behavioral alerts. For software engineering learners, the project offers a complete end-to-end case study involving requirements analysis, secure authentication, data modeling, API design, web/mobile client integration, and deployment planning. For future researchers, the project establishes a baseline for extending categorization logic, applying machine learning models, and integrating broader digital finance channels.

## 1.7 Scope and Limitation of the Study

### Scope

The project scope includes:

1. Parsing selected M-PESA SMS patterns for key fields such as amount, transaction type, recipient, reference, and occurrence time.

2. User registration, login, and token-based authentication for personalized transaction ownership.

3. Storage and retrieval of transactions in SQLite or MySQL/MariaDB through SQLAlchemy.

4. Expense categorization using hybrid rules (keyword fallback plus learned user mapping keys).

5. Web dashboard features for summary, insights, recent transactions, notifications, and budget limit interaction.

6. Prototype mobile app features for API configuration, authentication, and summary retrieval as a foundation for a future spending tracker.

7. Local development and deployment workflow using `uvicorn`, static file hosting, and optional mobile app connectivity.

### Limitations

1. Parsing currently focuses on common message formats and may not cover all telecom message variations.

2. Categorization remains rule-based and may misclassify unusual or ambiguous transaction descriptions.

3. The current mobile app is still a foundation and does not yet include full inbox sync, transaction review, or complete budgeting workflows.

4. Budget planning in the current frontend is partly local-storage based, with gradual backend alignment in progress.

5. Testing concentrated on functional scenarios within local environments and did not include large-scale production load testing.

6. The study focused on software implementation and did not conduct long-duration longitudinal behavioral impact analysis.

## 1.8 Proposed Modules

The system was designed around the following modules:

Module 1: User Registration and Authentication

This module manages account creation, login, and session access control. It validates credentials, hashes passwords with PBKDF2-SHA256, issues bearer tokens, and supports token expiry and invalidation rules for secure API access.

Module 2: SMS Parsing and Normalization

This module processes raw M-PESA SMS messages and extracts structured fields such as amount, reference code, transaction direction, recipient, and timestamp. It standardizes outputs for downstream storage and reporting.

Module 3: Transaction Categorization and Learning

This module assigns transaction categories using a hybrid strategy. It first checks user-specific learned mappings and then applies keyword-based fallback logic. Manual category changes are remembered for future consistency.

Module 4: Summary and Insight Engine

This module computes total spending, category aggregates, average daily spending, and simple warning signals, including high betting share and frequent small transfers.

Module 5: Budget Limit and Notification Management

This module stores monthly budget limits per user, calculates usage thresholds, and generates deduplicated notifications when budget consumption nears or exceeds limits.

Module 6: Web and Mobile Interaction Layer

This module provides user-facing web pages for account access, message ingestion (single and bulk), transactions review, summary visualization, and budget planning/actual comparison, while also exposing the same services to a mobile client foundation that will evolve into a dedicated spending tracker app.

<<<PAGE_BREAK>>>

# CHAPTER TWO

# LITERATURE REVIEW

## 2.1 Introduction

This chapter reviews theoretical and practical work related to mobile money analytics, personal finance management systems, SMS parsing, categorization techniques, and web-based financial dashboards. The review is structured in alignment with the project objectives. It examines relevant studies and technology practices, identifies methodological strengths and weaknesses, and highlights the gap addressed by this project.

The review is limited to sources directly relevant to (a) mobile money and household finance behavior, (b) software architecture for transaction processing, (c) classification strategies for spending categories, and (d) practical implementation frameworks for lightweight web systems.

## 2.2 Review of Objective One: Investigating Existing Limitations

Existing evidence shows mobile money has significant social and economic effects, including improved resilience, financial inclusion, and transaction convenience. However, the everyday management of personal spending behavior remains weak when users lack tools that convert transaction records into understandable insights.

Jack and Suri describe M-PESA as a transformative payment infrastructure, but they also imply that utility depends on surrounding support systems such as record management and decision tools. Suri and Jack further show long-run welfare impacts, reinforcing the need for practical analytics interfaces that help users interpret transaction behavior over time.

Conventional budgeting applications often assume direct bank APIs, extensive manual input, or paid service tiers. In contexts where users rely mainly on mobile money and SMS records, such assumptions create friction. Users frequently postpone recording expenses, resulting in incomplete data and poor monthly planning. Academic and industry discussions on personal finance apps consistently point to usability barriers, data entry burden, and poor continuity as common causes of tool abandonment.

Therefore, the first literature conclusion is that the core gap is not transaction availability but transformation of available transaction traces into low-friction, user-friendly insights.

## 2.3 Review of Objective Two: Developing Parsing and Storage Infrastructure

Information extraction from semi-structured text is a common problem in applied computing. SMS messages are concise but variable in formatting, punctuation, and language style. Rule-based parsing approaches remain useful in constrained domains where message templates are relatively stable, explainability is required, and datasets for machine learning are limited.

In software engineering terms, robust parsing requires explicit patterns, validation, and graceful failure handling. The system in this study applies regular-expression-driven extraction and date parsing utilities to capture amount, timestamp, and transaction attributes. Literature on software reliability emphasizes deterministic handling and defensive validation for user-facing systems, especially when financial data is involved.

On data persistence, established design principles recommend normalized models, integrity constraints, and explicit indexing for query performance. SQLAlchemy's ORM approach aligns with these principles while preserving portability between SQLite and MySQL/MariaDB. This supports educational prototyping and practical migration toward more scalable environments.

Authentication and access control are also central. OWASP guidance highlights password hashing, token management, and least-exposure credential practices as baseline security controls. The project aligns with this literature through PBKDF2 password hashing, token hashing in storage, expiry enforcement, and user-scoped queries across transaction operations.

## 2.4 Review of Objective Three: Categorization and Dashboard Analytics

Spending categorization can be approached by pure rules, statistical learning, or hybrid models. For low-resource and explainability-first applications, hybrid methods are often suitable because they combine deterministic behavior with adaptive user correction. In this project, category assignment first checks learned user mapping keys and then falls back to keyword matching. This design reflects literature that favors human-in-the-loop adaptation for evolving data contexts.

Visualization research emphasizes fast interpretation through concise key performance indicators and clear trend summaries. Personal finance dashboards commonly include total expenditure, top category, category distribution, and warning indicators to reduce cognitive load and support quick reflection. The implemented dashboard follows these practices by presenting total spent, top category, transaction count, category bars, and warnings/highlights.

Insight generation in early-stage systems is typically rule-based. Even simple heuristics (for example, high spending share in risky categories) can offer practical behavioral prompts. Literature on persuasive analytics supports the use of immediate, understandable feedback rather than opaque scoring models in first-generation financial behavior tools.

## 2.5 Review of Objective Four: Evaluation, Deployment, and Usability

Agile and iterative development methodologies are widely recommended for projects where requirements evolve through feedback. For student and small-team projects, short iteration cycles, continuous integration of UI and API changes, and frequent manual verification are practical and effective.

From a deployment perspective, modern lightweight stacks favor API-first backend services and decoupled clients across web and mobile platforms. This approach improves maintainability, simplifies debugging, and allows each layer to scale independently. FastAPI documentation and community practice demonstrate efficient development of typed REST endpoints, while lightweight web and mobile clients support gradual product evolution without tightly coupling presentation logic to backend internals.

Usability literature (including Nielsen's heuristics) highlights visibility of system status, consistency, error prevention, and user control as key factors. The developed interface includes API online indicators, clear action states, informative error messages, and explicit navigation paths, supporting these principles at MVP stage.

## 2.6 Conceptual Framework

Figure 2.1 Conceptual Framework for the M-PESA Spending Analyzer

Independent Variables:

1. Availability of raw M-PESA SMS transaction messages.

2. Parsing and categorization logic quality.

3. User-provided context notes and manual category corrections.

4. Budget limit configuration and threshold policies.

Intervening Variables:

1. Message format variability.

2. User data entry quality.

3. Infrastructure constraints (local vs MySQL deployment).

Dependent Variables:

1. Accuracy and consistency of categorized spending records.

2. Timeliness of budget/spending alerts.

3. User visibility into spending behavior.

4. Improved short-term budgeting decisions.

Narrative relation:

Raw SMS inputs are processed by parser and categorization modules, enhanced by user feedback. Structured outputs feed summaries, insights, and notification logic. These outputs influence user awareness and spending control behavior.

## 2.7 Literature Gap Summary

The literature confirms strong mobile money adoption but limited practical tooling that transforms SMS transaction histories into simple personal financial intelligence for everyday users. Existing systems often over-emphasize integration complexity or require high manual effort.

The gap addressed by this project is therefore a lightweight, explainable, user-scoped analyzer that works from accessible SMS inputs and provides immediate dashboard-level insights without expensive ecosystem dependencies. This gap directly informed the methodology, system architecture, and implementation choices described in the next chapter.

<<<PAGE_BREAK>>>

# CHAPTER THREE

# METHODOLOGY

## 3.1 Introduction

This chapter explains the methodological approach used to design, build, and evaluate the M-PESA SMS Spending Analyzer. It describes research design choices, development methodology, data collection approaches, system analysis and design techniques, and ethical considerations. The purpose is to make the project process transparent and reproducible.

## 3.2 Research Methodology and Research Design

The project used a mixed practical methodology combining qualitative requirement exploration and quantitative system validation.

Qualitative elements included:

1. Observation of common user spending-tracking habits.

2. Problem decomposition based on user pain points (manual tracking burden, delayed insight access, category ambiguity).

3. Design decisions guided by usability and simplicity principles.

Quantitative elements included:

1. Functional pass/fail testing across API endpoints.

2. Validation of parser outputs against expected structured fields.

3. Computation checks for summary totals, insight triggers, and budget threshold logic.

This mixed approach was selected because the project required both human-centered design understanding and measurable verification of software behavior.

## 3.2.1 Development Methodology (Software Project)

The implementation followed an iterative Agile-oriented workflow with short cycles:

Iteration 1: Core API foundation

1. Setup FastAPI application structure.

2. Configure database connection and model initialization.

3. Implement health endpoint and base routing.

Iteration 2: Authentication and user scoping

1. Add registration, login, and current-user endpoints.

2. Implement password hashing and token lifecycle.

3. Enforce user-scoped data access rules.

Iteration 3: Message analysis pipeline

1. Implement single-message parsing and storage.

2. Add bulk ingestion with partial failure handling.

3. Integrate categorization and deduplication by reference.

Iteration 4: Analytics and budget support

1. Implement summary and insights endpoints.

2. Add budget limit update/retrieval endpoints.

3. Generate and manage in-app notifications.

Iteration 5: Frontend integration and stabilization

1. Build auth, spending, dashboard, and budget pages.

2. Integrate API helpers and session handling.

3. Conduct scenario-based testing and bug fixes.

Iteration 6: Mobile app foundation

1. Setup Expo React Native application structure.

2. Add configurable API connection, account authentication, and persisted sessions.

3. Implement an authenticated summary screen to support future spending-tracker expansion.

This development style enabled incremental delivery, early verification, and practical alignment with user-facing needs.

## 3.3 Data Collection Methods Used

Given project timelines and scope, secondary and synthetic operational data approaches were prioritized:

1. Secondary technical data from framework/documentation sources for architecture and implementation decisions.

2. Sample and simulated M-PESA-style SMS texts used to validate parser logic and category mapping behavior.

3. Observational interaction data from local system usage scenarios (for example, repeated ingestion, category correction, budget threshold crossing).

Data collection instruments are provided in Appendix B, including test scenario templates and a brief usability checklist.

## 3.4 System Analysis and Design (SAD)

### 3.4.1 System Analysis

#### Requirements Gathering

Requirements were gathered through:

1. Observation of current spending-recording behavior among target users.

2. Review of project documentation and expected deliverables.

3. Scenario-based analysis of key user journeys (register, ingest, view insights, set budget).

4. Review of existing codebase architecture and data structures.

#### Functional Requirements

Table 3.1 Functional Requirements of the Proposed System

FR1: The system shall register a new user and issue an access token.

FR2: The system shall authenticate existing users and return valid session credentials.

FR3: The system shall parse a single M-PESA SMS into structured transaction fields.

FR4: The system shall process bulk SMS lines and return stored/failed counts.

FR5: The system shall categorize transactions using hybrid rules.

FR6: The system shall store transactions and retrieve them by user and filters.

FR7: The system shall compute summary totals and category aggregates.

FR8: The system shall generate spending insights and warnings.

FR9: The system shall allow users to set and retrieve monthly budget limits.

FR10: The system shall generate and manage user notifications.

FR11: The system shall expose authenticated summary data to both the web client and the prototype mobile app.

#### Non-Functional Requirements

Table 3.2 Non-Functional Requirements of the Proposed System

NFR1: Security - Passwords must be hashed and endpoints protected by bearer tokens.

NFR2: Performance - Common API responses should be fast for normal local workloads.

NFR3: Usability - Interfaces should be simple, consistent, and informative.

NFR4: Reliability - Parsing failures must return clear errors without crashing the service.

NFR5: Maintainability - Modules should be separated by responsibility for easier updates.

NFR6: Portability - Database backend should support SQLite and MySQL/MariaDB.

#### Feasibility Study

Table 3.3 Feasibility Analysis Summary

Technical Feasibility: High. Required technologies (FastAPI, SQLAlchemy, static web frontend, Expo React Native mobile client) are accessible and stable.

Economic Feasibility: High. Tooling is open-source and suitable for low-cost deployment.

Operational Feasibility: High. User workflow is simple and aligned with existing SMS transaction behavior.

Time Feasibility: Moderate to High. MVP achievable within academic semester timeline using iterative scope control.

#### System Modeling

Figure 3.1 High-Level System Architecture

Web frontend + mobile app -> Backend API (FastAPI) -> Database (SQLite/MySQL)

Figure 3.2 Data Flow for Message Analysis

1. User submits SMS message(s).

2. API authenticates request.

3. Parser extracts structured fields.

4. Categorizer assigns category.

5. Transaction is stored per user.

6. Summary/insights/notifications are recalculated.

7. Dashboard retrieves and renders updated analytics.

Figure 3.3 Use-Case Summary Diagram (Narrative)

Actor: Authenticated user.

Use cases: register/login, analyze message, analyze bulk, view transactions, update category, view summary, set budget limit, view notifications, clear transactions.

### 3.4.2 System Design

#### Architectural Design

The system uses a three-layer architecture:

1. Presentation layer: static web pages, JavaScript interaction logic, and a prototype mobile app client.

2. Application layer: REST API endpoints for auth, analysis, budgets, insights, and notifications.

3. Data layer: relational models managed through SQLAlchemy ORM.

This structure supports separation of concerns, easier debugging, and independent evolution of frontend and backend components.

#### Component Design

Major backend component groups include:

1. API endpoint classes (`backend/api/endpoints`).

2. Business logic modules (`parser.py`, `categorizer.py`, `insights.py`, `notifications.py`).

3. Security utilities (`security.py`, `current_user` dependency).

4. Data models and schemas (`models.py`, `schemas.py`).

5. Database setup and migration compatibility (`database.py`).

Frontend components include:

1. Shared API helper and token handling (`app.js`, `init.js`).

2. Auth workflow page (`auth.html`, `auth.js`).

3. Message ingestion page (`spending.html`, `spending.js`).

4. Dashboard analytics page (`index.html`, `dashboard.js`).

5. Budget planning page (`budget.html`, `budget.js`).

Mobile client components include:

1. Shared API client and type definitions (`mobile/src/api`).

2. Authentication context and secure session persistence (`mobile/src/auth`, `mobile/src/storage`).

3. Auth and summary screens (`mobile/src/screens`).

#### Database Design

Core tables used in implementation:

1. `users` and `auth_tokens` for secure identity/session handling.

2. `transactions` for normalized financial events.

3. `category_learning_rules` for adaptive categorization.

4. `user_budget_limits` for threshold monitoring.

5. `notifications` for user alerts.

The schema includes primary keys, unique constraints, and indexes to improve consistency and query performance.

#### User Interface Design

UI design principles applied:

1. Clear navigation across Dashboard, Spending, Budget, and Account pages.

2. Immediate API status indication.

3. Minimal and readable action controls.

4. Error visibility with plain-language feedback.

5. Responsive layout using Bootstrap utility classes for the web client and simplified native controls for the mobile client.

#### Design Validation

Design validation used checklist-driven reviews against requirements:

1. Every functional requirement mapped to at least one endpoint or UI action.

2. Security review for auth enforcement and password/token handling.

3. Data integrity checks for duplicate reference handling and per-user ownership.

4. UX checks for clarity of status messages and action flow continuity.

## 3.5 Research Ethics

Although the project is software-focused, ethical considerations were observed:

1. Privacy: Real personal SMS records should not be committed to source control; synthetic data is preferred in tests.

2. Confidentiality: User transactions are scoped by authenticated user ID and not exposed across accounts.

3. Data minimization: Only required transaction fields are persisted for analysis.

4. Transparency: Users are informed of system limitations, including parser coverage and categorization uncertainty.

5. Security hygiene: Passwords are hashed; tokens are stored as hashes and validated with expiry checks.

These measures align with responsible handling of personal financial information in educational and prototype systems.

<<<PAGE_BREAK>>>

# CHAPTER FOUR

# SYSTEM IMPLEMENTATION AND DEPLOYMENT

## 4.1 Introduction

This chapter presents the practical implementation of the M-PESA SMS Spending Analyzer. It explains the development environment, coding approach, implementation sequence, testing process, and deployment workflow. The chapter transitions from design and methodology into actual solution realization.

## 4.2 Development Environment Setup

Table 4.1 Development Tools and Environment

Programming language: Python 3 (backend), JavaScript ES6 (web frontend), TypeScript (mobile app)

Backend framework: FastAPI

Data layer: SQLAlchemy ORM

Validation layer: Pydantic models

Database options: SQLite (default), MySQL/MariaDB (optional)

Frontend stack: HTML5, CSS3, Bootstrap 5, Vanilla JavaScript, Expo React Native

Server runtime: Uvicorn (ASGI)

Version control: Git

Operating mode: Local development and testing

### Environment Configuration

Backend setup steps:

1. Create virtual environment and install dependencies from `requirements.txt`.

2. Configure database through environment variables (`MPESA_DATABASE_URL` or `MYSQL_*`).

3. Start API server using `uvicorn backend.main:app --reload`.

Web frontend setup steps:

1. Serve static pages from `frontend/src` using Python HTTP server.

2. Access UI via browser and connect to API base URL.

3. Persist authentication token in browser local storage for session continuity.

Mobile setup steps:

1. Install mobile dependencies from `mobile/package.json`.

2. Start Expo in LAN or USB mode and configure the API base URL in-app.

3. Authenticate and retrieve the protected summary screen through the shared backend API.

### Why These Tools Were Selected

1. FastAPI offers rapid API development, type validation, and documentation support.

2. SQLAlchemy provides flexible ORM modeling and backend portability.

3. Static frontend architecture lowers complexity and deployment cost for the browser client.

4. Expo React Native accelerates early mobile delivery while keeping the spending-tracker roadmap aligned with the same backend contracts.

5. Bootstrap accelerates responsive UI construction with minimal custom CSS overhead.

6. SQLite enables quick startup while MySQL/MariaDB supports migration to broader usage contexts.

## 4.3 Implementation Steps

### 4.3.1 Backend Implementation

Step 1: Application bootstrap and routing

A modular API architecture was implemented with endpoint classes registered through a router registry. This improved organization and maintainability.

Step 2: Authentication layer

Endpoints implemented:

1. `POST /auth/register`

2. `POST /auth/login`

3. `GET /auth/me`

Security features implemented:

1. PBKDF2 password hashing.

2. Token issuance and expiry management.

3. Token hash storage for reduced exposure.

4. Authorization dependency to resolve current user.

Step 3: Message analysis endpoints

Endpoints implemented:

1. `POST /analyze` for single-message ingestion.

2. `POST /analyze/bulk` for multi-message ingestion.

The parser extracts amount, timestamp, optional reference, recipient, and transaction type. Deduplication checks are done using user ID and reference code.

Step 4: Categorization and learning

The categorization pipeline applies:

1. User-learned mapping keys.

2. Keyword fallback when learned rules are absent.

Manual category updates are persisted via learned rules for future consistency.

Step 5: Analytics and transaction operations

Endpoints implemented:

1. `GET /transactions`

2. `PUT /transactions/{id}/category`

3. `DELETE /transactions`

4. `GET /summary`

5. `GET /insights`

These endpoints support browsing, correction, cleanup, and interpretation of transaction data.

Step 6: Budget and notification features

Endpoints implemented:

1. `PUT /budget/limit`

2. `GET /budget/limit`

3. `POST /notifications/refresh`

4. `GET /notifications`

5. `PATCH /notifications/{id}/read`

6. `POST /notifications/read-all`

Notification generation includes budget-threshold alerts and insight-driven messages with deduplication keys.

### 4.3.2 Client Implementation

Frontend pages and functions:

1. `auth.html` and `auth.js`: registration and sign-in workflows.

2. `spending.html` and `spending.js`: single/bulk SMS ingestion.

3. `index.html` and `dashboard.js`: KPIs, summaries, transactions, and notifications.

4. `budget.html` and `budget.js`: budget planning and actual-vs-planned comparison.

Shared interaction utilities (`app.js` and `init.js`) provide API communication, token persistence, API health checks, and page access control.

Mobile app functions:

1. `App.tsx`: root application setup and auth-state switching.

2. `AuthScreen.tsx`: API base configuration, register/login, and connection testing.

3. `HomeScreen.tsx`: authenticated profile and spending summary retrieval.

4. Shared client modules: typed API requests, auth context, and local session persistence.

### 4.3.3 Coding Standards and Practices

The following practices were applied:

1. Separation of concerns across API endpoints, business logic, mappers, and models.

2. Type hints and schema validation for safer interface contracts.

3. Clear error responses for invalid requests and unauthorized access.

4. Incremental commits and targeted refactoring for readability.

5. Explainable rule logic in parser/categorizer for easy debugging.

## 4.4 Testing and Quality Assurance

Testing focused on functional correctness and user workflow reliability.

### 4.4.1 Testing Strategy

1. Unit-like behavior checks for parser and categorization scenarios.

2. Endpoint-level validation using controlled request payloads.

3. Integration checks across web/mobile client actions and backend responses.

4. Regression checks after category, budget, and notification updates.

### 4.4.2 Functional Test Cases

Table 4.2 Functional Test Cases and Outcomes

TC1: Register with valid credentials

Input: email, username, password

Expected: token and user object returned

Outcome: Pass

TC2: Login with invalid password

Expected: 401 invalid credentials response

Outcome: Pass

TC3: Analyze single valid SMS message

Expected: parsed transaction stored and returned

Outcome: Pass

TC4: Analyze malformed SMS message

Expected: 400 parse error

Outcome: Pass

TC5: Analyze bulk with mixed valid/invalid lines

Expected: partial success with stored/failed counts

Outcome: Pass

TC6: Retrieve summary after multiple transactions

Expected: correct total and category aggregates

Outcome: Pass

TC7: Update transaction category manually

Expected: category updated and learning rule persisted

Outcome: Pass

TC8: Set budget below current monthly spend

Expected: warning notification generated

Outcome: Pass

TC9: Mark all notifications as read

Expected: unread count reduced to zero

Outcome: Pass

TC10: Access protected endpoint without token

Expected: 401 unauthorized response

Outcome: Pass

### 4.4.3 Quality Assurance Controls

1. Input validation via Pydantic schemas.

2. Database integrity constraints for duplicate protection and valid value ranges.

3. Authentication enforcement on all protected routes.

4. User-scoped query filtering for privacy.

5. Error-first fallback behavior on network/API failures in frontend.

## 4.5 Deployment Plan

The deployment strategy targeted predictable local and small-environment operation.

### Deployment Steps

1. Provision Python runtime and install dependencies.

2. Configure DB backend (SQLite default or MySQL/MariaDB environment variables).

3. Start backend API server.

4. Serve frontend static files.

5. Validate `/` health endpoint and key protected endpoints.

6. Register first user and execute smoke workflow (ingest -> summary -> notifications).

Table 4.3 Deployment and Rollback Checklist

Checklist item 1: Environment variables verified

Checklist item 2: Database initialized and reachable

Checklist item 3: API health endpoint returns success

Checklist item 4: Authentication endpoints working

Checklist item 5: Analyze and summary endpoints working

Checklist item 6: Notification refresh and read-all flows working

Rollback plan: if release fails, stop API process, restore previous `.env` and code revision, and restart known stable version.

## 4.6 Go-Live Plan

For controlled rollout, the following sequence is recommended:

1. Pre-go-live dry run with synthetic messages.

2. Limited user pilot phase.

3. Monitor error logs, parsing failures, and response latency.

4. Collect feedback on category accuracy and dashboard clarity.

5. Apply quick-fix updates and retest.

6. Expand to broader usage once baseline stability is confirmed.

Post-deployment monitoring metrics:

1. API uptime and response success rate.

2. Parser failure ratio.

3. Duplicate reference incidents.

4. Notification creation/read ratios.

5. User-reported categorization correction frequency.

## 4.7 Maintenance and Support

Maintenance activities include:

1. Expanding parser patterns for additional M-PESA message variants.

2. Updating keyword sets and learning rule controls.

3. Reviewing and optimizing slow DB queries.

4. Applying dependency security updates.

5. Improving frontend usability based on user feedback.

Support model:

1. Maintain technical documentation (`README.md`, `docs/api.md`, `docs/database.md`, `docs/architecture.md`).

2. Provide a troubleshooting guide for common API, CORS, and mobile configuration errors.

3. Maintain issue logs and prioritize fixes by user impact.

## 4.8 Chapter Summary

The system was fully implemented as a modular API-driven platform with secure authentication, SMS-to-transaction processing, spending analytics, budget notifications, a complete web client, and a mobile app foundation. The deployment approach is practical for local and educational settings, and the architecture supports iterative enhancement toward production readiness.

<<<PAGE_BREAK>>>

# CHAPTER FIVE

# CONCLUSION, RECOMMENDATIONS AND FUTURE WORK

## 5.1 Summary of the Study

This project set out to solve a practical challenge faced by many M-PESA users: difficulty converting SMS transaction records into useful spending intelligence. The developed M-PESA SMS Spending Analyzer demonstrates that a lightweight API-driven architecture can transform semi-structured messages into categorized, queryable, and visualized financial records across web and app-oriented clients.

The study covered the full project lifecycle from problem definition and literature review to methodology, implementation, testing, and deployment planning. Core objectives were achieved through development of authentication, parsing, categorization, summary analytics, insight generation, budget limit management, and notification modules.

## 5.2 Key Contributions

1. A functioning end-to-end prototype for SMS-based personal spending analysis.

2. A modular architecture balancing simplicity, security, and maintainability.

3. A hybrid categorization strategy that combines explainable rules and user-driven learning.

4. A practical dashboard experience for quick monthly spending awareness.

5. A foundation for future expansion into a fuller mobile spending tracker, richer budgeting, and predictive analytics.

## 5.3 Limitations

1. Coverage of M-PESA message patterns is not exhaustive.

2. Category classification is partly heuristic and may require periodic correction.

3. Long-term behavioral impact on users was not measured through extended field studies.

4. Current deployment and testing emphasize local environments over cloud-scale production conditions.

5. The current mobile client covers authentication and summary access, but not yet full transaction-ingestion and budgeting workflows.

6. Some budget workflows remain partially frontend-local and can be further normalized in backend APIs.

## 5.4 Recommendations

1. Expand parser and normalization rules using a larger real-world anonymized message dataset.

2. Introduce semi-supervised or supervised machine learning for improved categorization precision.

3. Complete the spending tracker roadmap across web and mobile, including transaction review, category correction, and budget workflows.

4. Add comprehensive backend budget CRUD and monthly report export capabilities.

5. Implement role-based administration and audit trails for multi-user or institutional versions.

6. Introduce automated test suites and CI pipelines for stronger release quality controls.

## 5.5 Future Work

Future enhancements may include:

1. OCR support for statement images and integration with additional payment channels.

2. Trend forecasting and anomaly detection for proactive financial coaching.

3. Personalized budget recommendations based on historical spending behavior.

4. A full-featured spending tracker app with inbox synchronization/import, transaction review, budget planning, and notification handling.

5. Offline synchronization support and conflict-aware data refresh between device and backend.

6. Secure cloud deployment with observability dashboards and periodic model updates.

In conclusion, the project proves that practical software engineering can bridge the gap between raw mobile money data and actionable everyday financial insights.

<<<PAGE_BREAK>>>

# REFERENCES

FastAPI. (n.d.). FastAPI documentation. https://fastapi.tiangolo.com/

Jack, W., & Suri, T. (2011). Mobile money: The economics of M-PESA. National Bureau of Economic Research Working Paper No. 16721. https://doi.org/10.3386/w16721

Nielsen, J. (1994). Usability engineering. Morgan Kaufmann.

OWASP Foundation. (n.d.). Password storage cheat sheet. https://cheatsheetseries.owasp.org/

Pressman, R. S., & Maxim, B. R. (2019). Software engineering: A practitioner's approach (9th ed.). McGraw-Hill.

Pydantic. (n.d.). Pydantic documentation. https://docs.pydantic.dev/

Python Software Foundation. (n.d.). Python documentation. https://docs.python.org/3/

Safaricom PLC. (n.d.). M-PESA services. https://www.safaricom.co.ke/personal/m-pesa

Sommerville, I. (2016). Software engineering (10th ed.). Pearson.

SQLAlchemy. (n.d.). SQLAlchemy documentation. https://docs.sqlalchemy.org/

Suri, T., & Jack, W. (2016). The long-run poverty and gender impacts of mobile money. Science, 354(6317), 1288-1292. https://doi.org/10.1126/science.aah5309

Uvicorn. (n.d.). Uvicorn documentation. https://www.uvicorn.org/

<<<PAGE_BREAK>>>

# APPENDICES

## Appendix A: Project Budget

Table A1 Project Budget Estimate

Item: Laptop and accessories

Estimated Cost (KES): 70,000

Item: Internet and bandwidth (4 months)

Estimated Cost (KES): 8,000

Item: Power and utility contribution

Estimated Cost (KES): 4,000

Item: Documentation and printing

Estimated Cost (KES): 3,500

Item: Testing data bundles and misc.

Estimated Cost (KES): 4,500

Total Estimated Budget (KES): 90,000

## Appendix B: Data Collection Tools

1. SMS Parsing Validation Sheet

Fields collected:

- Raw SMS text

- Expected amount

- Expected timestamp

- Expected direction/type

- Expected recipient/reference

- Parsed output

- Pass/Fail and comments

2. Dashboard Usability Checklist

- Is navigation clear between Dashboard, Spending, Budget, and Account pages?

- Are status messages and errors understandable?

- Can users complete message ingestion in less than three steps?

- Are category summaries easy to interpret?

- Are notification messages actionable?

3. Functional Test Log Template

- Test ID

- Scenario description

- Input payload

- Expected output

- Actual output

- Status

- Tester initials and date

## Appendix C: Project Schedule

Table C1 Project Schedule

Week 1-2: Problem analysis, proposal refinement, requirement definition

Week 3-4: Architecture design and database modeling

Week 5-6: Authentication module implementation

Week 7-8: Parser and categorization module implementation

Week 9-10: Dashboard and transaction module integration

Week 11: Budget and notification features

Week 12: Functional testing and bug fixes

Week 13: Documentation and chapter consolidation

Week 14: Final review, formatting, and submission preparation
