from flask import Flask, render_template, redirect, url_for, request, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "study_secret_key"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            filename TEXT,
            category TEXT,
            uploader TEXT
        )
    """)

    # Tạo admin mặc định
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                  ("admin","123456","admin"))

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================
@app.route("/")
def index():
    return render_template("index.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                      (username,password,"user"))
            conn.commit()
        except:
            conn.close()
            return "Tài khoản đã tồn tại!"
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username,password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["role"] = user[3]
            return redirect(url_for("index"))
        else:
            return "Sai tài khoản hoặc mật khẩu!"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ================= VIEW DOCUMENTS =================
@app.route("/documents/<category>")
def documents(category):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE category=?",(category,))
    docs = c.fetchall()
    conn.close()
    return render_template("documents.html",docs=docs,category=category)

# ================= DOWNLOAD =================
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ================= ADMIN UPLOAD =================
@app.route("/upload_admin", methods=["GET","POST"])
def upload_admin():
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]
        file = request.files["file"]

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO documents(title,filename,category,uploader) VALUES(?,?,?,?)",
                  (title,filename,category,"admin"))
        conn.commit()
        conn.close()

        return redirect(url_for("documents",category=category))

    return render_template("upload_admin.html")

# ================= USER UPLOAD =================
@app.route("/upload_user", methods=["GET","POST"])
def upload_user():
    if session.get("role") != "user":
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form["title"]
        file = request.files["file"]

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))

        conn = sqlite3.connect("database.db")
        c.execute("INSERT INTO documents(title,filename,category,uploader) VALUES(?,?,?,?)",
                  (title,filename,"donggop",session["user"]))
        conn.commit()
        conn.close()

        return redirect(url_for("documents",category="donggop"))

    return render_template("upload_user.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)