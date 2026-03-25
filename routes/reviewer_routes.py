from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db
from utils.notifications import get_user_notifications
import os
from datetime import datetime
from utils.helpers import format_datetime_ist

reviewer_bp = Blueprint("reviewer", __name__)


def get_assigned_project(conn, project_id):
    return conn.execute("""
        SELECT p.* FROM projects p
        INNER JOIN project_reviewers pr ON pr.project_id = p.id
        WHERE p.id = ? AND pr.reviewer_id = ?
    """, (project_id, session["user_id"])).fetchone()


def get_reviewer_visible_project(conn, project_id):
    project = get_assigned_project(conn, project_id)
    if project:
        return project

    has_review = conn.execute(
        "SELECT 1 FROM reviews WHERE project_id = ? AND reviewer_id = ? LIMIT 1",
        (project_id, session["user_id"])
    ).fetchone()
    if not has_review:
        return None

    return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

@reviewer_bp.route("/reviewer/dashboard")
def dashboard():
    conn = get_db()
    projects = conn.execute("""
        SELECT DISTINCT p.*, u.name AS contributor_name
        FROM projects p
        LEFT JOIN users u ON u.id = p.contributor_id
        INNER JOIN project_reviewers pr ON pr.project_id = p.id
        WHERE pr.reviewer_id = ? AND p.deleted_at IS NULL
        ORDER BY p.updated_at DESC, p.created_at DESC, p.id DESC
    """, (session["user_id"],)).fetchall()
    
    notifications = get_user_notifications(session["user_id"])
    
    return render_template("reviewer/dashboard.html", projects=projects, notifications=notifications)


@reviewer_bp.route("/reviewer/history")
def history():
    conn = get_db()
    reviews = conn.execute("""
        SELECT r.*, p.title AS project_title, p.updated_at AS project_updated_at
        FROM reviews r
        LEFT JOIN projects p ON r.project_id = p.id
        WHERE r.reviewer_id = ?
        ORDER BY r.id DESC
    """, (session["user_id"],)).fetchall()

    return render_template("reviewer/review_history.html", reviews=reviews)


@reviewer_bp.route("/reviewer/history/clear", methods=["POST"])
def clear_review_history():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM reviews WHERE reviewer_id = ?", (session["user_id"],))
    conn.commit()

    return redirect("/reviewer/history")


@reviewer_bp.route("/reviewer/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    now = datetime.utcnow().isoformat()
    conn = get_db()
    project = get_assigned_project(conn, project_id)
    if not project:
        return redirect("/reviewer/dashboard")

    conn.execute(
        "UPDATE projects SET deleted_at=?, status=?, updated_at=? WHERE id=?",
        (now, "Deleted", now, project_id)
    )
    conn.execute("""
        INSERT INTO project_history
        (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
        SELECT id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, ?, ? FROM projects
        WHERE id=?
    """, ("deleted_by_reviewer", now, project_id))
    conn.commit()
    return redirect("/reviewer/dashboard")


@reviewer_bp.route("/reviewer/project-history/<int:project_id>")
def project_history(project_id):
    conn = get_db()
    project = get_reviewer_visible_project(conn, project_id)
    if not project:
        return redirect("/reviewer/dashboard")

    history_rows = conn.execute(
        "SELECT * FROM project_history WHERE project_id=? ORDER BY recorded_at DESC",
        (project_id,)
    ).fetchall()

    last_modified = history_rows[0] if history_rows else None

    return render_template(
        "reviewer/project_history.html",
        project=project,
        history=history_rows,
        last_modified=last_modified
    )


@reviewer_bp.route("/reviewer/project-history/<int:project_id>/clear", methods=["POST"])
def clear_project_history(project_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    project = get_reviewer_visible_project(conn, project_id)

    if not project:
        return redirect("/reviewer/dashboard")

    conn.execute(
        "DELETE FROM project_history WHERE project_id=?",
        (project_id,)
    )
    conn.commit()

    return redirect(f"/reviewer/project-history/{project_id}")


@reviewer_bp.route("/reviewer/uploads")
def uploads():
    upload_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "uploads")
    upload_dir = os.path.abspath(upload_dir)
    files = []
    if os.path.exists(upload_dir) and os.path.isdir(upload_dir):
        for fname in sorted(os.listdir(upload_dir)):
            if os.path.isfile(os.path.join(upload_dir, fname)):
                files.append(fname)
    return render_template("reviewer/uploads.html", files=files)

@reviewer_bp.route("/review/<int:id>", methods=["GET","POST"])
def review(id):
    conn = get_db()
    project = get_assigned_project(conn, id)
    if not project:
        return redirect("/reviewer/dashboard")

    if request.method == "POST":
        conn.execute("""
        INSERT INTO reviews (project_id, reviewer_id, feedback, decision)
        VALUES (?,?,?,?)
        """, (id, session["user_id"], request.form["feedback"], request.form["decision"]))

        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE projects SET status=?, updated_at=? WHERE id=?",
            (request.form["decision"], now, id)
        )

        conn.execute("""
            INSERT INTO project_history
            (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
            SELECT id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, ?, ? FROM projects
            WHERE id=?
        """, ("reviewed", now, id))

        conn.commit()
        return redirect("/reviewer/dashboard")

    file_info = None
    if project and project["zip_path"]:
        upload_path = project["zip_path"]
        if not os.path.isabs(upload_path):
            upload_path = os.path.join(os.getcwd(), upload_path)
        if os.path.exists(upload_path):
            file_info = {
                "path": project["zip_path"],
                "name": os.path.basename(project["zip_path"]),
                "size": f"{os.path.getsize(upload_path) / 1024:.2f} KB",
                "modified": format_datetime_ist(datetime.utcfromtimestamp(os.path.getmtime(upload_path)), "datetime")
            }
        else:
            file_info = {"path": project["zip_path"], "missing": True}

    return render_template("reviewer/review_project.html", project=project, file_info=file_info)
