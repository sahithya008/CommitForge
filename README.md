# CommitForge - Project Submission and Review Portal

[![Live Demo](https://img.shields.io/badge/Live-Demo-purple?style=flat-square)](https://commitforge.onrender.com)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat-square\&logo=flask\&logoColor=white)](https://flask.palletsprojects.com/)

**CommitForge** is a web-based Project Submission and Review Portal designed to digitalize and streamline the end-to-end lifecycle of academic and organizational project management.

Traditional submission processes relying on email threads, shared folders, and paperwork are prone to disorganization and a lack of transparency. CommitForge replaces these fragmented workflows with a structured, role-driven platform.

---

## 🚀 Key Features

* **Role-Based Access Control (RBAC):** Distinct interfaces and permissions for Contributors, Reviewers, and Administrators.
* **Project Submissions & File Handling:** Contributors can submit project details along with optional ZIP file attachments securely sanitized using Werkzeug.
* **Multi-Reviewer Assignment:** Administrators can assign one or multiple reviewers to any project submission.
* **Structured Reviews & Status Tracking:** Reviewers can evaluate projects and assign statuses such as Approved, Revision Requested, or Rejected.
* **Automated In-App Notifications:** Instant alerts are triggered whenever a project status changes or a review or assignment occurs.
* **Immutable Audit Trail:** A comprehensive history log tracking every action taken on a project with exact timestamps and user attribution.

---

## 🛠️ Technology Stack

| Component         | Technologies                                            |
| ----------------- | ------------------------------------------------------- |
| Frontend          | HTML5, CSS3, JavaScript (ES6), Jinja2 Templating Engine |
| Backend           | Python, Flask, Flask-Login, Werkzeug                    |
| Database & ORM    | SQLite, SQLAlchemy                                      |
| Production Server | Gunicorn                                                |
| Deployment        | Render                                                  |

---

## 👥 Project Team

Developed as a real-time research project by the Department of Computer Science and Engineering (AI & ML) at **Sumathi Reddy Institute of Technology for Women** during the academic year 2025–2026.

### Team Members

| Name                | Hall Ticket Number |
| ------------------- | ------------------ |
| Nerella Shivani     | `246Y1A66B7`       |
| Mattewada Aishwarya | `246Y1A66A0`       |
| Manmadi Sahithya    | `246Y1A6694`       |
| Parikirala Manusri  | `246Y1A66C3`       |

**Under the Guidance of:** Mrs. D. Shravani (Assistant Professor, CSM)

---

## 📦 How to Run Locally

Follow these steps to set up and run CommitForge on your local machine.

### Prerequisites

Make sure you have the following installed:

* Python 3.10 or higher
* Git
* A modern web browser

### Step 1: Clone the Repository

```bash
git clone https://github.com/sahithya008/CommitForge.git
cd CommitForge
```

### Step 2: Set Up a Virtual Environment

It is recommended to create an isolated virtual environment to manage project dependencies.

**Windows (Command Prompt / PowerShell):**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

Install all required Python packages using pip:

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

Start the Flask development server by executing the application entry point:

```bash
python app.py
```

> **Note:** When the application starts, it will automatically initialize the SQLite database through `init_db()` if it does not already exist.

### Step 5: Access the Portal

Open your preferred web browser and navigate to:

http://127.0.0.1:5000

---

## 🎯 Getting Started

Once the application is running:

1. Click **Sign Up** to register a new account.
2. Choose your role (Contributor, Reviewer, or Admin) from the dropdown menu to explore the different role-based permissions.
3. Log in with your credentials to start submitting, reviewing, and managing projects.

---

## 🌐 Live Demo

Try the deployed application here:

**[CommitForge – Live Demo](https://commitforge.onrender.com)**

---

*CommitForge — Bringing structure, transparency, and accountability to project submissions and reviews.*
