AINDA NÃO IMPLEMENTADO MAS JÁ TESTEI DEU CERTO
from flask import Flask, render_template, Response, request

app = Flask(__name__)
robo_ref = None # Referência ao objeto principal

@app.route('/')
def index():
    return "<h1>Painel de Controle Tagarela</h1><button onclick='fetch(\"/move/left\")'>Esquerda</button>"

@app.route('/move/<direction>')
def move(direction):
    if robo_ref:
        # Envia comando direto para a classe de movimento
        robo_ref.motion.manual_command(direction)
    return "OK"

def start_server(bot_instance):
    global robo_ref
    robo_ref = bot_instance
    app.run(host='0.0.0.0', port=5000)