from google import genai
from config import GEMINI_KEY
import re

class TagarelaBrain:
    def __init__(self):
        # Cliente oficial do novo SDK
        self.client = genai.Client(api_key=GEMINI_KEY)
        
        # --- O NOME EXATO DA SUA LISTA ---
        # Usamos o 2.5 Flash por ser rápido e estar disponível (sem erro 404)
       # Mude de "models/gemini-1.5-flash" para:
        self.model_id = "gemini-2.5-flash"
        
        self.instruction = (
            "Você é o Tagarela, um robô desktop que ajuda em suas tarefas, meu criador o Wagner, é um cara solitario, por isso ele inventou este deskbot"
            "Responda de forma direta, curta e objetiva (máximo 2 frases). "
            "Não use asteriscos, negritos ou formatação markdown."
        )

    def perguntar(self, mensagem):
        try:
            print("-" * 30)
            print(f">>> ENVIANDO PARA ({self.model_id}): {mensagem}")

            # Chama o modelo usando o nome validado
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"{self.instruction}\n\nPergunta: {mensagem}"
            )
            
            if not response or not response.text:
                return "ERRO: Resposta vazia da IA."

            # Limpa o texto para o motor de voz não falar símbolos
            texto_limpo = re.sub(r'[\*\_\#\`]', '', response.text).strip()
            
            print(f">>> RESPOSTA: {texto_limpo}")
            print("-" * 30)
            return texto_limpo

        except Exception as e:
            erro_str = str(e)
            print(f">>> FALHA NA CONEXÃO: {erro_str}")
            
            # Tratamento para os erros que vimos nos gráficos
            if "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str:
                return "ERRO_COTA"
            if "503" in erro_str or "overloaded" in erro_str:
                return "ERRO_SOBRECARGA"
            
            return "ERRO_TECNICO"