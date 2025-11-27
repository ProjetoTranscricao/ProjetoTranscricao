import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, Response
from werkzeug.utils import secure_filename
import whisper

app = Flask(__name__)
app.secret_key = "chave_secreta"

# Pasta onde os áudios serão salvos
app.config["UPLOAD_PASTA"] = os.path.join(os.getcwd(), "uploads")

# Formatos aceitos
FORMATOS = ["mp3", "wav", "m4a", "webm", "mp4", "ogg"]

# Modelos disponíveis
mapa_qualidade = {
    "Simples": "tiny",
    "Media": "base",
    "Precisa": "large"
}

modelo = None
modelo_atual = None


def arquivo_ok(nome):
    return "." in nome and nome.rsplit(".", 1)[1].lower() in FORMATOS


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/transcrever", methods=["POST"])
def transcrever():
    global modelo, modelo_atual

    qualidade = request.form.get("quality", "Simples")
    nome_modelo = mapa_qualidade.get(qualidade, "tiny")

    # Carregar modelo se mudou
    if nome_modelo != modelo_atual or modelo is None:
        try:
            print("Carregando modelo:", nome_modelo)
            modelo = whisper.load_model(nome_modelo)
            modelo_atual = nome_modelo
        except:
            print("Falha ao carregar modelo. Tentando tiny.")
            modelo = whisper.load_model("tiny")
            modelo_atual = "tiny"

    if "audio" not in request.files:
        flash("Nenhum arquivo enviado.", "warning")
        return redirect(url_for("inicio"))

    arq = request.files["audio"]

    if arq.filename == "":
        flash("Nenhum arquivo selecionado.", "warning")
        return redirect(url_for("inicio"))

    if not arquivo_ok(arq.filename):
        flash("Formato de arquivo não aceito.", "danger")
        return redirect(url_for("inicio"))

    nome_limpo = secure_filename(arq.filename)
    tempo = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    nome_salvo = f"{tempo}_{nome_limpo}"

    pasta = app.config["UPLOAD_PASTA"]
    os.makedirs(pasta, exist_ok=True)

    caminho = os.path.join(pasta, nome_salvo)
    arq.save(caminho)

    # Transcrição
    try:
        print("Transcrevendo:", caminho)
        resultado = modelo.transcribe(caminho)
        texto = resultado.get("text", "").strip()
        print("Texto retornado:", repr(texto))
    except Exception as e:
        print("Erro:", e)
        flash("Erro durante a transcrição.", "danger")
        return redirect(url_for("inicio"))

    return render_template(
        "transcriptions.html",
        nome_arquivo=nome_salvo,
        qualidade_usada=qualidade,
        texto_transcrito=texto
    )


@app.route("/baixar_texto", methods=["POST"])
def baixar_texto():
    conteudo = request.form.get("conteudo_texto", "")
    tempo = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    nome = f"transcricao_{tempo}.txt"

    return Response(
        conteudo,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={nome}"}
    )


@app.route("/uploads/<nome>")
def pegar_arquivo(nome):
    pasta = app.config["UPLOAD_PASTA"]
    return send_from_directory(pasta, nome, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
