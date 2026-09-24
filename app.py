import sqlite3
from pathlib import Path

from flask import Flask, current_app, flash, g, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "instance" / "applytrack.sqlite3"
STATUSES = ("applied", "interviewing", "offer", "rejected", "withdrawn")


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=DATABASE,
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

            get_db().execute(
                """INSERT INTO applications
                (company, role, status, job_description, job_url, applied_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                tuple(application.values()),
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
                SET company = ?, role = ?, status = ?, job_description = ?,
                    job_url = ?, applied_date = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (*updated_application.values(), application_id),
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


def get_application(application_id):
    application = get_db().execute(
        "SELECT * FROM applications WHERE id = ?", (application_id,)
    ).fetchone()
    return dict(application) if application else None


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