from datetime import datetime
from utils.db import get_db


def create_notification(user_id, message, notification_type, related_project_id=None):
    """
    Create a notification for a user.
    
    Args:
        user_id: ID of the user to notify
        message: Notification message text
        notification_type: Type of notification (e.g., 'assignment', 'status_update')
        related_project_id: Optional project ID related to the notification
    """
    conn = get_db()
    now = datetime.utcnow().isoformat()
    
    conn.execute("""
        INSERT INTO notifications (user_id, message, type, related_project_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, message, notification_type, related_project_id, now))
    
    conn.commit()
    conn.close()


def notify_reviewers_on_assignment(reviewers, project, contributor):
    """
    Notify assigned reviewers about a new project assignment.
    
    Args:
        reviewers: List of reviewer dicts with 'id' and 'name' keys
        project: Project dict with 'id', 'title' keys
        contributor: Contributor dict with 'name' key
    """
    reviewer_names = ", ".join([r['name'] for r in reviewers])
    message = f"You have been assigned to review '{project['title']}' by {contributor['name']}"
    
    for reviewer in reviewers:
        create_notification(
            user_id=reviewer['id'],
            message=message,
            notification_type='assignment',
            related_project_id=project['id']
        )


def notify_contributor_on_assignment(contributor, project, reviewers):
    """
    Notify contributor that their project has been assigned to reviewers.
    
    Args:
        contributor: Contributor dict with 'id' and 'name' keys
        project: Project dict with 'id' and 'title' keys
        reviewers: List of reviewer dicts with 'name' keys
    """
    reviewer_names = ", ".join([r['name'] for r in reviewers])
    message = f"Your project '{project['title']}' has been assigned to: {reviewer_names}"
    
    create_notification(
        user_id=contributor['id'],
        message=message,
        notification_type='assignment',
        related_project_id=project['id']
    )


def get_user_notifications(user_id, unread_only=False):
    """
    Get notifications for a user.
    
    Args:
        user_id: ID of the user
        unread_only: If True, only get unread notifications
        
    Returns:
        List of notifications
    """
    conn = get_db()
    
    if unread_only:
        notifications = conn.execute("""
            SELECT * FROM notifications
            WHERE user_id = ? AND read_status = 0
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()
    else:
        notifications = conn.execute("""
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()
    
    conn.close()
    return notifications


def mark_as_read(notification_id):
    """Mark a notification as read."""
    conn = get_db()
    conn.execute("""
        UPDATE notifications
        SET read_status = 1
        WHERE id = ?
    """, (notification_id,))
    conn.commit()
    conn.close()


def clear_all_notifications(user_id):
    """Clear all notifications for a user by deleting them."""
    conn = get_db()
    conn.execute("""
        DELETE FROM notifications
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
