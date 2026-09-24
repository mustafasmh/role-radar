import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, current_app, flash, g, redirect, render_template, request, url_for
from google import genai


BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "instance" / "applytrack.sqlite3"
STATUSES = ("applied", "interviewing", "offer", "rejected", "withdrawn")
load_dotenv(BASE_DIR / ".env")


def create_app():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to .env before starting ApplyTrack.")

    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=DATABASE,
        GEMINI_API_KEY=gemini_api_key,
        SECRET_KEY="dev-change-this-in-production",
    )

    Path(app.config["DATABASE"]).parent.mkdir(exist_ok=True)
    init_db(app)

    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop("database", None)
        if connection is not None:
            connection.close()

    @app.route("/")
    def dashboard():
        applications = get_db().execute(
            "SELECT * FROM applications ORDER BY applied_date DESC, created_at DESC"
        ).fetchall()
        grouped_applications = {status: [] for status in STATUSES}
        for application in applications:
            grouped_applications.setdefault(application["status"], []).append(application)
        return render_template(
            "index.html",
            grouped_applications=grouped_applications,
            statuses=STATUSES,
        )

    @app.route("/add", methods=("GET", "POST"))
    def add_application():
        if request.method == "POST":
            application = read_application_form()
            error = validate_application(application)
            if error:
                flash(error, "error")
                return render_template("add.html", application=application, statuses=STATUSES), 400

            # in add_application:
            get_db().execute(
                """INSERT INTO applications
                (company, role, status, job_description, job_url, applied_date, notes)
                VALUES (:company, :role, :status, :job_description, :job_url, :applied_date, :notes)""",
                application,
            )

            get_db().commit()
            flash("Application added.", "success")
            return redirect(url_for("dashboard"))

        return render_template("add.html", application={}, statuses=STATUSES)

    @app.route("/edit/<int:application_id>", methods=("GET", "POST"))
    def edit_application(application_id):
        application = get_application(application_id)
        if application is None:
            return "Application not found", 404

        if request.method == "POST":
            updated_application = read_application_form()
            error = validate_application(updated_application)
            if error:
                flash(error, "error")
                return render_template(
                    "edit.html",
                    application=updated_application | {"id": application_id},
                    statuses=STATUSES,
                ), 400

            get_db().execute(
                    """UPDATE applications
                    SET company = :company, role = :role, status = :status, job_description = :job_description,
                        job_url = :job_url, applied_date = :applied_date, notes = :notes,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id""",
                    {**updated_application, "id": application_id},
                )
            
            get_db().commit()
            flash("Application updated.", "success")
            return redirect(url_for("dashboard"))

        return render_template("edit.html", application=application, statuses=STATUSES)

    @app.post("/delete/<int:application_id>")
    def delete_application(application_id):
        get_db().execute("DELETE FROM applications WHERE id = ?", (application_id,))
        get_db().commit()
        flash("Application deleted.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/settings", methods=("GET", "POST"))
    def settings():
        profile = get_profile()
        if request.method == "POST":
            resume_text = request.form.get("resume_text", "").strip()
            get_db().execute(
                "UPDATE profile SET resume_text = ? WHERE id = 1", (resume_text,)
            )
            get_db().commit()
            flash("Resume profile saved.", "success")
            return redirect(url_for("settings"))

        return render_template("settings.html", profile=profile)

    @app.post("/draft/<int:application_id>")
    def draft_application(application_id):
        application = get_application(application_id)
        if application is None:
            return "Application not found", 404

        profile = get_profile()
        resume_text = profile["resume_text"].strip()
        if not resume_text:
            flash("Please fill in your resume in Settings before creating a draft.", "error")
            return redirect(url_for("edit_application", application_id=application_id))

        prompt = f"""Create application materials for this specific job.

Job description:
{application['job_description'] or '(No job description provided)'}

Candidate resume:
{resume_text}

Return exactly two clearly labeled sections:
1. Tailored Cover Letter: a professional draft in 3-4 short paragraphs.
2. Resume Bullet Suggestions: 3-5 concise bullet points tailored to this job.
Use only information supported by the candidate resume. Do not invent experience, employers, or skills.
"""
        try:
            client = genai.Client(api_key=current_app.config["GEMINI_API_KEY"])
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            ai_draft = (response.text or "").strip()
        except Exception:
            flash("Gemini could not create a draft. Please try again.", "error")
            return redirect(url_for("edit_application", application_id=application_id))

        if not ai_draft:
            flash("Gemini returned an empty draft. Please try again.", "error")
            return redirect(url_for("edit_application", application_id=application_id))

        get_db().execute(
            "UPDATE applications SET ai_draft = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (ai_draft, application_id),
        )
        get_db().commit()
        flash("AI draft generated.", "success")
        return redirect(url_for("edit_application", application_id=application_id))

    return app


def get_db():
    if "database" not in g:
        g.database = sqlite3.connect(current_app.config["DATABASE"])
        g.database.row_factory = sqlite3.Row
    return g.database


def init_db(app):
    database_path = app.config["DATABASE"]
    with sqlite3.connect(database_path) as connection:
        schema = (BASE_DIR / "schema.sql").read_text()
        connection.executescript(schema)
        application_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(applications)")
        }
        if "ai_draft" not in application_columns:
            connection.execute("ALTER TABLE applications ADD COLUMN ai_draft TEXT")


def get_application(application_id):
    application = get_db().execute(
        "SELECT * FROM applications WHERE id = ?", (application_id,)
    ).fetchone()
    return dict(application) if application else None


def get_profile():
    profile = get_db().execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return dict(profile)


def read_application_form():
    return {
        "company": request.form.get("company", "").strip(),
        "role": request.form.get("role", "").strip(),
        "status": request.form.get("status", "applied").strip(),
        "job_description": request.form.get("job_description", "").strip(),
        "job_url": request.form.get("job_url", "").strip(),
        "applied_date": request.form.get("applied_date", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }


def validate_application(application):
    if not application["company"] or not application["role"]:
        return "Company and role are required."
    if application["status"] not in STATUSES:
        return "Please choose a valid status."
    return None


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)