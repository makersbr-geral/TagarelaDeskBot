#include "esp_camera.h"
#include <WiFi.h>
#include <Arduino.h> // Necessário para verificação de versão

// ==========================================
// 1. DEFINIÇÕES HARDWARE
// ==========================================
#define CAMERA_MODEL_AI_THINKER 
#define LED_GPIO_NUM 4          // O LED do Flash é o pino 4

// ==========================================
// 2. CREDENCIAIS WI-FI
// ==========================================
const char *ssid = "";
const char *password = "";

// ==========================================
// 3. DECLARAÇÃO DE FUNÇÕES
// ==========================================
void startCameraServer();

// --- CORREÇÃO DO ERRO: IMPLEMENTAÇÃO DA FUNÇÃO DO LED ---
// Esta função estava faltando e causava o erro de compilação.
// Ela detecta se seu ESP32 é versão nova ou antiga automaticamente.
void setupLedFlash(int pin) {
    #if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
        // Código para ESP32 Core 3.0 (Seu caso provável)
        // No Core 3.0, ledcAttach configura tudo de uma vez
        ledcAttach(pin, 5000, 8); 
    #else
        // Código para ESP32 Core 2.x (Antigo)
        ledcSetup(0, 5000, 8); // Canal 0, 5kHz, 8 bits
        ledcAttachPin(pin, 0);
    #endif
}

void setup() {
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH); // Liga o LED no máximo
  delay(2000);           // Espera 2 segundos
  digitalWrite(4, LOW);
  
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // ==========================================
  // 4. CONFIGURAÇÃO DA CÂMERA
  // ==========================================
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  
  // Mapeamento correto para AI THINKER
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;   // D4 correto é 36 
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sccb_sda = 26;
  config.pin_sccb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_SVGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  

  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

  // Inicializa a câmera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);       
    s->set_brightness(s, 1);  
    s->set_saturation(s, -2); 
  }

  // ==========================================
  // 5. INICIA O FLASH (LED)
  // ==========================================
  #if defined(LED_GPIO_NUM)
    setupLedFlash(LED_GPIO_NUM);
  #endif

  // ==========================================
  // 6. CONEXÃO WI-FI
  // ==========================================
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
}

void loop() {
  delay(10000);
}