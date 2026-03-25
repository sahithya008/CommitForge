from flask import session, redirect

def login_required(role=None):
    def wrapper(func):
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect("/")

            if role and session.get("role") != role:
                return redirect("/")

            return func(*args, **kwargs)
        decorated.__name__ = func.__name__
        return decorated
    return wrapper