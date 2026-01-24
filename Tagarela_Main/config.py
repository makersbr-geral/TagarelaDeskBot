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
# MECATRÔNICA / MOTION TUNING (Seus ajustes finos)
# =============================================================================
GANHO_VELOCIDADE = 0.09
VELOCIDADE_MAX_PASSO = 2.14
DEADZONE = 40
INTERVALO_COMANDOS = 0.000001

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
GEMINI_API_KEY = "SUA_CHAVE_API_AQUI"