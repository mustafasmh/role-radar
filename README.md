# RoleRadar

> An AI-powered job application tracker that helps you organize your job search and generate tailored resume and cover-letter drafts for each opportunity.

## 📌 Overview

Job hunting can quickly become messy.

Applications end up scattered across LinkedIn, company websites, emails, spreadsheets, and random notes. On top of that, tailoring a resume and cover letter for every position can take a significant amount of time.

**RoleRadar** is a personal job-search management tool designed to solve that problem.

It combines a job application tracker with AI-assisted document tailoring. Users can save job opportunities, track their application status, and generate customized resume and cover-letter drafts based on a job description and their base resume.

The project was built around a simple idea:

> **If I'm going to apply for dozens of jobs anyway, I might as well build the tool I'm going to use to manage them.**

---

## ✨ Features

### 📋 Job Application Tracking

- Add and manage job applications
- Store company, role, location, salary, and job posting details
- Track application status
- Add notes and follow-up information
- View applications in an organized dashboard

### 🤖 AI-Powered Tailoring

- Paste a job description into the application
- Provide a base resume/profile
- Generate an AI-tailored resume draft
- Generate a customized cover-letter draft
- Highlight relevant skills and experience from the candidate's background
- Keep generated content grounded in the information provided by the user

### 📊 Application Dashboard

- View total applications
- Track applications by status
- Monitor interviews and offers
- Quickly identify applications requiring follow-up

### 🔍 Job Details

Each application can contain:

- Job title
- Company
- Location
- Job posting URL
- Job description
- Application date
- Current status
- Salary range
- Notes
- Follow-up date

---

## 🛠️ Tech Stack

**Frontend**

- [Add frontend framework]
- HTML / CSS / JavaScript
- [Add UI library if applicable]

**Backend**

- [Add backend framework]
- REST API

**Database**

- [Add database]

**AI**

- LLM API
- Prompt-based resume and cover-letter generation

**Development**

- Git & GitHub
- VS Code
- GitHub Copilot

## ApplyTrack Flask App

The first working version of the application tracker is a small Flask app using
SQLite directly and Jinja templates. It supports adding, editing, updating the
status of, and deleting job applications from the dashboard.

### Run locally

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Then open `http://127.0.0.1:5000`. The SQLite database is created at
`instance/applytrack.sqlite3` the first time the app starts.

### Project structure

- `app.py` - Flask app factory, database connection helper, and routes
- `schema.sql` - applications table definition
- `templates/` - shared layout, dashboard, and application forms
- `requirements.txt` - Python dependency list

---

## 🏗️ How It Works

```text
                    ┌─────────────────┐
                    │   Job Posting   │
                    └────────┬────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │      RoleRadar      │
                  │                     │
                  │ Job Details         │
                  │        +            │
                  │ Base Resume         │
                  └──────────┬──────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     LLM API     │
                    └────────┬────────┘
                             │
                   ┌─────────┴─────────┐
                   ▼                   ▼
          ┌─────────────────┐ ┌─────────────────┐
          │ Tailored Resume │ │ Cover Letter    │
          │      Draft      │ │      Draft      │
          └─────────────────┘ └─────────────────┘