# Tagarela Deskbot 🤖
### Open-Source AI Desktop Companion & Accessibility Tool

**Tagarela** is a DIY, open-source desktop robot designed to bridge the gap between AI models and the physical world. It acts as a physical copilot that can see, track, and interact with you using Python, Computer Vision, and ESP32.

# To Do List
* **Voice commands**
* **Screen interaction**
* **Api Consumer**
* **Self Balance**

---

## 🎯 The Vision
Tagarela is built to be a **hardware-agnostic** and **subscription-free** alternative to closed-market robots. 
One of its core missions is **accessibility**: The robot can take screenshots, send them to a Vision AI, and describe the desktop content via audio to assist visually impaired users.

## 🧠 Current Tech Stack
* **Language:** Python 3.x
* **Computer Vision:** [MediaPipe](https://mediapipe.dev/) (Face Mesh, Hands, and Pose detection). << USING JUST CV2 AFTER SOME TESTS, STILL TESTING
* **Communication:** Low-latency **UDP Protocol** for real-time servo control.
* **Hardware (Current Prototype):** ESP32-CAM, Pan-Tilt Servo system.
* **Interface:** Gesture-based menu system (no keyboard/mouse needed for basic operation).

## 🚀 Key Features in the Code
* **Real-time Tracking:** Smooth movement logic for Face, Hand (Index finger), and Pose.
* **Gesture Control System:**
    * **5 Fingers:** Wake up / Abort / Go back.
    * **Pinch Gesture:** Toggle ESP32 Flash/LED (with visual progress bar).
    * **Fist/0 Fingers:** Confirm selection or Sleep mode.
* **Anti-Jitter Filter:** Smart movement threshold to reduce mechanical vibration and save Wi-Fi bandwidth.
* **Auto-Scan Mode:** Automatically searches for users when they leave the camera's field of view.

## 🛠️ Hardware Roadmap (Support Needed!)
I have pushed the standard **ESP32-CAM** to its limits. To evolve Tagarela into a professional-grade robot, I am raising funds to upgrade to:
* **ESP32-S3 (Xiao Sense):** For onboard AI processing and digital microphone support.
* **Precision Motors:** High-quality servos/steppers for professional movement.
* **Custom PCB:** To eliminate "spaghetti wiring" and create a robust hardware kit.

## 💰 Support the Project
If you believe in open-source robotics, consider supporting the development. 100% of the funds go towards buying components and development time.

**[Link to Wise / Donation here]**

---

## 💻 How to Run the Python Controller

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/tagarela-deskbot.git](https://github.com/your-username/tagarela-deskbot.git)
    ```
2.  **Install dependencies:**
    ```bash
    pip install opencv-python mediapipe numpy requests
    ```
3.  **Configure your ESP32 IP:**
    Open `controller.py` and update the `IP_ESP` variable with your robot's IP address.
4.  **Run:**
    ```bash
    python controller.py
    ```

---

## 🤝 Contributing & Support

Contributions are welcome! Whether it's refining the Python logic, porting to C++ (ESP-IDF), or improving the 3D chassis design, feel free to open a Pull Request.

### ⚡ Support the Project
**Help me keep the soldering iron hot!** (Me ajude a manter o ferro de solda quente!)
Your support is vital to upgrade the hardware from the ESP32-CAM to the ESP32-S3 and fund the development of custom PCBs.

* **Global Support (Wise):** [Pay via Wise](https://wise.com/pay/me/wagnerwelingtond) 🌍
* **Brazilian Support (Apoia.se):** [Apoia.se/tagareladeskbot](https://apoia.se/tagareladeskbot) 🇧🇷

---

## 🔗 Connect with the Maker

| Platform | Link |
| :--- | :--- |
| **YouTube (Global)** | [@] [Wagner Maker Global](https://youtube.com/@wagnermaker-global) 🌐 |
| **YouTube (PT-BR)** | [@] [Wagner Maker](https://www.youtube.com/@wagnermaker) 🇧🇷 |
| **LinkedIn** | [in/wagner-domingues](https://www.linkedin.com/in/wagner-domingues-a41ab039) 💼 |
| **TikTok (PT-BR)** | [@wagnermaker](https://www.tiktok.com/@wagnermaker) 🎥 |
| **TikTok (Dev Log)** | [@tagareladeskbot](https://www.tiktok.com/@tagareladeskbot) 🛠️ |

---
**Developed with ☕ and ⚡ by Wagner Wellington**
*Mechatronics Technician | AI Enthusiast | Open Source Advocate*
