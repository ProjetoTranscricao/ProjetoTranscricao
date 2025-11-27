import os

# diretório base do projeto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# pasta onde os uploads vão ficar (cria se não existir)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "chavesecretars"
)


# caminho opcional para binários do ffmpeg (se tiver)
FFMPEG_BIN = os.path.join(BASE_DIR, "vendor", "bin")
