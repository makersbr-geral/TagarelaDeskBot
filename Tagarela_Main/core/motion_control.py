import socket
import time
import threading
import numpy as np
from config import *

class MotionController:
    def __init__(self, ip, porta):
        self.ip = ip
        self.porta = porta
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Posições atuais
        self.pos_x = float(HOME_X)
        self.pos_y = float(HOME_Y)
        
        # Posições Alvo
        self.target_x = float(HOME_X)
        self.target_y = float(HOME_Y)
        
        self.running = True
        
        # Thread de envio (evita travar o vídeo)
        self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self.sender_thread.start()

    # --- AQUI ESTÁ A FUNÇÃO QUE ESTAVA FALTANDO ---
    def sync_manual_position(self, x, y):
        """Sincroniza a posição quando o usuário mexe no slider manual"""
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)

    def move_to_target(self, coords, resolucao_atual=(480, 320)):
        if coords == (-1, -1) or coords is None: return
        largura, altura = resolucao_atual
        centro_x, centro_y = largura // 2, altura // 2
        
        self._calcular_proximo_passo(coords[0], coords[1], centro_x, centro_y)

    def _calcular_proximo_passo(self, tx, ty, cx, cy):
        erro_x = tx - cx
        erro_y = ty - cy
        
        # Ganho suavizado
        vx = min(abs(erro_x) * 0.05, VELOCIDADE_MAX_PASSO)
        vy = min(abs(erro_y) * 0.05, VELOCIDADE_MAX_PASSO)

        if abs(erro_x) > DEADZONE:
            self.target_x = self.pos_x - (vx if erro_x < 0 else -vx)
            
        if abs(erro_y) > DEADZONE:
            self.target_y = self.pos_y - (vy if erro_y < 0 else -vy)

        self.target_x = np.clip(self.target_x, SERVO_MIN_X, SERVO_MAX_X)
        self.target_y = np.clip(self.target_y, SERVO_MIN_Y, SERVO_MAX_Y)

    def _sender_loop(self):
        last_sent_x = -1
        last_sent_y = -1
        
        while self.running:
            # Atualiza posição interna
            self.pos_x = self.target_x
            self.pos_y = self.target_y
            
            # Só envia se mudou mais que 1 grau
            if abs(self.pos_x - last_sent_x) > 1 or abs(self.pos_y - last_sent_y) > 1:
                try:
                    msg = f"{int(self.pos_x)},{int(self.pos_y)}\n"
                    self.sock.sendto(msg.encode(), (self.ip, self.porta))
                    last_sent_x = self.pos_x
                    last_sent_y = self.pos_y
                except:
                    pass
            
            # Delay de 100ms para proteger o ESP32 de travamento
            time.sleep(0.1)