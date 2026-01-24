import cv2
import time
import threading
import pyttsx3
import pyautogui
import speech_recognition as sr
from core.vision_system import VisionSystem
from core.motion_control import MotionController
from config import *
import numpy as np
# --- ESTADOS DO SISTEMA ---
S_MENU, S_FACE, S_HAND = "MENU", "FACE", "HAND"
S_DEV, S_WORK = "DEV_ASSIST", "PC_OPERATOR"

class TagarelaBot:
    def __init__(self):
        # Inicia no modo FACE (Seguir Rosto)
        self.state = S_FACE
        
        # Sistemas de Hardware e Visão
        self.vision = VisionSystem()
        self.motion = MotionController(IP_ESP, PORTA_UDP)
        
        # Controle de Seleção Visual (Menu)
        self.hand_timer = 0
        self.confirm_timer = 0
        self.current_selection = None
        self.selecao_travada = False 
        
        # Controle de Áudio (Lock para evitar erro de Thread)
        self.voice_lock = threading.Lock()
        
        # Inicia Audição em Background
        threading.Thread(target=self.ouvir_comandos, daemon=True).start()

    def falar(self, texto):
        """Sistema de fala Thread-Safe com Lock"""
        def _speak_task(txt):
            # Tenta adquirir a trava (lock). Se já estiver falando, ignora.
            if self.voice_lock.acquire(blocking=False):
                try:
                    # Inicializa engine local para não travar o loop principal
                    engine_local = pyttsx3.init()
                    
                    # Configura voz para Português (se disponível)
                    voices = engine_local.getProperty('voices')
                    for voice in voices:
                        if "brazil" in voice.name.lower():
                            engine_local.setProperty('voice', voice.id)
                    
                    engine_local.setProperty('rate', 190)
                    engine_local.say(txt)
                    engine_local.runAndWait()
                    
                    engine_local.stop()
                    del engine_local
                except Exception as e:
                    print(f"Erro no módulo de voz: {e}")
                finally:
                    # Libera a trava para a próxima fala
                    self.voice_lock.release()

        threading.Thread(target=_speak_task, args=(texto,), daemon=True).start()

    def ouvir_comandos(self):
        """Loop de escuta de comandos de voz"""
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(">>> SISTEMA DE VOZ ATIVO")
            
            while True:
                try:
                    # Ouve por 4 segundos
                    audio = recognizer.listen(source, phrase_time_limit=4)
                    comando = recognizer.recognize_google(audio, language='pt-BR').lower()
                    print(f">>> VOCÊ DISSE: {comando}")
                    
                    if "tagarela" in comando:
                        # Comandos de Estado
                        novo_estado = None
                        resposta = ""

                        if "rosto" in comando or "face" in comando:
                            novo_estado = S_FACE
                            resposta = "Rastreando rosto."
                        elif "mão" in comando:
                            novo_estado = S_HAND
                            resposta = "Seguindo mão."
                        elif "menu" in comando:
                            novo_estado = S_MENU
                            resposta = "Menu principal."
                        elif "ajuda" in comando or "código" in comando:
                            novo_estado = S_DEV
                            resposta = "Modo desenvolvedor."
                        elif "mouse" in comando or "operador" in comando:
                            novo_estado = S_WORK
                            resposta = "Controle de mouse ativado."
                        elif "diga" in comando or "fale" in comando:
                            self.falar("Sistemas operacionais e prontos, Wagner.")
                            time.sleep(3) # Pausa para não ouvir a si mesmo
                            continue

                        if novo_estado:
                            self.state = novo_estado
                            self.falar(resposta)
                            time.sleep(2) # Pausa para evitar feedback de áudio

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    print(f"Erro no microfone: {e}")

    def run(self):
        self.falar("Tagarela iniciado.")
        print(">>> PRESSIONE 'Q' PARA SAIR <<<")
        
        while True:
            frame, info = self.vision.get_frame()
            if frame is None: continue

            dedos = info['dedos']
            agora = time.time()

            # --- GATILHO PARA VOLTAR AO MENU (5 dedos por 2s) ---
            if dedos == 5:
                if self.hand_timer == 0: self.hand_timer = agora
                elif agora - self.hand_timer > 2.0:
                    if self.state != S_MENU:
                        self.state = S_MENU
                        self.current_selection = None
                        self.selecao_travada = False
                        self.falar("Menu aberto.")
                    self.hand_timer = 0
            else: self.hand_timer = 0

            # --- MÁQUINA DE ESTADOS VISUAL ---
            timer_visual = 0
            
            if self.state == S_MENU:
                # Lógica de Seleção
                if not self.selecao_travada:
                    if dedos in [1, 2, 3, 4]:
                        opcoes = {1: S_FACE, 2: S_HAND, 3: S_DEV, 4: S_WORK}
                        opt = opcoes[dedos]
                        
                        if self.current_selection != opt:
                            self.current_selection = opt
                            self.confirm_timer = agora
                        
                        # Trava a seleção após 1.5s
                        elif agora - self.confirm_timer > 1.5:
                            self.selecao_travada = True
                            self.falar(f"Opção {self.current_selection} selecionada.")

                # Confirmação (Punho Fechado)
                if self.selecao_travada and dedos == 0:
                     self.state = self.current_selection
                     self.falar(f"Iniciando {self.state}")
                     self.selecao_travada = False
                     self.current_selection = None 
                
                if self.current_selection and not self.selecao_travada:
                    timer_visual = agora - self.confirm_timer

            # --- EXECUÇÃO DOS MODOS ---
            elif self.state == S_FACE:
                if info['face_detected']:
                    self.motion.move_to_target(info['face_coords'])

            elif self.state == S_HAND:
                if info['hand_detected']:
                    self.motion.move_to_target(info['hand_coords'])

            elif self.state == S_DEV:
                self.motion.move_to_target((320, 240)) # Centraliza
                # Se fizer gesto de 3 dedos, tira print
                if dedos == 3:
                    self.falar("Capturando tela.")
                    pyautogui.screenshot("print_dev.png")
                    time.sleep(2) # Evita prints múltiplos

            elif self.state == S_WORK:
                if info['hand_detected']:
                    # Controle de Mouse
                    cx, cy = info['hand_coords']
                    sw, sh = pyautogui.size()
                    # Mapeamento de Coordenadas (Câmera -> Tela)
                    mx = np.interp(cx, [0, 640], [0, sw])
                    my = np.interp(cy, [0, 480], [0, sh])
                    
                    pyautogui.moveTo(mx, my, duration=0.1)
                    
                    # Clique com Punho Fechado
                    if dedos == 0:
                        pyautogui.click()
                        time.sleep(0.2)

            # HUD
            hud_state = f"{self.state}"
            hud_sel = f"{self.current_selection}" if self.current_selection else ""
            self.vision.show_hud(frame, hud_state, hud_sel, float(timer_visual))

            if cv2.waitKey(1) == ord('q'): break

        cv2.destroyAllWindows()

if __name__ == "__main__":
    bot = TagarelaBot()
    bot.run()