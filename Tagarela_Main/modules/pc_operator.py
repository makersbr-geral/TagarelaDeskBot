AQUI ATÉ QUE FUNCIONOU, REVER MAIS TARDE
import pyautogui
import time

def manter_ativo():
    # Move o mouse levemente para não deixar o PC bloquear
    pyautogui.moveRel(10, 0)
    time.sleep(0.5)
    pyautogui.moveRel(-10, 0)

def executar_macro_login():
    # Exemplo: Abrir VS Code
    pyautogui.press('win')
    pyautogui.write('vscode')
    pyautogui.press('enter')