from datetime import datetime

from flask import Blueprint, redirect, render_template, request, flash, session
from utils.db import get_db
from utils.notifications import notify_reviewers_on_assignment, notify_contributor_on_assignment, get_user_notifications

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
def dashboard():
    if session.get("role") != "Admin":
        return redirect("/login")
    
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    reviewers = conn.execute(
        "SELECT id, name, email FROM users WHERE role = 'Reviewer' ORDER BY name, email"
    ).fetchall()
    projects = conn.execute("""
        SELECT
            p.*,
            c.name AS contributor_name,
            c.email AS contributor_email
        FROM projects p
        LEFT JOIN users c ON c.id = p.contributor_id
        ORDER BY COALESCE(p.updated_at, p.created_at, p.id) DESC
    """).fetchall()

    # Fetch assigned reviewers for each project
    projects_with_reviewers = []
    for project in projects:
        assigned_reviewers = conn.execute("""
            SELECT u.id, u.name, u.email
            FROM project_reviewers pr
            JOIN users u ON u.id = pr.reviewer_id
            WHERE pr.project_id = ?
            ORDER BY u.name
        """, (project['id'],)).fetchall()
        project_dict = dict(project)
        project_dict['assigned_reviewers'] = assigned_reviewers
        project_dict['assigned_reviewer_ids'] = [r['id'] for r in assigned_reviewers]
        projects_with_reviewers.append(project_dict)

    notifications = get_user_notifications(session.get("user_id", 0))

    return render_template(
        "admin/dashboard.html",
        users=users,
        reviewers=reviewers,
        projects=projects_with_reviewers,
        status_options=[
            "Submitted",
            "Assigned",
            "In Review",
            "Revision Requested",
            "Approved",
            "Rejected",
            "Deleted",
        ],
        notifications=notifications,
    )


@admin_bp.route("/admin/projects/<int:project_id>/assignment", methods=["POST"])
def update_project_assignment(project_id):
    if session.get("role") != "Admin":
        return redirect("/login")
    
    conn = get_db()
    now = datetime.utcnow().isoformat()
    
    # Get selected reviewer IDs from the multi-select form
    selected_reviewer_ids = request.form.getlist("reviewer_ids")
    selected_reviewer_ids = [int(rid) for rid in selected_reviewer_ids if rid.strip()]

    current_project = conn.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()
    if not current_project:
        return redirect("/admin/dashboard")

    # Validate all selected reviewers exist
    for reviewer_id in selected_reviewer_ids:
        reviewer = conn.execute(
            "SELECT id, name FROM users WHERE id = ? AND role = 'Reviewer'",
            (reviewer_id,)
        ).fetchone()
        if not reviewer:
            return redirect("/admin/dashboard")

    # Clear existing assignments
    conn.execute("DELETE FROM project_reviewers WHERE project_id = ?", (project_id,))
    
    # Add new assignments
    action_parts = []
    assigned_reviewers = []
    for reviewer_id in selected_reviewer_ids:
        conn.execute("""
            INSERT INTO project_reviewers (project_id, reviewer_id, assigned_at)
            VALUES (?, ?, ?)
        """, (project_id, reviewer_id, now))
        
        reviewer = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (reviewer_id,)
        ).fetchone()
        if reviewer:
            reviewer_name = reviewer['name']
            assigned_reviewers.append({'id': reviewer['id'], 'name': reviewer_name})
            action_parts.append(reviewer_name)
    
    # Update project status
    next_status = current_project["status"]
    if selected_reviewer_ids and current_project["status"] in (None, "", "Submitted"):
        next_status = "Assigned"
    elif not selected_reviewer_ids and current_project["status"] == "Assigned":
        next_status = "Submitted"

    action = f"assigned_to_{', '.join(action_parts)}" if action_parts else "assignment_cleared"
    
    conn.execute(
        """
        UPDATE projects
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        (next_status, now, project_id)
    )
    conn.execute("""
        INSERT INTO project_history
        (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
        SELECT id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, ?, ?
        FROM projects
        WHERE id = ?
    """, (action, now, project_id))
    conn.commit()
    
    # Send notifications to reviewers and contributor
    if assigned_reviewers:
        # Get project and contributor details for notification
        project = conn.execute("SELECT id, title FROM projects WHERE id = ?", (project_id,)).fetchone()
        contributor_id = current_project['contributor_id']
        if contributor_id:
            contributor = conn.execute("SELECT id, name FROM users WHERE id = ?", (contributor_id,)).fetchone()
            if contributor:
                # Notify reviewers
                notify_reviewers_on_assignment(assigned_reviewers, project, contributor)
                # Notify contributor
                notify_contributor_on_assignment(contributor, project, assigned_reviewers)
    
    return redirect("/admin/dashboard")


@admin_bp.route("/admin/projects/<int:project_id>/status", methods=["POST"])
def update_project_status(project_id):
    if session.get("role") != "Admin":
        return redirect("/login")
    
    conn = get_db()
    now = datetime.utcnow().isoformat()
    status = request.form.get("status", "").strip() or "Submitted"

    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        return redirect("/admin/dashboard")

    conn.execute(
        "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
        (status, now, project_id)
    )
    conn.execute("""
        INSERT INTO project_history
        (project_id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, action, recorded_at)
        SELECT id, contributor_id, title, description, category, demo_link, github_link, zip_path, status, ?, ?
        FROM projects
        WHERE id = ?
    """, ("status_updated_by_admin", now, project_id))
    conn.commit()
    return redirect("/admin/dashboard")


@admin_bp.route("/admin/users/add", methods=["GET", "POST"])
def add_user():
    if session.get("role") != "Admin":
        return redirect("/login")
    
    if request.method == "GET":
        return render_template("admin/add_user.html")
    
    conn = get_db()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "Contributor").strip()
    
    if not name or not email or not password:
        return render_template("admin/add_user.html", error="All fields are required")
    
    if role not in ["Contributor", "Reviewer", "Admin"]:
        return render_template("admin/add_user.html", error="Invalid role")
    
    try:
        conn.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, password, role)
        )
        conn.commit()
        return redirect("/admin/dashboard")
    except Exception as e:
        return render_template("admin/add_user.html", error="Email already exists or database error")


@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    if session.get("role") != "Admin":
        return redirect("/login")
    
    if user_id == session.get("user_id"):
        flash("You cannot delete your own account.", "error")
        return redirect("/admin/dashboard")
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return redirect("/admin/dashboard")
    
    # Delete user and related data
    conn.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM reviews WHERE reviewer_id = ?", (user_id,))
    conn.execute("DELETE FROM project_reviewers WHERE reviewer_id = ?", (user_id,))
    conn.execute("DELETE FROM project_history WHERE contributor_id = ?", (user_id,))
    # Set contributor_id to NULL for projects by this user, or delete them?
    # For simplicity, set to NULL to avoid deleting projects
    conn.execute("UPDATE projects SET contributor_id = NULL WHERE contributor_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    
    flash(f"User {user['name']} has been deleted.", "success")
    return redirect("/admin/dashboard")


@admin_bp.route("/admin/projects/manage", methods=["GET"])
def manage_projects():
    if session.get("role") != "Admin":
        return redirect("/login")
    
    conn = get_db()
    projects = conn.execute("""
        SELECT
            p.*,
            c.name AS contributor_name,
            c.email AS contributor_email
        FROM projects p
        LEFT JOIN users c ON c.id = p.contributor_id
        ORDER BY COALESCE(p.updated_at, p.created_at, p.id) DESC
    """).fetchall()
    
    return render_template("admin/manage_projects.html", projects=projects)


@admin_bp.route("/admin/projects/clear_all", methods=["POST"])
def clear_all_projects():
    if session.get("role") != "Admin":
        return redirect("/login")
    
    conn = get_db()
    
    try:
        # Delete all project-related data
        # Delete notifications related to projects
        conn.execute("UPDATE notifications SET related_project_id = NULL WHERE related_project_id IS NOT NULL")
        
        # Delete project history
        conn.execute("DELETE FROM project_history")
        
        # Delete reviews
        conn.execute("DELETE FROM reviews")
        
        # Delete project reviewer assignments
        conn.execute("DELETE FROM project_reviewers")
        
        # Delete projects
        conn.execute("DELETE FROM projects")
        
        conn.commit()
        
        flash("All projects and their history have been cleared.", "success")
        return redirect("/admin/dashboard")
    except Exception as e:
        conn.rollback()
        flash("An error occurred while clearing projects.", "error")
        return redirect("/admin/dashboard")


@admin_bp.route("/admin/projects/<int:project_id>/clear", methods=["POST"])
def clear_project(project_id):
    if session.get("role") != "Admin":
        return redirect("/login")

    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        return redirect("/admin/dashboard")

    conn.execute("DELETE FROM project_history WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM reviews WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM project_reviewers WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()

    flash(f"Project #{project_id} and its related history were cleared.", "success")
    return redirect("/admin/dashboard")
