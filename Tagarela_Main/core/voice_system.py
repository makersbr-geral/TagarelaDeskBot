import os
import logging
from faster_whisper import WhisperModel

# Silencia logs
logging.getLogger("faster_whisper").setLevel(logging.ERROR)

class VoiceSystem:
    def __init__(self):
        print(">>> CARREGANDO MODELO WHISPER 'BASE' (Mais preciso)...")
        # Troquei 'tiny' por 'base'. A diferença de precisão é gigante.
        # Se ficar MUITO lento no seu PC, volte para 'tiny', mas use o prompt abaixo.
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        print(">>> WHISPER PRONTO.")

        # Dicionário de correções (O pulo do gato para mecatrônica)
        self.correcoes = {
            "tá garela": "tagarela",
            "a garela": "tagarela",
            "ta garela": "tagarela",
            "tô ganhando a mão": "tagarela mão",
            "da garela": "tagarela",
            "hóstia": "rosto", # O tiny confunde 'rosto' com 'hóstia' as vezes
            "print": "tela",
            "ver tela": "tela"
        }

    def transcrever(self, caminho_arquivo):
        try:
            if not os.path.exists(caminho_arquivo): return ""

            # --- O SEGREDO ESTÁ AQUI: initial_prompt ---
            # A gente "avisa" a IA quais palavras esperar. Isso enviesa o resultado.
            prompt_contexto = "Tagarela, robô, mecatrônica, rosto, mão, tela, busca, gemini."

            segments, _ = self.model.transcribe(
                caminho_arquivo, 
                language="pt", 
                beam_size=5,
                initial_prompt=prompt_contexto, # Dica para a IA
                vad_filter=True # Remove silêncio e respiração antes de processar
            )
            
            texto_final = ""
            for segment in segments:
                texto_final += segment.text
            
            texto_limpo = texto_final.strip().lower()

            # --- PÓS-PROCESSAMENTO ---
            # Remove pontuação chata que atrapalha o 'if'
            texto_limpo = texto_limpo.replace(".", "").replace(",", "").replace("?", "")

            # Aplica correções manuais forçadas
            for errado, certo in self.correcoes.items():
                if errado in texto_limpo:
                    texto_limpo = texto_limpo.replace(errado, certo)

            return texto_limpo

        except Exception as e:
            print(f"Erro Whisper: {e}")
            return ""