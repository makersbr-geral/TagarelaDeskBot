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
WEB_SERVER_HOST = '0.0.0.0'
WEB_SERVER_PORT = 5000

# =============================================================================
# MECATRÔNICA / MOTION TUNING (Ajuste Turbo)
# =============================================================================
GANHO_VELOCIDADE = 0.065      # Era 0.09 (Agora ele corre atrás do rosto)
VELOCIDADE_MAX_PASSO = 1.2   # Era 2.14 (Libera o motor para girar rápido)
DEADZONE = 25                # Era 40 (Aumenta a precisão, 40 é muito "folgado")

# Delay TÉCNICO (Não zere isso!)
# 0.02s = 50Hz (Frequência nativa de servos analógicos como MG996R/SG90)
INTERVALO_COMANDOS = 0.02

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
GEMINI_KEY = "AQUI VC COLOCA A CHAVE QUE VC TEM QUE FAZER LÁ NO GOOGLE DEV"