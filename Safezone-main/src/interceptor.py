from flask import session, redirect, url_for, flash, request

def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap
