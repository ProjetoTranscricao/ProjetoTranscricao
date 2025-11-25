import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, Response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Transcription
import whisper
import config


ALLOWED_EXTENSIONS = {"wav", "m4a", "mp3", "flac", "ogg", "mpga", "aac"}

app = Flask(__name__)
app.config.from_object("config")
app.secret_key = app.config["SECRET_KEY"]
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB de limite



db.init_app(app)
with app.app_context():
    db.create_all()


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



ffmpeg_bin = config.FFMPEG_BIN
if os.path.isdir(ffmpeg_bin):
    os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ.get("PATH", "")

print("Carregando modelo Whisper (una única vez)...")
MODEL_NAME = os.environ.get("WHISPER_MODEL", "small")
model = whisper.load_model(MODEL_NAME)
print(f"Modelo '{MODEL_NAME}' carregado com sucesso.")



def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """Salva arquivo enviado e retorna caminho"""
    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    saved_name = f"{timestamp}_{filename}"
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
    file.save(saved_path)
    return saved_name, saved_path



@app.route("/")
def index():
    return render_template("index.html", user=current_user)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Usuário e senha são obrigatórios.", "warning")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Usuário já existe.", "danger")
            return redirect(url_for("register"))

        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logado com sucesso.", "success")
            return redirect(url_for("index"))

        flash("Usuário ou senha incorretos.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")




@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("index"))




@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)



@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        flash("Nenhum arquivo enviado.", "warning")
        return redirect(url_for("index"))

    file = request.files["audio"]

    if file.filename == "":
        flash("Selecione um arquivo válido.", "warning")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Tipo de arquivo não permitido.", "danger")
        return redirect(url_for("index"))

    saved_name, saved_path = save_uploaded_file(file)

    try:
        result = model.transcribe(saved_path)
        text = result.get("text", "").strip()
    except Exception as e:
        flash(f"Erro ao transcrever: {e}", "danger")
        return redirect(url_for("index"))

    if current_user.is_authenticated:
        t = Transcription(
            user_id=current_user.id,
            filename=saved_name,
            text=text
        )
        db.session.add(t)
        db.session.commit()

        flash("Transcrição concluída e salva!", "success")
        return redirect(url_for("my_transcriptions"))

    # Convidado → só mostra
    return render_template("transcriptions.html", text=text, filename=saved_name, guest=True)




@app.route("/my")
@login_required
def my_transcriptions():
    trans = Transcription.query.filter_by(
        user_id=current_user.id
    ).order_by(Transcription.created_at.desc()).all()

    return render_template("transcriptions.html", transcriptions=trans, guest=False)



@app.route("/download/<int:tid>")
@login_required
def download_transcription(tid):
    t = Transcription.query.filter_by(id=tid, user_id=current_user.id).first_or_404()
    filename = f"transcription_{t.id}.txt"
    return Response(
        t.text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )



if __name__ == "__main__":
    app.run(debug=True)



