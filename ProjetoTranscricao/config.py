import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SECRET_KEY -> use var de ambiente em produção
SECRET_KEY = os.environ.get("SECRET_KEY", "muda_isso_em_producao")
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "app.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Caminho para binários do ffmpeg (se você tiver uma pasta vendor/bin como no desktop)
FFMPEG_BIN = os.path.join(BASE_DIR, "vendor", "bin")
