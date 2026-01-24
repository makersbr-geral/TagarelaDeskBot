import pyautogui
import google.generativeai as genai
from config import GEMINI_API_KEY

class DevAssistant:
    def __init__(self):
        if GEMINI_API_KEY != "SUA_CHAVE_API_AQUI":
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro-vision')
        else:
            self.model = None
            print("AVISO: API Key do Gemini não configurada.")

    def analisar_tela(self, prompt_usuario="O que há de errado neste código?"):
        if not self.model: return "Erro: Configure a API Key no config.py"
        
        print(">>> Tirando Print da Tela...")
        screenshot = pyautogui.screenshot()
        
        print(">>> Enviando para IA...")
        response = self.model.generate_content([prompt_usuario, screenshot])
        
        print(">>> Resposta Recebida.")
        return response.text