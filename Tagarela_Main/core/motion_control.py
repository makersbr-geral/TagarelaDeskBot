import socket
import time
import numpy as np
from config import *

class MotionController:
    def __init__(self, ip, porta):
        self.ip, self.porta = ip, porta
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pos_x, self.pos_y = float(HOME_X), float(HOME_Y)
        self.last_x, self.last_y = 0, 0
        self.last_send = 0

    def move_to_target(self, coords):
        if coords == (-1, -1): return
        # Define o centro como alvo (ajuste se a resolução do ESP32 for diferente)
        self.mover_para_alvo(coords[0], coords[1], 320, 240)

    def mover_para_alvo(self, tx, ty, cx, cy):
        agora = time.time()
        if (agora - self.last_send) < INTERVALO_COMANDOS: return

        erro_x = tx - cx
        erro_y = ty - cy

        # Velocidade Proporcional
        vx = min(abs(erro_x) * GANHO_VELOCIDADE, VELOCIDADE_MAX_PASSO)
        vy = min(abs(erro_y) * GANHO_VELOCIDADE, VELOCIDADE_MAX_PASSO)

        changed = False
        if abs(erro_x) > DEADZONE:
            self.pos_x += vx if erro_x < 0 else -vx
            changed = True
        if abs(erro_y) > DEADZONE:
            # Inverter o sinal abaixo se o eixo Y estiver invertido
            self.pos_y += vy if erro_y < 0 else -vy
            changed = True

        if changed:
            self._enviar()

    def _enviar(self, forcar=False):
        self.pos_x = np.clip(self.pos_x, SERVO_MIN_X, SERVO_MAX_X)
        self.pos_y = np.clip(self.pos_y, SERVO_MIN_Y, SERVO_MAX_Y)
        
        # Filtro de micro-movimentos
        if abs(self.pos_x - self.last_x) > 1 or abs(self.pos_y - self.last_y) > 1 or forcar:
            try:
                msg = f"{int(self.pos_x)},{int(self.pos_y)}"
                self.sock.sendto(msg.encode(), (self.ip, self.porta))
                self.last_x, self.last_y = self.pos_x, self.pos_y
                self.last_send = time.time()
            except: pass