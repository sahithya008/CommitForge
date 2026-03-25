import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone

ALLOWED_EXTENSIONS = {"zip"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, upload_folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(upload_folder, filename)
        file.save(path)
        return path
    return None

def format_datetime_ist(dt_str=None, format_type="full"):
    """
    Convert UTC datetime to IST and format it.

    Args:
        dt_str: ISO datetime string (UTC) or None for current time
        format_type: "full" (date + time), "date" (date only), "time" (time only)

    Returns:
        Formatted datetime string in IST
    """
    if dt_str:
        # Parse ISO datetime string
        if isinstance(dt_str, str):
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            dt = dt_str
    else:
        dt = datetime.utcnow()

    # Convert to IST (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_dt = dt + ist_offset

    if format_type == "date":
        return ist_dt.strftime("%Y-%m-%d")
    elif format_type == "time":
        return ist_dt.strftime("%H:%M")
    elif format_type == "datetime":
        return ist_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:  # full
        return ist_dt.strftime("%Y-%m-%d at %H:%M")