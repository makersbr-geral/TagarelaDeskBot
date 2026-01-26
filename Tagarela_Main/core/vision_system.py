import cv2
import mediapipe as mp
import numpy as np
import time
from config import URL_STREAM

class VisionSystem:
    def __init__(self):
        self.cap = cv2.VideoCapture(URL_STREAM)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.mp_hands = mp.solutions.hands
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.draw_spec_face = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
        self.draw_spec_hand = self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)

        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
        self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

    def get_frame(self, state):
        # --- MUDANÇA: Blindagem contra queda de WiFi ---
        try:
            ret, frame = self.cap.read()
        except Exception:
            ret = False

        if not ret:
            print(">>> ERRO: Sinal de vídeo perdido. Reconectando...")
            self.cap.release()
            time.sleep(0.5) # Dá um tempo para o buffer limpar
            self.cap = cv2.VideoCapture(URL_STREAM)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return None, None
        # -----------------------------------------------

        frame = cv2.flip(frame, 1)
        ih, iw = frame.shape[:2]
        
        processar_ia = state in ["RASTREIO_ROSTO", "RASTREIO_MAO", "VARREDURA"]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if processar_ia else None
        
        info = {
            'face_detected': False, 'face_coords': (-1, -1),
            'hand_detected': False, 'hand_coords': (-1, -1),
            'dedos': -1
        }

        if state in ["RASTREIO_ROSTO", "VARREDURA"] and rgb is not None:
            res_face = self.face_mesh.process(rgb)
            if res_face.multi_face_landmarks:
                info['face_detected'] = True
                face_lms = res_face.multi_face_landmarks[0]
                p = face_lms.landmark[4] 
                info['face_coords'] = (int(p.x * iw), int(p.y * ih))
                self.mp_drawing.draw_landmarks(frame, face_lms, self.mp_face_mesh.FACEMESH_TESSELATION, None, self.draw_spec_face)

        elif state == "RASTREIO_MAO" and rgb is not None:
            res_hands = self.hands.process(rgb)
            if res_hands.multi_hand_landmarks:
                info['hand_detected'] = True
                hl = res_hands.multi_hand_landmarks[0]
                p = hl.landmark[8] 
                info['hand_coords'] = (int(p.x * iw), int(p.y * ih))
                self.mp_drawing.draw_landmarks(frame, hl, self.mp_hands.HAND_CONNECTIONS, self.draw_spec_hand)

        return frame, info

    def show_hud(self, frame, state, sub_state, timer):
        if frame is None: return
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 40), (0, 0, 0), -1)
        cor_status = (0, 255, 0) if state != "TRAVADO" else (0, 0, 255)
        cv2.putText(frame, f"MODO: {state}", (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor_status, 2)
        cv2.imshow("Tagarela Robot", frame)