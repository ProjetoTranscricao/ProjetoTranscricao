import unittest
import io
from app import app, arquivo_ok

class TesteBasicoCalouro(unittest.TestCase):

    def setUp(self):
        # deixa o app em modo de teste
        app.config["TESTING"] = True
        self.cliente = app.test_client()

    # TESTE 1: página inicial abre
    def test_pagina_inicial(self):
        resposta = self.cliente.get("/")
        self.assertEqual(resposta.status_code, 200)

    # TESTE 2: função que valida extensão do arquivo
    def test_arquivo_ok(self):
        self.assertTrue(arquivo_ok("audio.wav"))
        self.assertTrue(arquivo_ok("som.mp3"))
        self.assertFalse(arquivo_ok("foto.png"))
        self.assertFalse(arquivo_ok("texto.txt"))

    # TESTE 3: rota /transcrever sem enviar arquivo
    def test_transcrever_sem_arquivo(self):
        resposta = self.cliente.post(
            "/transcrever",
            data={"quality": "Simples"},
            content_type="multipart/form-data",
            follow_redirects=True
        )
        # só checa se responde
        self.assertEqual(resposta.status_code, 200)

    # TESTE 4: baixar texto simples
    def test_baixar_texto(self):
        texto = "teste calouro"
        resposta = self.cliente.post(
            "/baixar_texto",
            data={"conteudo_texto": texto}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.mimetype, "text/plain")
        self.assertEqual(resposta.data.decode("utf-8"), texto)


if __name__ == "__main__":
    unittest.main()
