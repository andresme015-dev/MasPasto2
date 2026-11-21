// Modulo zenit: ESP32 Dev Module + AS7341 (SDA=GPIO21, SCL=GPIO22)
// Envia un JSON por UDP al puerto 5005 de la Raspberry Pi cada segundo.
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <Adafruit_AS7341.h>

// ------------------- configuracion -------------------
const char*    SSID_AP     = "PasturaMetrics";
const char*    PASS_AP     = "CLAVE_RED_PASTURAMETRICS";
const uint16_t PUERTO      = 5005;
const uint32_t PERIODO_MS  = 1000;
const bool     TX_REDUCIDA = false;     // true solo con la QT Py ESP32-C3 (problema de antena)
const int      PIN_SDA     = 21;        // ESP32 Dev Module
const int      PIN_SCL     = 22;

// Integracion: (ATIME+1)*(ASTEP+1)*2,78 us = 101*1000*2,78 us = 280,78 ms
const uint8_t  ATIME = 100;
const uint16_t ASTEP = 999;
const float    T_INT_MS = (ATIME + 1) * (ASTEP + 1) * 0.00278f;

// Ganancia adaptativa
const as7341_gain_t GANANCIAS[] = {
  AS7341_GAIN_0_5X, AS7341_GAIN_1X, AS7341_GAIN_2X, AS7341_GAIN_4X,
  AS7341_GAIN_8X,   AS7341_GAIN_16X, AS7341_GAIN_32X, AS7341_GAIN_64X };
const float MULT[] = {0.5, 1, 2, 4, 8, 16, 32, 64};
const int   N_GAN  = 8;
const uint16_t LIM_SAT  = 58000;
const uint16_t LIM_BAJO = 12000;
int idxGan = 3;

Adafruit_AS7341 as7341;
WiFiUDP udp;
uint32_t seq = 0;

bool conectarWiFiFijo(uint32_t limite_ms = 20000) {
  WiFi.disconnect(true);
  delay(300);
  WiFi.mode(WIFI_STA);
  if (TX_REDUCIDA) WiFi.setTxPower(WIFI_POWER_8_5dBm);

  int n = WiFi.scanNetworks();
  uint8_t bssid[6]; int32_t canal = 0, mejor = -200; bool hay = false;
  for (int i = 0; i < n; i++) {
    if (WiFi.SSID(i) == String(SSID_AP) && WiFi.RSSI(i) > mejor) {
      mejor = WiFi.RSSI(i); canal = WiFi.channel(i);
      memcpy(bssid, WiFi.BSSID(i), 6); hay = true;
    }
  }
  WiFi.scanDelete();
  if (!hay) { Serial.println("[wifi] AP no visible"); return false; }

  WiFi.setMinSecurity(WIFI_AUTH_WPA_PSK);   // TEMPORAL: borrar cuando el AP quede en WPA2
  WiFi.begin(SSID_AP, PASS_AP, canal, bssid, true);
  if (TX_REDUCIDA) WiFi.setTxPower(WIFI_POWER_8_5dBm);

  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < limite_ms) delay(250);
  if (WiFi.status() != WL_CONNECTED) { Serial.println("[wifi] no conecto"); return false; }

  WiFi.setSleep(false);   // evita que la power bank se apague por bajo consumo
  Serial.printf("[wifi] conectado  IP %s  gateway %s  canal %d  %d dBm\n",
                WiFi.localIP().toString().c_str(), WiFi.gatewayIP().toString().c_str(),
                canal, WiFi.RSSI());
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Wire.begin(PIN_SDA, PIN_SCL);
  if (!as7341.begin()) {
    Serial.println("[as7341] no detectado: revisa SDA, SCL y alimentacion");
    while (true) delay(1000);
  }
  as7341.setATIME(ATIME);
  as7341.setASTEP(ASTEP);
  as7341.setGain(GANANCIAS[idxGan]);
  Serial.println("[as7341] listo");
  conectarWiFiFijo();
}

void loop() {
  static uint32_t t0 = 0;
  if (millis() - t0 < PERIODO_MS) return;
  t0 = millis();

  if (WiFi.status() != WL_CONNECTED) { conectarWiFiFijo(); return; }

  uint16_t c[12];
  if (!as7341.readAllChannels(c)) { Serial.println("[as7341] error de lectura"); return; }

  // indices validos: 0-3 = F1-F4, 6-9 = F5-F8, 10 = Clear, 11 = NIR
  const int idx[] = {0, 1, 2, 3, 6, 7, 8, 9, 10, 11};
  uint16_t maxv = 0;
  for (int i : idx) if (c[i] > maxv) maxv = c[i];

  bool  sat       = maxv >= LIM_SAT;
  float gananciaX = MULT[idxGan];

  if (sat && idxGan > 0)                                as7341.setGain(GANANCIAS[--idxGan]);
  else if (!sat && maxv < LIM_BAJO && idxGan < N_GAN-1) as7341.setGain(GANANCIAS[++idxGan]);

  char buf[512];
  int n = snprintf(buf, sizeof(buf),
    "{\"modulo\":\"zenit\",\"seq\":%lu,\"t_ms\":%lu,"
    "\"f1_415nm\":%u,\"f2_445nm\":%u,\"f3_480nm\":%u,\"f4_515nm\":%u,"
    "\"f5_555nm\":%u,\"f6_590nm\":%u,\"f7_630nm\":%u,\"f8_680nm\":%u,"
    "\"clear\":%u,\"nir_910nm\":%u,"
    "\"ganancia_x\":%.1f,\"t_int_ms\":%.2f,\"saturado\":%s,\"rssi_dbm\":%d}",
    (unsigned long)seq++, (unsigned long)millis(),
    c[0], c[1], c[2], c[3], c[6], c[7], c[8], c[9], c[10], c[11],
    gananciaX, T_INT_MS, sat ? "true" : "false", WiFi.RSSI());

  udp.beginPacket(WiFi.gatewayIP(), PUERTO);
  udp.write((const uint8_t*)buf, n);
  udp.endPacket();
  Serial.println(buf);
}
