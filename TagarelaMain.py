import cv2
import socket
import time
import numpy as np
import mediapipe as mp
import math
import requests

# =============================================================================
# 1. CONFIGURAÇÕES & TUNING / SETTINGS & TUNING
# =============================================================================
IP_ESP = "192.168.0.214"
PORTA_UDP = 8888
URL_STREAM = f"http://{IP_ESP}:81/stream"
URL_FLASH_ON = f"http://{IP_ESP}/control?var=led_intensity&val=255"
URL_FLASH_OFF = f"http://{IP_ESP}/control?var=led_intensity&val=0"

# Mecatrônica Tuning / Mechatronics Tuning
GANHO_VELOCIDADE = 0.05
DEADZONE = 20 
INTERVALO_COMANDOS = 0.08 # 80ms delay for Wi-Fi stability / Delay de 80ms para estabilidade
FILTRO_TREMEDEIRA = 2     # Minimum degrees to trigger move / Graus mínimos para mover

HOME_X, HOME_Y = 100, 45
SERVO_MIN_X, SERVO_MAX_X = 0, 180
SERVO_MIN_Y, SERVO_MAX_Y = 0, 180

# Timers / Tempos de interface
TEMPO_TRAVAR_SELECAO = 0.7
TEMPO_CONFIRMAR = 1.0
TEMPO_ACORDAR = 1.5
TEMPO_ABORTAR = 1.0
TEMPO_PINCA_TRIGGER = 0.6
INTERVALO_CHECK_SLEEP = 2.0

# =============================================================================
# 2. INICIALIZAÇÃO / INITIALIZATION
# =============================================================================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, model_complexity=0, min_detection_confidence=0.7)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.6)

# Network Setup / Configuração de Rede (UDP)
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.02) 
    print(f"UDP CONNECTED -> {IP_ESP}:{PORTA_UDP}")
    # Reset servos to home / Reseta servos para posição inicial
    sock.sendto(f"{int(HOME_X)},{int(HOME_Y)}".encode(), (IP_ESP, PORTA_UDP))
except Exception as e:
    print(f"UDP ERROR: {e}")
    sock = None

# =============================================================================
# 3. GLOBAL STATES / ESTADOS GLOBAIS
# =============================================================================
STATE_SLEEP, STATE_MENU, STATE_MISSION = 0, 1, 2
OP_ROSTO, OP_MAO, OP_AUTOSCAN = 1, 2, 3
NOME_OPCOES = {1: "ROSTO", 2: "MAO", 3: "AUTOSCAN"}

estado_atual = STATE_MENU
posicao_atual_x = float(HOME_X)
posicao_atual_y = float(HOME_Y)
ultimo_envio_serial = 0
ultima_pos_enviada_x = 0 
ultima_pos_enviada_y = 0

flash_ligado = False
tempo_inicio_pinca = None
pinca_travada = False
selecao_travada = None
timer_geral = 0
gesto_ativo = False
scan_dir = 1
ultimo_check_sleep = 0
buffer_dedos = []

# =============================================================================
# 4. SYSTEM FUNCTIONS / FUNÇÕES DO SISTEMA
# =============================================================================

def controlar_flash(ligar):
    """Controls ESP32 LED via HTTP / Controla o LED do ESP32 via HTTP"""
    global flash_ligado
    try:
        url = URL_FLASH_ON if ligar else URL_FLASH_OFF
        requests.get(url, timeout=0.05) # Short timeout to avoid lag / Timeout curto para evitar lag
        flash_ligado = ligar
    except:
        pass

def analisar_dedos(hl):
    """Counts open fingers / Conta a quantidade de dedos abertos"""
    dedos = []
    # Thumb / Polegar
    if abs(hl.landmark[4].x - hl.landmark[0].x) > abs(hl.landmark[3].x - hl.landmark[0].x):
        dedos.append(1)
    else: 
        dedos.append(0)
    # Other fingers / Outros dedos
    for p, b in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        dedos.append(1 if hl.landmark[p].y < hl.landmark[b].y else 0)
    return sum(dedos)

def mover_servo(frame, tx, ty, cx, cy, forcar_envio=False):
    """Calculates movement and sends via UDP / Calcula o movimento e envia via UDP"""
    global posicao_atual_x, posicao_atual_y, ultimo_envio_serial
    global ultima_pos_enviada_x, ultima_pos_enviada_y

    # Flow Control / Controle de Fluxo
    if not forcar_envio and (time.time() - ultimo_envio_serial) < INTERVALO_COMANDOS:
        return

    alterou = False
    if tx >= 0:
        erro_x = abs(tx - cx)
        erro_y = abs(ty - cy)
        
        # Proportional Speed / Velocidade Proporcional
        vel_x = min(erro_x * GANHO_VELOCIDADE, 4.0)
        vel_y = min(erro_y * GANHO_VELOCIDADE, 4.0)

        if erro_x > DEADZONE:
            posicao_atual_x += vel_x if tx < cx else -vel_x
            alterou = True
        if erro_y > DEADZONE:
            posicao_atual_y -= vel_y if ty < cy else -vel_y
            alterou = True
    elif forcar_envio: 
        alterou = True

    if alterou:
        posicao_atual_x = np.clip(posicao_atual_x, SERVO_MIN_X, SERVO_MAX_X)
        posicao_atual_y = np.clip(posicao_atual_y, SERVO_MIN_Y, SERVO_MAX_Y)
        
        # Filtering micro-movements / Filtro de tremedeira
        diff_x = abs(posicao_atual_x - ultima_pos_enviada_x)
        diff_y = abs(posicao_atual_y - ultima_pos_enviada_y)
        
        if (diff_x >= FILTRO_TREMEDEIRA or diff_y >= FILTRO_TREMEDEIRA) or forcar_envio:
            if sock:
                try:
                    msg = f"{int(posicao_atual_x)},{int(posicao_atual_y)}"
                    sock.sendto(msg.encode(), (IP_ESP, PORTA_UDP))
                    ultimo_envio_serial = time.time()
                    ultima_pos_enviada_x = posicao_atual_x
                    ultima_pos_enviada_y = posicao_atual_y
                except:
                    pass

# =============================================================================
# 5. MAIN LOOP / LOOP PRINCIPAL
# =============================================================================
cap = cv2.VideoCapture(URL_STREAM)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)

while True:
    ret, frame = cap.read()
    if not ret:
        time.sleep(1)
        continue

    frame = cv2.resize(frame, (640, 480))
    ih, iw = frame.shape[:2]
    cx, cy = iw // 2, ih // 2
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # State: SLEEP / Estado: DORMINDO
    if estado_atual == STATE_SLEEP:
        if (time.time() - ultimo_check_sleep) > INTERVALO_CHECK_SLEEP:
            ultimo_check_sleep = time.time()
            res = hands.process(frame_rgb)
            if res.multi_hand_landmarks:
                for hl in res.multi_hand_landmarks:
                    if analisar_dedos(hl) == 5:
                        estado_atual = STATE_MENU
        cv2.putText(frame, "ZZZ... (5 DEDOS PARA ACORDAR)", (100, 240), 1, 1.2, (255,255,255), 2)
        cv2.imshow("SISTEMA", frame)
        if cv2.waitKey(1) == ord('q'): break
        continue

    # Process Hands / Processamento de Mãos
    res_hands = hands.process(frame_rgb)
    qtd_dedos_estavel = -1
    
    if res_hands.multi_hand_landmarks:
        for hl in res_hands.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)
            qtd_dedos = analisar_dedos(hl)
            buffer_dedos.append(qtd_dedos)
            if len(buffer_dedos) > 5: buffer_dedos.pop(0)
            qtd_dedos_estavel = max(set(buffer_dedos), key=buffer_dedos.count)

    # Menu Logic / Lógica de Menu
    if estado_atual == STATE_MENU:
        cv2.putText(frame, "MENU - SELECIONE COM OS DEDOS", (20, 50), 1, 1.2, (0,255,255), 2)
        if qtd_dedos_estavel in NOME_OPCOES:
            selecao_travada = qtd_dedos_estavel
            estado_atual = STATE_MISSION
        elif qtd_dedos_estavel == 0:
            estado_atual = STATE_SLEEP

    # Mission Logic / Lógica de Missão (Tracking)
    elif estado_atual == STATE_MISSION:
        tx, ty = -1, -1
        
        if selecao_travada == OP_ROSTO:
            res_face = face_mesh.process(frame_rgb)
            if res_face.multi_face_landmarks:
                p = res_face.multi_face_landmarks[0].landmark[4]
                tx, ty = int(p.x * iw), int(p.y * ih)
        
        elif selecao_travada == OP_MAO and res_hands.multi_hand_landmarks:
            p = res_hands.multi_hand_landmarks[0].landmark[8]
            tx, ty = int(p.x * iw), int(p.y * ih)

        if tx != -1:
            mover_servo(frame, tx, ty, cx, cy)
            cv2.circle(frame, (tx, ty), 10, (0, 255, 0), 2)

        if qtd_dedos_estavel == 5: # Back to menu / Volta ao menu
            estado_atual = STATE_MENU
            mover_servo(frame, -1, -1, 0, 0, forcar_envio=True)

    cv2.imshow("SISTEMA", frame)
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()