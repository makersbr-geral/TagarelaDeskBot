import sys
import os

# Correção de importação
pasta_atual = os.path.dirname(os.path.abspath(__file__))
pasta_principal = os.path.dirname(pasta_atual)
sys.path.append(pasta_principal)

from google import genai
from config import GEMINI_KEY

# Silencia logs
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'

print("-" * 50)
print(">>> LISTANDO TODOS OS MODELOS DISPONÍVEIS NA SUA CONTA...")
print("-" * 50)

try:
    client = genai.Client(api_key=GEMINI_KEY)
    
    # Pega a lista bruta
    todos_modelos = client.models.list()
    
    contador = 0
    for m in todos_modelos:
        # Tenta pegar o nome de várias formas possíveis para garantir
        nome = getattr(m, 'name', None) or getattr(m, 'id', None) or str(m)
        
        # Filtra visualmente só os que parecem ser o Gemini
        if "gemini" in str(nome).lower():
            print(f" [DISPONÍVEL] {nome}")
            contador += 1
            
    if contador == 0:
        print(">>> NENHUM MODELO 'GEMINI' ENCONTRADO.")
        print(">>> Verifique se sua API KEY tem permissão no Google AI Studio.")
    else:
        print(f"\n>>> SUCESSO! Encontrei {contador} modelos.")
        print(">>> ESCOLHA UM DOS NOMES ACIMA (ex: gemini-1.5-flash)")
        print(">>> E atualize a linha 'self.model_id' no seu brain.py")

except Exception as e:
    print(f"\n>>> ERRO CRÍTICO: {e}")

print("-" * 50)