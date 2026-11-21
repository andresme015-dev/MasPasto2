// Modulo zenit (MasPasto2): ESP32 Dev Module + AS7343 (SDA=GPIO21, SCL=GPIO22)
// Envia un JSON por UDP al puerto 5005 de la Raspberry Pi despues de cada lectura.
// Escucha ordenes en el puerto 5006:
//   "G<n>"  fija la ganancia en el indice n (0 = 0,5x, 1 = 1x, ..., 7 = 64x, 12 = 2048x)
//   "GA"    vuelve a la ganancia adaptativa
// Librerias (Arduino IDE > Gestor de librerias): "Adafruit AS7343" (instala Adafruit BusIO).
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <Adafruit_AS7343.h>

// ------------------- configuracion -------------------
// Red a la que se conecta el ESP32:
//   USAR_RED_CASA = false -> red PasturaMetrics que crea la Raspberry (campo); los datos
//                            van al gateway, que es la Raspberry (192.168.4.1).
//   USAR_RED_CASA = true  -> red Wi-Fi de la casa (2,4 GHz); los datos van a IP_RPI_CASA,
//                            la IP que tiene la Raspberry en esa red.
const bool     USAR_RED_CASA = false;   // pruebas: red PasturaMetrics
const char*    SSID_CASA     = "NOMBRE_RED_CASA";
const char*    PASS_CASA     = "CLAVE_RED_CASA";
const char*    IP_RPI_CASA   = "IP_DE_LA_RPI_EN_CASA";
const char*    SSID_AP       = USAR_RED_CASA ? SSID_CASA : "PasturaMetrics";
const char*    PASS_AP       = USAR_RED_CASA ? PASS_CASA : "CLAVE_RED_PASTURAMETRICS";
// Identificacion del sensor fisico y del montaje (se envian en cada paquete y quedan en
// los CSV). Cambialas si cambias de sensor o de montaje.
const char*    ID_SENSOR     = "B";              // sensor fisico conectado a este ESP32
const char*    CONFIG_MONT   = "desnudo";        // "desnudo" o "capsula_ptfe"
const uint16_t PUERTO_DATOS = 5005;
const uint16_t PUERTO_CMD   = 5006;
const uint32_t PERIODO_MS   = 1000;   // una lectura dura ~0,55 s; se envia como maximo 1 por segundo
const int      PIN_SDA      = 21;
const int      PIN_SCL      = 22;

// Integracion por ciclo: (ATIME+1)*(ASTEP+1)*2,78 us = 100*656*2,78 us = 182,4 ms.
// Es el tiempo mas corto que conserva el techo de 65535 cuentas; con 3 ciclos la lectura
// completa toma ~0,55 s, por debajo del limite de 1 s de readAllChannels().
const uint8_t  ATIME    = 99;
const uint16_t ASTEP    = 655;
const float    T_INT_MS = (ATIME + 1) * (ASTEP + 1) * 0.00278f;

// Ganancia adaptativa: 0,5x a 64x (se amplia solo si la Etapa 1 verifica mas ganancias).
// Los limites se aplican al canal mas alto de los 18, VIS incluido: con el VIS saturado los
// canales espectrales reciben un exceso de cuentas (prueba del 2026-10-21). Los indicadores
// de saturacion del sensor se envian pero no se usan para decidir (en las pruebas no se
// activaron ni con 65535 cuentas).
const int      GAN_MIN  = AS7343_GAIN_0_5X;   // indice 0
const int      GAN_MAX  = AS7343_GAIN_64X;    // indice 7
const uint16_t LIM_SAT  = 58981;              // 90 % del techo de 65535 cuentas
const uint16_t LIM_BAJO = 26214;              // 40 % del techo
const int      MAX_AJUSTES = 6;
int  idxGan   = AS7343_GAIN_4X;               // indice 3
bool ganFija  = false;

// Posiciones de los 12 canales espectrales y de los 6 VIS en el arreglo de 18 lecturas
const int IDX_ESP[12] = {AS7343_CHANNEL_F1, AS7343_CHANNEL_F2, AS7343_CHANNEL_FZ, AS7343_CHANNEL_F3,
                         AS7343_CHANNEL_F4, AS7343_CHANNEL_F5, AS7343_CHANNEL_FY, AS7343_CHANNEL_FXL,
                         AS7343_CHANNEL_F6, AS7343_CHANNEL_F7, AS7343_CHANNEL_F8, AS7343_CHANNEL_NIR};
const int IDX_VIS[6]  = {AS7343_CHANNEL_VIS_TL_0, AS7343_CHANNEL_VIS_BR_0, AS7343_CHANNEL_VIS_TL_1,
                         AS7343_CHANNEL_VIS_BR_1, AS7343_CHANNEL_VIS_TL_2, AS7343_CHANNEL_VIS_BR_2};

uint16_t maxDe(const uint16_t *c, const int *idx, int n) {
  uint16_t m = 0;
  for (int i = 0; i < n; i++) if (c[idx[i]] > m) m = c[idx[i]];
  return m;
}

Adafruit_AS7343 as7343;
WiFiUDP udp;       // datos
WiFiUDP udpCmd;    // ordenes
uint32_t seq = 0;
IPAddress destino;  // Raspberry

float ganX(int i) { return powf(2.0f, (float)(i - 1)); }

bool conectarWiFiFijo(uint32_t limite_ms = 20000) {
  WiFi.disconnect(true);
  delay(300);
  WiFi.mode(WIFI_STA);

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

  WiFi.begin(SSID_AP, PASS_AP, canal, bssid, true);   // BSSID y canal fijos
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < limite_ms) delay(250);
  if (WiFi.status() != WL_CONNECTED) { Serial.println("[wifi] no conecto"); return false; }

  if (USAR_RED_CASA) destino.fromString(IP_RPI_CASA);
  else               destino = WiFi.gatewayIP();
  WiFi.setSleep(false);   // evita que la power bank se apague por bajo consumo
  udpCmd.stop();
  udpCmd.begin(PUERTO_CMD);
  Serial.printf("[wifi] conectado a %s  IP %s  envia a %s  canal %d  %d dBm\n", SSID_AP,
                WiFi.localIP().toString().c_str(), destino.toString().c_str(),
                canal, WiFi.RSSI());
  return true;
}

void revisarOrdenes() {
  int len = udpCmd.parsePacket();
  if (len <= 0) return;
  char msg[16] = {0};
  udpCmd.read(msg, sizeof(msg) - 1);
  if (msg[0] == 'G' && msg[1] == 'A') {
    ganFija = false;
    Serial.println("[cmd] ganancia adaptativa");
  } else if (msg[0] == 'G') {
    int i = atoi(msg + 1);
    if (i >= 0 && i <= 12) {
      ganFija = true; idxGan = i;
      as7343.setGain((as7343_gain_t)idxGan);
      Serial.printf("[cmd] ganancia fija %.1fx\n", ganX(idxGan));
    }
  }
}

// Lee los 18 canales; devuelve false si falla la lectura
bool leer(uint16_t *c, bool &satA, bool &satD) {
  if (!as7343.readAllChannels(c)) return false;
  satA = as7343.isAnalogSaturated();
  satD = as7343.isDigitalSaturated();
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Wire.begin(PIN_SDA, PIN_SCL);
  if (!as7343.begin(AS7343_I2CADDR_DEFAULT, &Wire)) {
    Serial.println("[as7343] no detectado: revisa SDA, SCL y alimentacion");
    while (true) delay(1000);
  }
  as7343.setATIME(ATIME);
  as7343.setASTEP(ASTEP);
  as7343.setSMUXMode(AS7343_SMUX_18CH);       // necesario para F7 y F8
  as7343.setGain((as7343_gain_t)idxGan);
  Serial.printf("[as7343] listo  sensor %s  montaje %s  t_int %.1f ms por ciclo\n",
                ID_SENSOR, CONFIG_MONT, T_INT_MS);
  conectarWiFiFijo();
}

void loop() {
  static uint32_t t0 = 0;
  if (WiFi.status() != WL_CONNECTED) { conectarWiFiFijo(); return; }
  revisarOrdenes();
  if (millis() - t0 < PERIODO_MS) return;
  t0 = millis();

  uint16_t c[18];
  bool satA = false, satD = false;
  uint32_t tLect = 0;
  int g = idxGan;
  for (int k = 0; k < MAX_AJUSTES; k++) {
    g = idxGan;
    tLect = millis();
    if (!leer(c, satA, satD)) { Serial.println("[as7343] error de lectura"); return; }
    if (ganFija) break;
    uint16_t m = 0;
    for (int i = 0; i < 18; i++) if (c[i] > m) m = c[i];   // 18 canales, VIS incluido
    if (m >= LIM_SAT && idxGan > GAN_MIN) {
      as7343.setGain((as7343_gain_t)(--idxGan)); continue;
    }
    if (m < LIM_BAJO && idxGan < GAN_MAX) {
      as7343.setGain((as7343_gain_t)(++idxGan)); continue;
    }
    break;
  }
  uint16_t m = 0;
  for (int i = 0; i < 18; i++) if (c[i] > m) m = c[i];   // 18 canales: criterio
  uint16_t mEsp = maxDe(c, IDX_ESP, 12);                  // informativo
  bool sat    = m >= LIM_SAT;
  bool satVis = maxDe(c, IDX_VIS, 6) >= LIM_SAT;

  char buf[768];
  int n = snprintf(buf, sizeof(buf),
    "{\"modulo\":\"zenit\",\"sensor\":\"AS7343\",\"id_sensor\":\"%s\",\"config\":\"%s\","
    "\"seq\":%lu,\"t_ms\":%lu,"
    "\"f1_405nm\":%u,\"f2_425nm\":%u,\"fz_450nm\":%u,\"f3_475nm\":%u,"
    "\"f4_515nm\":%u,\"f5_550nm\":%u,\"fy_555nm\":%u,\"fxl_600nm\":%u,"
    "\"f6_640nm\":%u,\"f7_690nm\":%u,\"f8_745nm\":%u,\"nir_855nm\":%u,"
    "\"vis_c1\":%u,\"vis_c2\":%u,\"vis_c3\":%u,"
    "\"ganancia_idx\":%d,\"ganancia_x\":%.1f,\"ganancia_fija\":%s,\"t_int_ms\":%.2f,\"max_cuentas\":%u,\"max_espectral\":%u,\"vis_saturado\":%s,"
    "\"sat_analogica\":%s,\"sat_digital\":%s,\"saturado\":%s,\"rssi_dbm\":%d}",
    ID_SENSOR, CONFIG_MONT, (unsigned long)seq++, (unsigned long)tLect,
    c[AS7343_CHANNEL_F1], c[AS7343_CHANNEL_F2], c[AS7343_CHANNEL_FZ], c[AS7343_CHANNEL_F3],
    c[AS7343_CHANNEL_F4], c[AS7343_CHANNEL_F5], c[AS7343_CHANNEL_FY], c[AS7343_CHANNEL_FXL],
    c[AS7343_CHANNEL_F6], c[AS7343_CHANNEL_F7], c[AS7343_CHANNEL_F8], c[AS7343_CHANNEL_NIR],
    (unsigned)(c[AS7343_CHANNEL_VIS_TL_0] + c[AS7343_CHANNEL_VIS_BR_0]),
    (unsigned)(c[AS7343_CHANNEL_VIS_TL_1] + c[AS7343_CHANNEL_VIS_BR_1]),
    (unsigned)(c[AS7343_CHANNEL_VIS_TL_2] + c[AS7343_CHANNEL_VIS_BR_2]),
    g, ganX(g), ganFija ? "true" : "false", T_INT_MS, (unsigned)m, (unsigned)mEsp, satVis ? "true" : "false",
    satA ? "true" : "false", satD ? "true" : "false", sat ? "true" : "false", WiFi.RSSI());

  udp.beginPacket(destino, PUERTO_DATOS);
  udp.write((const uint8_t*)buf, n);
  udp.endPacket();
  Serial.println(buf);
}
