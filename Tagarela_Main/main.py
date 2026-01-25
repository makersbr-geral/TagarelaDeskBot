import os
import re
import asyncio
import edge_tts
import pygame
import time
import threading
import speech_recognition as sr
import numpy as np
import cv2
import pyautogui # Restaurado: Para controle do PC futuramente

# Silencia logs técnicos
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

from core.vision_system import VisionSystem
from core.motion_control import MotionController
from config import *

# --- ESTADOS DO SISTEMA ---
# Modos de Rastreio
S_FACE = "FACE"
S_HAND = "HAND"
S_BUSCA = "BUSCA" # Novo: Modo Varredura

# Modos de Ação
S_HOME = "HOME"
S_DANCA = "DANCA" # Novo: Modo Dança
S_GEMINI = "GEMINI"
S_TRAVA = "TRAVA"
S_WORK = "PC_OPERATOR" # Restaurado

class TagarelaBot:
    def __init__(self):
        print(">>> INICIALIZANDO TAGARELA DESKBOT (Full Version)...")
        
        # Estado Inicial
        self.state = S_TRAVA
        
        # Módulos Core
        self.vision = VisionSystem()
        self.motion = MotionController(IP_ESP, PORTA_UDP)
        self.brain = None 
        
        # Configuração de Áudio Neural
        #self.voz_neural = "pt-BR-AntonioNeural"
        self.arquivo_audio = "fala_tagarela.mp3"
        pygame.mixer.init()
        #self.voz_neural = "pt-BR-FranciscaNeural"
        self.voz_neural = "pt-BR-ThalitaNeural"
        #self.voz_neural= "pt-BR-ValerioNeural"
        # Sincronização e Trava de Voz
        self.voice_lock = threading.Lock()
        self.esta_falando = False  

        # Variáveis de Controle de Movimento (Dança/Busca)
        self.scan_direction = 1
        self.scan_pos = 90
        self.scan_pos_y = 90

        threading.Thread(target=self.ouvir_comandos, daemon=True).start()

    def limpar_texto(self, texto):
        if not texto: return ""
        return re.sub(r'[\*\_\#\`]', '', texto).strip()

    async def _gerar_e_falar(self, texto):
        """Tarefa assíncrona para gerar e tocar o áudio"""
        try:
            communicate = edge_tts.Communicate(texto, self.voz_neural, rate="+20%")
            await communicate.save(self.arquivo_audio)
            
            pygame.mixer.music.load(self.arquivo_audio)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.001)
                
            pygame.mixer.music.unload()
        except Exception as e:
            print(f">>> Erro no motor de voz neural: {e}")

    def falar(self, texto):
        """Interface para chamar a fala assíncrona"""
        def _thread_falar(txt):
            if self.voice_lock.acquire(blocking=False):
                self.esta_falando = True 
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._gerar_e_falar(txt))
                    loop.close()
                finally:
                    #time.sleep(0.01)
                    self.esta_falando = False
                    self.voice_lock.release()
        
        threading.Thread(target=_thread_falar, args=(texto,), daemon=True).start()

    def ouvir_comandos(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("\n>>> MICROFONE PRONTO - ESCUTANDO...")
            
            while True:
                if self.esta_falando:
                   # time.sleep(0.001)
                    continue
                try:
                    audio = recognizer.listen(source) # Tempo curto para comandos rápidos
                    if self.esta_falando: continue
            
                    comando = recognizer.recognize_google(audio, language='pt-BR').lower()
                    print(f"\n[VOZ]: {comando}")

                    # --- 1. COMANDOS GLOBAIS (Funcionam sempre) ---
                    if "tagarela" in comando:
                        # Mapeamento Solicitado:
                        if any(x in comando for x in ["parar", "trava", "cancelar","inferno"]):
                            self.state = S_TRAVA
                            self.falar("Travando posição.",)

                        elif "rosto" in comando or "face" in comando:
                            self.state = S_FACE
                            self.falar("Rastreando rosto.")

                        elif "mão" in comando:
                            self.state = S_HAND
                            self.falar("Rastreando mão.")
                        
                        elif "home" in comando:
                            self.state = S_HOME
                            self.falar("Indo para home.")
                            
                        elif any(x in comando for x in ["diga", "fale", "repete","repita","fala"]):
                            self.falar(comando)

                        elif "dança" in comando:
                            self.state = S_DANCA
                            self.falar("Modo dança ativado!")

                        elif "busca" in comando or "procurar" in comando:
                            self.state = S_BUSCA
                            self.falar("Iniciando varredura por alvos.")

                        elif any(x in comando for x in ["gemini", "inteligência", "ia","gemin"]):
                            if self.brain is None:
                                from core.brain import TagarelaBrain
                                self.brain = TagarelaBrain()
                            self.state = S_GEMINI
                            self.falar("Modo Gemini online.")

                    # --- 2. LÓGICA ESPECÍFICA DO MODO GEMINI ---
                    elif self.state == S_GEMINI:
                        if any(x in comando for x in ["sair", "cancelar"]):
                            self.state = S_TRAVA
                            self.falar("Saindo do Gemini.")
                        else:
                            if self.brain:
                                print(f">>> IA PROCESSANDO: '{comando}'")
                                resposta = self.brain.perguntar(comando)
                                if "ERRO" in resposta:
                                    self.falar("Erro de conexão.")
                                else:
                                    self.falar(self.limpar_texto(resposta))
                        continue

                except Exception:
                    pass
                    
    def executar_danca(self):
        """Movimento simples de balanço para 'Dança'"""
        # Sequência: Esquerda -> Direita -> Centro
        targets = [(45, 90), (135, 90), (45, 90), (135, 90), (90, 90)]
        for x, y in targets:
            self.motion.move_to_target((0,0)) # Hack: Se move_to_target aceitasse angulos diretos seria melhor,
                                              # mas assumindo que ele recebe coords de tela,
                                              # vamos deixar o loop principal cuidar se for movimento complexo.
                                              # Como não tenho acesso ao seu motion_control.py agora,
                                              # vou simular mudando o estado visualmente ou deixar parado se não tiver a função.
            pass
        # Nota: Idealmente, adicione um método 'dancar()' no seu MotionController

    def executar_busca(self):
        """Logica de varredura (Scan)"""
        # Move o eixo X de um lado para o outro
        self.scan_pos += (2 * self.scan_direction) # Velocidade do scan
        if self.scan_pos > 160: self.scan_direction = -1
        if self.scan_pos < 20: self.scan_direction = 1
        
        # Envia comando direto (Assumindo que sua classe Motion converte coords)
        # Se MotionController espera Coords de Tela (640x480), convertemos:
        # 0 graus ~= 0px, 180 graus ~= 640px
        target_x = int((self.scan_pos / 180) * 640)
        self.motion.move_to_target((target_x, 240))

    def run(self):
        self.falar("Sistema corrigido e pronto.")
        
        while True:
            frame, info = self.vision.get_frame()
            if frame is None: continue

            # --- AUTO-DETECÇÃO DE RESOLUÇÃO ---
            h, w = frame.shape[:2] 
            resolucao_frame = (w, h)

            # HUD Ajustado Automaticamente
            cv2.circle(frame, (w//2, h//2), 5, (0, 255, 255), -1) 

            # --- MÁQUINA DE ESTADOS DINÂMICA ---
            if self.state == S_FACE:
                if info['face_detected']: 
                    self.motion.move_to_target(info['face_coords'], resolucao_frame)

            elif self.state == S_HAND:
                # --- FALTAVA ISSO AQUI ---
                if info.get('hand_detected'):
                    coords = info.get('finger_tip_coords') or info.get('hand_coords')
                    self.motion.move_to_target(coords, resolucao_frame)

            elif self.state == S_BUSCA:
                self.scan_pos += (5 * self.scan_direction)
                # Bate e volta na largura real (w)
                if self.scan_pos > (w - 20): self.scan_direction = -1
                if self.scan_pos < 20: self.scan_direction = 1
                
                # Se achar algo, muda de estado e avisa
                if info['face_detected']:
                    self.state = S_FACE
                    self.falar("Rosto encontrado.")
                elif info.get('hand_detected'):
                    self.state = S_HAND
                    self.falar("Mão encontrada.")
                else:
                    # Continua varrendo no horizonte (h//2)
                    self.motion.move_to_target((self.scan_pos, h//2), resolucao_frame)

            elif self.state == S_DANCA:
                # --- MOVIMENTO X ---
                self.scan_pos += (15 * self.scan_direction)
                if self.scan_pos > (w - 50): self.scan_direction = -1
                if self.scan_pos < 50: self.scan_direction = 1

                # --- MOVIMENTO Y (Adicionado) ---
                # Usei 10 na velocidade para dessincronizar do X e não fazer apenas uma diagonal
                self.scan_pos += (15 * self.scan_direction)
                if self.scan_pos > (h - 50): self.scan_direction = -1
                if self.scan_pos < 50: self.scan_direction = 1

                # Envia a tupla com (X, Y) atualizados
                self.motion.move_to_target((self.scan_pos, self.scan_pos_y), resolucao_frame)

            elif self.state == S_HOME:
                # --- E ISSO AQUI ---
                self.motion.reset_para_90()
                #time.sleep(1) # Dá tempo de chegar
                self.state = S_TRAVA # Trava depois de centralizar

            elif self.state in [S_TRAVA, S_GEMINI, S_WORK]:
                # Trava no centro da tela (olhando para frente)
                self.motion.move_to_target((w//2, h//2), resolucao_frame)

            self.vision.show_hud(frame, self.state, "", 0)
            if cv2.waitKey(1) == ord('q'): break
        cv2.destroyAllWindows()

if __name__ == "__main__":
    bot = TagarelaBot()
    bot.run()