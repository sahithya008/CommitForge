from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db
from utils.notifications import get_user_notifications, mark_as_read, clear_all_notifications

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    if "user_id" in session:
        role = session.get("role")
        if role == "Contributor":
            return redirect("/contributor/dashboard")
        elif role == "Reviewer":
            return redirect("/reviewer/dashboard")
        elif role == "Admin":
            return redirect("/admin/dashboard")
    return redirect("/login")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "user_id" in session:
            return redirect("/")
        return render_template("login.html")
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (request.form["email"], request.form["password"])
    ).fetchone()

    if user:
        session["user_id"] = user["id"]
        session["role"] = user["role"]

        if user["role"] == "Contributor":
            return redirect("/contributor/dashboard")
        elif user["role"] == "Reviewer":
            return redirect("/reviewer/dashboard")
        else:
            return redirect("/admin/dashboard")

    return render_template("login.html", error="Account not found. Please register or check your credentials.")

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
            (request.form["name"], request.form["email"], request.form["password"], request.form["role"])
        )
        conn.commit()
        return redirect("/")
    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@auth_bp.route("/delete_account", methods=["POST"])
def delete_account():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session.get("user_id")
    conn = get_db()
    
    try:
        # Handle cascading deletes
        # Delete notifications
        conn.execute("DELETE FROM notifications WHERE user_id=?", (user_id,))
        
        # Delete reviews by this user
        conn.execute("DELETE FROM reviews WHERE reviewer_id=?", (user_id,))
        
        # Delete project_reviewer assignments
        conn.execute("DELETE FROM project_reviewers WHERE reviewer_id=?", (user_id,))
        
        # Set contributor_id to NULL for projects by this user
        conn.execute("UPDATE projects SET contributor_id=NULL WHERE contributor_id=?", (user_id,))
        
        # Set assigned_reviewer_id to NULL for projects assigned to this user
        conn.execute("UPDATE projects SET assigned_reviewer_id=NULL WHERE assigned_reviewer_id=?", (user_id,))
        
        # Delete the user account
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        
        # Clear session
        session.clear()
        
        return redirect("/login")
    except Exception as e:
        conn.rollback()
        # For now, just redirect to login. In production, you'd log the error
        session.clear()
        return redirect("/login")


@auth_bp.route("/notifications")
def notifications():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session.get("user_id")
    notifications = get_user_notifications(user_id)
    unread_count = sum(1 for n in notifications if n['read_status'] == 0)
    
    return render_template("notifications.html", notifications=notifications, unread_count=unread_count)


@auth_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    if "user_id" not in session:
        return redirect("/login")
    
    mark_as_read(notification_id)
    return redirect("/notifications")


@auth_bp.route("/notifications/clear", methods=["POST"])
def clear_notifications():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session.get("user_id")
    clear_all_notifications(user_id)
    return redirect("/notifications")