#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

/**
 * 1. CONFIGURAÇÕES / SETTINGS
 */
const char *ssid = "";
const char *password = "";

#define SERVO_X_PIN 14 
#define SERVO_Y_PIN 15 
#define UDP_PORT 8888 

// Global Objects
Servo servoX;
Servo servoY;
WiFiUDP udp;
char packetBuffer[64]; // Reduced buffer for speed / Buffer reduzido para maior velocidade

// Camera Model Definitions
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

void startCameraServer(); 

void setup() {
  // Set CPU to maximum speed for faster processing
  // Define CPU para velocidade máxima para processamento mais rápido
  setCpuFrequencyMhz(240);

  // Servo setup with specific timings
  // Configuração dos servos com timings específicos
  servoX.setPeriodHertz(50); 
  servoY.setPeriodHertz(50);
  servoX.attach(SERVO_X_PIN, 500, 2400); 
  servoY.attach(SERVO_Y_PIN, 500, 2400);
  
  // Initial position: Center
  // Posição inicial: Centro
  servoX.write(90);
  servoY.write(90);

  /**
   * CAMERA CONFIGURATION / CONFIGURAÇÃO DA CÂMERA
   */
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Optimize for low latency streaming (QVGA is faster than SVGA)
  // Otimização para streaming de baixa latência (QVGA é mais rápido que SVGA)
  if(psramFound()){
    config.frame_size = FRAMESIZE_QVGA; 
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST; // Always get the newest frame / Pega sempre o quadro mais atual
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) return;

  // Wi-Fi Connection / Conexão Wi-Fi
  WiFi.begin(ssid, password);
  WiFi.setSleep(false); // Disable power save for lower latency / Desativa economia de energia para reduzir latência
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
  }
  
  startCameraServer();
  udp.begin(UDP_PORT);
}

void loop() {
  /**
   * DYNAMIC UDP PROCESSING / PROCESSAMENTO DINÂMICO UDP
   */
  int packetSize = udp.parsePacket();
  
  if (packetSize) {
    int len = udp.read(packetBuffer, sizeof(packetBuffer) - 1);
    if (len > 0) {
      packetBuffer[len] = 0; // Null-terminate string

      int posX, posY;
      // Use sscanf for much faster parsing than String objects
      // Uso de sscanf para processamento muito mais rápido que objetos String
      if (sscanf(packetBuffer, "%d,%d", &posX, &posY) == 2) {
        // Constrain values to safe servo limits (0-180)
        // Limita os valores aos limites seguros do servo
        servoX.write(constrain(posX, 0, 180));
        servoY.write(constrain(posY, 0, 180));
      }
    }
  }
  // No delay() here to maintain maximum responsiveness
  // Sem delay() aqui para manter a responsividade máxima
}