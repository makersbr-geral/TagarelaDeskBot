import os

# =============================================================================
# REDE E CONEXÃO / NETWORK
# =============================================================================
IP_ESP = "192.168.0.214"
PORTA_UDP = 8888
URL_STREAM = f"http://{IP_ESP}:81/stream"
URL_FLASH_ON = f"http://{IP_ESP}/control?var=led_intensity&val=255"
URL_FLASH_OFF = f"http://{IP_ESP}/control?var=led_intensity&val=0"
# Servidor Web (Modo IoT)
# No config.py
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPICO_COMANDO = "tagarela/comando/servos"

# =============================================================================
# MECATRÔNICA / MOTION TUNING (Ajuste Turbo)
# =============================================================================
# MECATRÔNICA
GANHO_VELOCIDADE = 0.05      # Aumentei um pouco para compensar o delay maior
VELOCIDADE_MAX_PASSO = 2.0
DEADZONE = 35                # Aumente para 35 ou 40 (evita correções inúteis que travam o ESP)

# IMPORTANTE: Aumente este tempo!
# 0.1s = 10 comandos por segundo (Alivia o Wi-Fi do ESP32)
INTERVALO_COMANDOS = 0.1

# Limites Físicos dos Servos
SERVO_MIN_X, SERVO_MAX_X = 0, 180
SERVO_MIN_Y, SERVO_MAX_Y = 0, 180
HOME_X, HOME_Y = 90, 90

# Configurações de Varredura (Scan) quando perde o alvo
VELOCIDADE_SCAN = 2.0
LIMITE_PERDA_FRAMES = 300 # Quadros sem alvo antes de iniciar varredura

# =============================================================================
# INTEGRAÇÃO IA (DEV ASSISTANT)
# =============================================================================
# Recomendo usar variáveis de ambiente para segurança, mas pode por direto aqui para teste
GEMINI_KEY = ""