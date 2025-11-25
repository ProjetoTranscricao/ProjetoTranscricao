import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Transcription
import whisper
import config

ALLOWED_EXTENSIONS = {"wav", "m4a", "mp3", "flac", "ogg", "mpga", "aac"}

# cria app
app = Flask(__name__)
app.config.from_object("config")
app.secret_key = app.config["SECRET_KEY"]
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

# db
db.init_app(app)

with app.app_context():
    db.create_all()

# login manager
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# configura PATH do ffmpeg se existir
ffmpeg_bin = config.FFMPEG_BIN
if os.path.isdir(ffmpeg_bin):
    os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ.get("PATH", "")

# Carrega modelo Whisper uma vez (escolha: "tiny","base","small","medium","large")
# Use "tiny" ou "small" para testes locais — large exige muito.
print("Carregando modelo Whisper (pode demorar)...")
MODEL_NAME = os.environ.get("WHISPER_MODEL", "tiny")
model = whisper.load_model(MODEL_NAME)
print(f"Modelo {MODEL_NAME} carregado.")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS




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
        u = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        flash("Conta criada. Faça login.", "success")
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
        flash("Usuário ou senha inválidos.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Desconectado.", "info")
    return redirect(url_for("index"))

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # somente para debug/local; em produção sirva via nginx
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    # Se usuário não selecionado, faz como convidado — o resultado NÃO será salvo.
    if "audio" not in request.files:
        flash("Nenhum arquivo enviado.", "warning")
        return redirect(url_for("index"))

    f = request.files["audio"]
    if f.filename == "":
        flash("Nenhum arquivo selecionado.", "warning")
        return redirect(url_for("index"))
    if not allowed_file(f.filename):
        flash("Tipo de arquivo não permitido.", "danger")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    saved_name = f"{timestamp}_{filename}"
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
    f.save(saved_path)

    try:
        # roda transcrição (pode levar)
        # Para áudio longos, considere streaming ou jobs em background (celery). Aqui fazemos direto.
        result = model.transcribe(saved_path)
        texto = result.get("text", "").strip()
    except Exception as e:
        flash(f"Erro na transcrição: {e}", "danger")
        # remove arquivo salvo se quiser
        # os.remove(saved_path)
        return redirect(url_for("index"))

    if current_user.is_authenticated:
        t = Transcription(user_id=current_user.id, filename=saved_name, text=texto)
        db.session.add(t)
        db.session.commit()
        flash("Transcrição salva no seu perfil.", "success")
        return redirect(url_for("my_transcriptions"))
    else:
        # modo convidado: não salva no DB, só mostra o texto e link pra download
        return render_template("transcriptions.html", text=texto, filename=saved_name, guest=True)

@app.route("/my")
@login_required
def my_transcriptions():
    ts = Transcription.query.filter_by(user_id=current_user.id).order_by(Transcription.created_at.desc()).all()
    return render_template("transcriptions.html", transcriptions=ts, user=current_user, guest=False)

# rota pra baixar como arquivo txt
@app.route("/download/<int:tid>")
@login_required
def download_transcription(tid):
    t = Transcription.query.filter_by(id=tid, user_id=current_user.id).first_or_404()
    # retorna texto como attachment simples
    from flask import Response
    filename = f"transcription_{t.id}.txt"
    return Response(
        t.text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

if __name__ == "__main__":
    app.run(debug=True)
