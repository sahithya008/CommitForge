from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db
from utils.notifications import get_user_notifications
import os
from datetime import datetime, timedelta

contributor_bp = Blueprint("contributor", __name__)

UPLOAD_FOLDER = "uploads"


def is_within_edit_window(created_at):
    if not created_at:
        return False
    try:
        created_dt = datetime.fromisoformat(created_at)
    except Exception:
        return False
    return datetime.utcnow() - created_dt <= timedelta(hours=5)


def format_projects_with_edit(projects):
    formatted = []
    for p in projects:
        item = dict(p)
        item["editable"] = True
        item["time_remaining"] = None
        formatted.append(item)
    return formatted


@contributor_bp.route("/contributor/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "Contributor":
        return redirect("/login")
    
    conn = get_db()
    projects = conn.execute(
        "SELECT * FROM projects WHERE contributor_id=? AND deleted_at IS NULL",
        (session["user_id"],)
    ).fetchall()

    notifications = get_user_notifications(session["user_id"])

    return render_template("contributor/dashboard.html", projects=format_projects_with_edit(projects), notifications=notifications)


@contributor_bp.route("/contributor/deleted")
def deleted_projects():
    conn = get_db()
    projects = conn.execute(
        "SELECT * FROM projects WHERE contributor_id=? AND deleted_at IS NOT NULL",
        (session["user_id"],)
    ).fetchall()

    return render_template("contributor/deleted_projects.html", projects=format_projects_with_edit(projects))


@contributor_bp.route("/contributor/history/<int:project_id>")
def project_history(project_id):
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM project_history WHERE project_id=? AND contributor_id=? ORDER BY recorded_at DESC",
        (project_id, session["user_id"])
    ).fetchall()

    project = conn.execute(
        "SELECT * FROM projects WHERE id=? AND contributor_id=?",
        (project_id, session["user_id"])
    ).fetchone()

    if not project:
        return redirect("/contributor/dashboard")

    return render_template("contributor/project_history.html", project=project, history=history)


@contributor_bp.route("/contributor/project-history/<int:project_id>/clear", methods=["POST"])
def clear_project_history(project_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    project = conn.execute(
        "SELECT id FROM projects WHERE id=? AND contributor_id=?",
        (project_id, session["user_id"])
    ).fetchone()

    if not project:
        return redirect("/contributor/dashboard")

    conn.execute(
        "DELETE FROM project_history WHERE project_id=? AND contributor_id=?",
        (project_id, session["user_id"])
    )
    conn.commit()

    return redirect(f"/contributor/history/{project_id}")


@contributor_bp.route("/contributor/submit", methods=["GET","POST"])
def submit():
    if request.method == "POST":
        project_type = request.form.get("project_type", "").strip()
        github_link = request.form.get("github_link", "").strip()
        zip_file = request.files.get("zip_file")

        if not project_type:
            return render_template("contributor/submit_project.html", error="Please select a Project Type before submitting.")

        if not github_link:
            return render_template("contributor/submit_project.html", error="Please provide GitHub link before submitting.")

        if not zip_file or zip_file.filename == "":
            return render_template("contributor/submit_project.html", error="Please provide a project zip file (.zip) before submitting.")

        if not zip_file.filename.lower().endswith(".zip"):
            return render_template("contributor/submit_project.html", error="Project file must be a .zip archive.")

        path = os.path.join(UPLOAD_FOLDER, zip_file.filename)
        zip_file.save(path)

        category_value = request.form.get("category", "").strip()
        if not category_value:
            return render_template("contributor/submit_project.html", error="Please provide a category for your project.")

        conn = get_db()
        now = datetime.utcnow().isoformat()
        cursor = conn.execute("""
        INSERT INTO projects 
        (contributor_id,title,description,category,demo_link,github_link,zip_path,status,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            session["user_id"],
            request.form.get("title", "").strip(),
            request.form.get("description", "").strip(),
            category_value,
            request.form.get("demo_link", "").strip(),
            github_link,
            path,
            "Submitted",
            now,
            now
        ))

        project_id = cursor.lastrowid
        conn.execute("""
        INSERT INTO project_history 
        (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            project_id,
            session["user_id"],
            request.form.get("title", "").strip(),
            request.form.get("description", "").strip(),
            category_value,
            request.form.get("demo_link", "").strip(),
            github_link,
            path,
            "Submitted",
            "created",
            now
        ))
        conn.commit()
        return redirect("/contributor/dashboard")

    return render_template("contributor/submit_project.html")


@contributor_bp.route("/contributor/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    if "user_id" not in session or session.get("role") != "Contributor":
        return redirect("/login")
    
    now = datetime.utcnow().isoformat()
    conn = get_db()
    
    try:
        conn.execute(
            "UPDATE projects SET deleted_at=?, status=? WHERE id=? AND contributor_id=?",
            (now, "Deleted", project_id, session["user_id"])
        )
        conn.execute("""
        INSERT INTO project_history 
        (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
        SELECT id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, ?, ? FROM projects
        WHERE id=? AND contributor_id=?
        """, ("deleted", now, project_id, session["user_id"]))
        conn.commit()
        return redirect("/contributor/dashboard")
    except Exception as e:
        conn.rollback()
        # For now, just redirect. In production, you'd show an error message
        return redirect("/contributor/dashboard")


@contributor_bp.route("/contributor/restore/<int:project_id>", methods=["POST"])
def restore_project(project_id):
    now = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute(
        "UPDATE projects SET deleted_at=NULL, status=? WHERE id=? AND contributor_id=?",
        ("Submitted", project_id, session["user_id"])
    )
    conn.execute("""
    INSERT INTO project_history 
    (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
    SELECT id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, ?, ? FROM projects
    WHERE id=? AND contributor_id=?
    """, ("restored", now, project_id, session["user_id"]))
    conn.commit()
    return redirect("/contributor/deleted")


@contributor_bp.route("/contributor/deleted/restore_all", methods=["POST"])
def restore_all_deleted_projects():
    if "user_id" not in session:
        return redirect("/login")

    now = datetime.utcnow().isoformat()
    conn = get_db()

    deleted_projects = conn.execute(
        "SELECT id FROM projects WHERE contributor_id=? AND deleted_at IS NOT NULL",
        (session["user_id"],)
    ).fetchall()

    for row in deleted_projects:
        project_id = row["id"]
        conn.execute(
            "UPDATE projects SET deleted_at=NULL, status=? WHERE id=? AND contributor_id=?",
            ("Submitted", project_id, session["user_id"])
        )
        conn.execute("""
            INSERT INTO project_history
            (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
            SELECT id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, ?, ? FROM projects
            WHERE id=? AND contributor_id=?
            """, ("restored_all", now, project_id, session["user_id"]))

    conn.commit()
    return redirect("/contributor/deleted")


@contributor_bp.route("/contributor/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    conn = get_db()
    project = conn.execute(
        "SELECT * FROM projects WHERE id=? AND contributor_id=?",
        (project_id, session["user_id"])
    ).fetchone()

    if not project:
        return redirect("/contributor/dashboard")

    if request.method == "POST":

        github_link = request.form.get("github_link", "").strip()
        new_zip_file = request.files.get("zip_file")

        if not github_link:
            return render_template("contributor/edit_project.html", project=project, error="GitHub link is required.")

        updated_zip_path = project["zip_path"]
        if new_zip_file and new_zip_file.filename != "":
            if not new_zip_file.filename.lower().endswith(".zip"):
                return render_template("contributor/edit_project.html", project=project, error="New file must be a .zip archive.")
            updated_zip_path = os.path.join(UPLOAD_FOLDER, new_zip_file.filename)
            new_zip_file.save(updated_zip_path)

        now = datetime.utcnow().isoformat()
        # preserve the existing state in history before changes
        conn.execute("""
            INSERT INTO project_history 
            (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                project_id,
                session["user_id"],
                project["title"],
                project["description"],
                project["category"],
                project["demo_link"],
                project["github_link"],
                project["zip_path"],
                project["status"],
                "updated",
                now
            ))

        conn.execute(
            "UPDATE projects SET title=?, description=?, category=?, demo_link=?, github_link=?, zip_path=?, updated_at=? WHERE id=? AND contributor_id=?",
            (
                request.form.get("title", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("category", "").strip(),
                request.form.get("demo_link", "").strip(),
                github_link,
                updated_zip_path,
                now,
                project_id,
                session["user_id"]
            )
        )
        conn.commit()
        return redirect("/contributor/dashboard")

    return render_template("contributor/edit_project.html", project=project)
