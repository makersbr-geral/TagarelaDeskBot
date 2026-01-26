import flet as ft
import cv2
import base64
import threading
import time
import socket
import requests
# REMOVI O IMPORT DO PAHO.MQTT QUE ESTAVA AQUI
from config import IP_ESP, PORTA_UDP

NOMES_MODOS = {
    "RASTREIO_ROSTO": "Rastreio de Rosto",
    "VARREDURA": "Busca Automática",
    "RASTREIO_MAO": "Controle por Mão",
    "MODO_DANCA": "Dança",
    "INTELIGENCIA": "Inteligência Artificial",
    "TRAVADO": "Parado"
}

class TagarelaApp:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.running = True
        
        # --- VOLTANDO PARA O SOCKET UDP (O Slide volta a funcionar aqui) ---
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def set_esp_resolution(self, index):
        try:
            requests.get(f"http://{IP_ESP}/control?var=framesize&val={index}", timeout=2)
        except: pass

    def main(self, page: ft.Page):
        page.title = "Tagarella Command Center"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 20
        page.scroll = "adaptive"

        img_feed = ft.Image(src="", width=320, height=240, fit="contain", gapless_playback=True)
        status_text = ft.Text(f"Estado: {self.bot.state}", size=20, weight="bold")

        def change_state(e):
            novo_estado = e.control.data 
            self.bot.state = novo_estado
            nome_falado = NOMES_MODOS.get(novo_estado, "Desconhecido")
            self.bot.falar(f"Modo {nome_falado} ativado.")
            status_text.value = f"Estado: {novo_estado}"
            status_text.color = "red" if novo_estado == "TRAVADO" else "green"
            page.update()

        def on_manual_move(e):
            # Se mexer no slider, trava o robô para manual
            if self.bot.state != "TRAVADO":
                self.bot.state = "TRAVADO"
                status_text.value = "Estado: MANUAL"
                page.update()
            
            # Envia via UDP Local
            cmd = f"{int(slider_x.value)},{int(slider_y.value)}\n"
            try:
                self.sock.sendto(cmd.encode(), (IP_ESP, PORTA_UDP))
            except Exception as ex: 
                print(f"Erro UDP Slider: {ex}")
                
        slider_x = ft.Slider(min=0, max=180, value=90, label="Pan (X)", on_change=on_manual_move)
        slider_y = ft.Slider(min=0, max=180, value=90, label="Tilt (Y)", on_change=on_manual_move)

        controles = ft.Column([
            ft.Text("👁️ Visão Local (Wi-Fi)", size=16),
            ft.Container(content=img_feed, border=ft.border.all(2, "blue"), border_radius=10),
            ft.Row([
                ft.ElevatedButton("VGA", on_click=lambda _: self.set_esp_resolution(6)),
                ft.ElevatedButton("HD", on_click=lambda _: self.set_esp_resolution(9)),
            ], alignment="center"),
            status_text,
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton("Rosto", on_click=change_state, data="RASTREIO_ROSTO"),
                ft.ElevatedButton("Busca", on_click=change_state, data="VARREDURA"),
                ft.ElevatedButton("Mão", on_click=change_state, data="RASTREIO_MAO"),
            ], alignment="center"),
            ft.Row([
                ft.ElevatedButton("Dança", on_click=change_state, data="MODO_DANCA"),
                ft.ElevatedButton("Gemini", on_click=change_state, data="INTELIGENCIA"),
                ft.ElevatedButton("PARAR", on_click=change_state, data="TRAVADO", bgcolor="red"),
            ], alignment="center"),
            ft.Divider(),
            slider_x, slider_y
        ], horizontal_alignment="center")

        page.add(controles)

        def update_stream():
            while self.running:
                try:
                    # Pega o frame processado do bot
                    frame = getattr(self.bot, "frame_atual", None)
                    if frame is not None:
                        # Reduz a qualidade do preview para não travar o app
                        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                        b64_img = base64.b64encode(buffer).decode('utf-8')
                        img_feed.src = f"data:image/jpeg;base64,{b64_img}"
                        img_feed.update()
                    
                    # Atualiza os sliders se o robô estiver se movendo sozinho
                    if self.bot.state != "TRAVADO" and hasattr(self.bot, 'motion'):
                        # Verifica se o valor mudou antes de atualizar para não pesar a UI
                        if abs(slider_x.value - self.bot.motion.pos_x) > 1:
                            slider_x.value = self.bot.motion.pos_x
                            slider_x.update()
                        if abs(slider_y.value - self.bot.motion.pos_y) > 1:
                            slider_y.value = self.bot.motion.pos_y
                            slider_y.update()
                    
                    time.sleep(0.05) # Delay para respirar
                except: 
                    time.sleep(0.1)

        threading.Thread(target=update_stream, daemon=True).start()
        
def iniciar_servidor(bot):
    app = TagarelaApp(bot)
    
    # Pega o IP real da máquina para mostrar o link certo
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    print("\n" + "="*40)
    print(f"🚀 SERVIDOR ONLINE")
    print(f"👉 Link Local: http://{local_ip}:8550")
    print("="*40 + "\n")

    ft.app(target=app.main, view=ft.AppView.WEB_BROWSER, port=8550, host="0.0.0.0")