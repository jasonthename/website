import sqlite3
from datetime import datetime

from flask import Blueprint, render_template, request, g, redirect, url_for

from app.constants import DATABASE
from app.forms import PostForm
from app.limiter import limiter

msg_bp = Blueprint("msg", __name__, subdomain="msg")


def get_db():
    """
    Get the current database connection, or create a new one if one doesn't exist
    """

    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    return db


@msg_bp.route("/", methods=["GET", "POST"])
@limiter.limit("3 per minute", methods=["POST"])
def index():
    """
    The main 'msg' index, where a visitor may view or post a message.
    """
    db = get_db()
    cur = db.cursor()
    form = PostForm()

    # We only want to add to the database if the entry passed validation checks.
    if form.validate_on_submit():

        data = (
            request.form["name"].strip() or "Anonymous",
            request.form["message"],
            str(datetime.now()),
        )

        cur.execute("INSERT INTO messages(name, message, created) VALUES (?, ?, ?)", data)
        db.commit()
        
        return redirect(url_for("msg.index"))

    # TODO: Use a better way of getting the messages because this is relatively slow.
    cur.execute("SELECT * FROM messages")
    messages = cur.fetchall()

    return render_template('msg/index.html', form=form, posts=reversed(messages), admin=False)


@msg_bp.route("/admin", methods=["GET", "POST"])
def admin():
    db = get_db()
    cur = db.cursor()
    
    if request.method == "POST":
        try:
            target = request.form["delete"]
        except KeyError:
            pass
        else:
            cur.execute("DELETE FROM messages WHERE id = ?", (target,))
            db.commit()

    cur.execute("SELECT * FROM messages")
    messages = cur.fetchall()
    return render_template('msg/title.html', posts=reversed(messages), admin=True)


@msg_bp.route("/message-<int:msg_id>")
def message(msg_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))

    msg = cur.fetchone()
    
    if msg is not None:
        return render_template('msg/message.html', msg=msg)
    else:
        return redirect(url_for("msg.index"))
  