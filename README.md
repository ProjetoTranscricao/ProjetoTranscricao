# Projeto de Transcrição de Áudio (Flask + Whisper)

Aplicação simples desenvolvida em **Python** usando **Flask** e o modelo **Whisper** para converter áudios em texto.  
O objetivo é servir como ferramenta prática para estudos e pequenos projetos envolvendo IA e transcrição automática.

---

## Funcionalidades

- Upload de arquivos de áudio  
- Três níveis de qualidade de transcrição: **Simples**, **Média** e **Precisa**  
- Uso do modelo Whisper para gerar o texto  
- Download do texto transcrito  
- Download do arquivo de áudio enviado  
- Interface feita com **HTML + CSS**  
- Sistema de mensagens (*flash messages*) para avisos, erros e confirmações  

---

## Estrutura do Projeto

O projeto é organizado da seguinte forma:

- **app.py** — código principal do Flask (rotas e lógica)  
- **config.py** — configurações de upload e caminho do FFmpeg  
- **requirements.txt** — dependências do Python  
- **/templates** — arquivos HTML (`base.html`, `index.html`, `transcricao.html`)  
- **/static** — arquivo `styles.css` com o estilo da interface  
- **/uploads** — pasta onde ficam temporariamente os áudios enviados  

---

## Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt

### 2. Instalar FFmpeg

O Whisper precisa do FFmpeg para processar os áudios.

Windows: baixe o FFmpeg e coloque a pasta bin dentro de vendor/bin

Linux:
```bash
sudo apt install ffmpeg

### 3. Executar o servidor Flask
```bash
python app.py

### 4. Acessar no navegador
http://127.0.0.1:5000


### Testes

Os testes utilizam a biblioteca unittest.
Para executar:
```bash
python -m unittest -v

🧠 Tecnologias Utilizadas

• Python
• Flask
• Whisper
• Torch
• FFmpeg
• HTML / CSS
