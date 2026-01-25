import cv2
import mediapipe as mp
import numpy as np
import time
from config import URL_STREAM

class VisionSystem:
    def __init__(self):
        self.cap = cv2.VideoCapture(URL_STREAM)
        self.mp_hands = mp.solutions.hands
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Estilos de desenho (Verde para rosto, Vermelho para mãos)
        self.draw_spec_face = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
        self.draw_spec_hand = self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)

        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

    def contar_dedos(self, hl):
        """Lógica para contar dedos abertos"""
        dedos = []
        # Polegar (ajustado para flip horizontal)
        if abs(hl.landmark[4].x - hl.landmark[0].x) > abs(hl.landmark[3].x - hl.landmark[0].x):
            dedos.append(1)
        else: dedos.append(0)
        # Outros dedos
        for p, b in zip([8, 12, 16, 20], [6, 10, 14, 18]):
            dedos.append(1 if hl.landmark[p].y < hl.landmark[b].y else 0)
        return sum(dedos)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret: return None, None
        
        frame = cv2.flip(frame, 1)
        ih, iw = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        res_face = self.face_mesh.process(rgb)
        res_hands = self.hands.process(rgb)
        
        info = {
            'face_detected': False, 'face_coords': (-1, -1),
            'hand_detected': False, 'hand_coords': (-1, -1),
            'finger_tip_coords': (-1, -1), # Padrão para o robô seguir
            'dedos': -1
        }

        # Processar Rosto
        if res_face.multi_face_landmarks:
            info['face_detected'] = True
            face_lms = res_face.multi_face_landmarks[0]
            p = face_lms.landmark[4] # Ponta do nariz
            info['face_coords'] = (int(p.x * iw), int(p.y * ih))
            self.mp_drawing.draw_landmarks(frame, face_lms, self.mp_face_mesh.FACEMESH_TESSELATION, None, self.draw_spec_face)

        # Processar Mãos
        if res_hands.multi_hand_landmarks:
            info['hand_detected'] = True
            hl = res_hands.multi_hand_landmarks[0]
            info['dedos'] = self.contar_dedos(hl)
            
            # Ponto 8: INDEX_FINGER_TIP (Ponta do dedo indicador)
            p = hl.landmark[8] 
            coords = (int(p.x * iw), int(p.y * ih))
            info['hand_coords'] = coords
            info['finger_tip_coords'] = coords # Garante que a main receba o nome correto
            
            self.mp_drawing.draw_landmarks(frame, hl, self.mp_hands.HAND_CONNECTIONS, self.draw_spec_hand)

        return frame, info

    def show_hud(self, frame, state, sub_state, timer):
        """Exibe o HUD tecnológico na tela"""
        if frame is None: return
        h, w = frame.shape[:2]
        
        # Barra de status superior
        cv2.rectangle(frame, (0, 0), (w, 50), (0, 0, 0), -1)
        cv2.putText(frame, f"STATUS: {state}", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if sub_state and sub_state != "None":
            cv2.putText(frame, f"ESCOLHA: {sub_state} ({timer:.1f}s)", (int(w*0.45), 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow("Tagarela Robot - Visao Computacional", frame)