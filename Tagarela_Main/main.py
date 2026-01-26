import os
import re
import asyncio
import edge_tts
import pygame
import threading
import speech_recognition as sr
import cv2
import io
import time

# --- IMPORTS LIMPOS ---
# Importa TUDO do config (incluindo MQTT_BROKER e MQTT_PORT)
from config import * 
from core.voice_system import VoiceSystem
from core.vision_system import VisionSystem
from core.motion_control import MotionController
from modules.web_server import iniciar_servidor

# Limpa logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# --- ESTADOS ---
S_TRAVA = "TRAVADO"
S_FACE = "RASTREIO_ROSTO"
S_HAND = "RASTREIO_MAO"
S_BUSCA = "VARREDURA"
S_GEMINI = "INTELIGENCIA"
S_DANCA = "MODO_DANCA"
S_HOME = "POSICAO_HOME"

class TagarelaBot:
    def __init__(self):
        print(">>> INICIALIZANDO TAGARELA V3 (Web Only)...")
        self.frame_atual = None
        self.state = S_TRAVA
        
        # Hardware
        # No __init__ do TagarelaBot dentro do main.py
        # Hardware
        self.vision = VisionSystem()
        
        # REMOVA O PRINT DO BROKER E DEIXE APENAS:
        self.motion = MotionController(IP_ESP, PORTA_UDP)
        self.brain = None
        
        # Áudio
        pygame.mixer.init()
        self.voz_neural = "pt-BR-ThalitaNeural"
        self.voice_lock = threading.Lock()
        self.esta_falando = False
        
        # Ouvido
        self.ears = VoiceSystem()
        
        # Variáveis de Movimento
        self.scan_pos = 90
        self.scan_pos_y = 90
        self.scan_direction = 1

        threading.Thread(target=self.ouvir_comandos, daemon=True).start()

    # ... (MANTENHA O RESTO DAS SUAS FUNÇÕES: _falar_async, falar, ouvir_comandos, etc.) ...
    # ... (NÃO PRECISA ALTERAR NADA DAQUI PARA BAIXO NO SEU CÓDIGO ORIGINAL) ...
    # Apenas certifique-se de que as funções _falar_async, falar, ouvir_comandos,
    # processar_comando e run continuam identicas ao que você já tinha.

    async def _falar_async(self, texto):
        if not texto: return
        try:
            comm = edge_tts.Communicate(texto, self.voz_neural, rate="+20%")
            byte_stream = io.BytesIO()
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    byte_stream.write(chunk["data"])
            byte_stream.seek(0)
            if byte_stream.getbuffer().nbytes > 0:
                pygame.mixer.music.load(byte_stream, "mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.05)
        except Exception as e: print(f"Erro Áudio: {e}")

    def falar(self, texto):
        if self.esta_falando: return 
        def run():
            with self.voice_lock:
                self.esta_falando = True
                asyncio.run(self._falar_async(texto))
                self.esta_falando = False
        threading.Thread(target=run, daemon=True).start()

    def ouvir_comandos(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        temp_audio_file = "comando_temp.wav"
        print(">>> SISTEMA AUDITIVO ONLINE")
        while True:
            if self.esta_falando: 
                time.sleep(0.5); continue
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
                with open(temp_audio_file, "wb") as f: f.write(audio.get_wav_data())
                comando = self.ears.transcrever(temp_audio_file)
                if comando:
                    print(f"[VOCÊ]: {comando}")
                    self.processar_comando(comando)
            except: pass

    def processar_comando(self, comando):
        cmd = comando.lower()
        if "tagarela" in cmd:
            if any(p in cmd for p in ["parar", "trava", "chega"]):
                self.state = S_TRAVA; self.falar("Parado.")
            elif "rosto" in cmd or "face" in cmd:
                self.state = S_FACE; self.falar("Rastreando rosto.")
            elif "mão" in cmd:
                self.state = S_HAND; self.falar("Rastreando mão.")
            elif any(p in cmd for p in ["busca", "procurar", "varredura"]):
                self.state = S_BUSCA; self.falar("Iniciando varredura.")
            elif "dança" in cmd:
                self.state = S_DANCA; self.falar("Solta o som.")
            elif "home" in cmd:
                self.state = S_HOME; self.falar("Posição inicial.")
            elif any(p in cmd for p in ["inteligência", "gemini", "conversa"]):
                self.state = S_GEMINI; self.falar("Pode perguntar.")
        elif self.state == S_GEMINI:
            if any(p in cmd for p in ["sair", "cancelar", "parar"]):
                self.state = S_TRAVA; self.falar("Conversa encerrada.")
            else:
                if self.brain is None:
                    from core.brain import TagarelaBrain
                    self.brain = TagarelaBrain()
                resp = self.brain.perguntar(cmd)
                self.falar(re.sub(r'[*_#]', '', resp))

    def run(self):
        self.falar("Sistema online.")
        while True:
            frame, info = self.vision.get_frame(self.state)
            self.frame_atual = frame
            if frame is None: time.sleep(0.1); continue
            h, w = frame.shape[:2]
            res = (w, h)

            if self.state == S_FACE and info.get('face_detected'):
                self.motion.move_to_target(info['face_coords'], res)
            elif self.state == S_HAND and info.get('hand_detected'):
                self.motion.move_to_target(info['hand_coords'], res)
            elif self.state == S_BUSCA:
                self.scan_pos += (5 * self.scan_direction)
                if self.scan_pos > w-40 or self.scan_pos < 40: self.scan_direction *= -1
                if info.get('face_detected'):
                    self.state = S_FACE; self.falar("Encontrei.")
                else: self.motion.move_to_target((self.scan_pos, h//2), res)
            elif self.state == S_DANCA:
                self.scan_pos += (20 * self.scan_direction)
                if self.scan_pos > (w - 50): self.scan_direction = -1
                if self.scan_pos < 50: self.scan_direction = 1
                self.scan_pos_y += (15 * self.scan_direction)
                if self.scan_pos_y > (h - 50): self.scan_direction = -1
                if self.scan_pos_y < 50: self.scan_direction = 1
                self.motion.move_to_target((self.scan_pos, self.scan_pos_y), res)
            elif self.state == S_HOME:
                self.motion.move_to_target((w//2, h//2), res); self.state = S_TRAVA
            elif self.state in [S_TRAVA, S_GEMINI]:
                self.motion.move_to_target((w//2, h//2), res)
            
            if cv2.waitKey(1) == ord('q'): break
        cv2.destroyAllWindows()

if __name__ == "__main__":
    bot = TagarelaBot()
    robot_thread = threading.Thread(target=bot.run, daemon=True)
    robot_thread.start()
    print(">>> INICIANDO SERVIDOR WEB (FLET)...")
    try: iniciar_servidor(bot)
    except KeyboardInterrupt: print("Desligando...")