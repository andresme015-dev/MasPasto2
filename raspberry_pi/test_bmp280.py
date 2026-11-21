"""BMP280 (I2C 0x76): temperatura y presion.
El modulo es BMP280 (registro de ID 0xD0 = 0x58), no BME280: no mide humedad."""
import smbus2
import bme280

DIRECCION = 0x76
bus = smbus2.SMBus(1)
params = bme280.load_calibration_params(bus, DIRECCION)


def leer_bmp280():
    data = bme280.sample(bus, DIRECCION, params)
    return {
        "temperatura_c": round(data.temperature, 2),
        "presion_hpa": round(data.pressure, 2),
    }


if __name__ == "__main__":
    m = leer_bmp280()
    print(m["temperatura_c"], "°C")
    print(m["presion_hpa"], "hPa")
