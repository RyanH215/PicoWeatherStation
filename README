# Weather Station - Raspberry Pi Pico W

![MicroPython](https://img.shields.io/badge/MicroPython-1.22-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20Pico%20W-red)

A solar-powered weather station using Raspberry Pi Pico W that measures temperature, humidity, and pressure with a BME280 sensor. Features WiFi data transmission and intelligent power management.

![Weather Station](https://img.shields.io/badge/status-production%20ready-brightgreen)

## 📋 Table of Contents

- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Software Setup](#software-setup)
- [Usage](#usage)
- [Data Transmission](#data-transmission-options)
- [Calibration](#calibration)
- [Power Consumption](#power-consumption)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)
- [Future Enhancements](#future-enhancements)

## ✨ Features

- 🌡️ **BME280 Sensor**: Temperature, humidity, and barometric pressure measurements
- ☀️ **Solar Power**: Battery monitoring with adaptive sleep modes
- 📡 **WiFi Transmission**: Supports ThingSpeak, MQTT, or custom HTTP POST
- 🔋 **Power Efficient**: Deep sleep between readings to maximize battery life
- 💾 **Data Buffering**: Stores data locally when WiFi unavailable
- 📊 **Derived Calculations**: Dew point, sea level pressure, altitude
- 🔧 **Diagnostic Tools**: Built-in testing and calibration functions

## 🛠️ Hardware Requirements

### Core Components

| Component | Specification | Notes |
|-----------|---------------|-------|
| Microcontroller | Raspberry Pi Pico W or Pico 2 W | WiFi required |
| Sensor | BME280 (I2C) | Temperature, humidity, pressure |
| Solar Panel | 5-10W, 5-6V | For continuous outdoor operation |
| Battery | Li-ion/LiPo 3000-5000mAh | 18650 recommended |
| Charge Controller | TP4056 or similar | With load sharing |
| Voltage Regulator | 5V output, Buck-Boost | Stable power supply |
| Enclosure | IP65+ weatherproof | UV-resistant plastic |

### Wiring Connections

#### BME280 Sensor (I2C)

```
BME280 VCC  → Pico 3.3V (Pin 36)
BME280 GND  → Pico GND (Pin 38)
BME280 SDA  → Pico GP0 (Pin 1)
BME280 SCL  → Pico GP1 (Pin 2)
```

#### Battery Monitoring

```
Battery (+) → Voltage Divider → Pico GP27/ADC1 (Pin 32)
                              → Pico GND (Pin 33)

Voltage Divider: Use two equal resistors (e.g., 10kΩ each)
to divide battery voltage by 2 for ADC reading
```

#### Power Supply

```
Solar Panel → Charge Controller → Battery
           → Voltage Regulator → Pico VSYS (Pin 39)
                               → Pico GND (Pin 38)
```

#### Optional Status LED

```
Pico GP28 (Pin 34) → 220Ω Resistor → LED → GND
```

> 📘 **See [WIRING.md](WIRING.md) for detailed diagrams and schematics**

## 💻 Software Setup

### 1. Install MicroPython

1. Download MicroPython firmware for Pico W from [micropython.org](https://micropython.org/download/rp2-pico-w/)
2. Hold BOOTSEL button while plugging in Pico
3. Copy `.uf2` file to RPI-RP2 drive
4. Pico will reboot with MicroPython installed

### 2. Install Required Libraries

Some libraries are built-in, but you may need `urequests`:

```python
# Connect to Pico via Thonny or similar IDE
import upip
upip.install('urequests')
```

### 3. Upload Files to Pico

Upload all `.py` files to the Pico:
- `config.py`
- `bme280.py`
- `power.py`
- `wifi_manager.py`
- `main.py`

### 4. Configure Settings

Edit `config.py` and update:

```python
# WiFi credentials
WIFI_SSID = "Your_WiFi_Name"
WIFI_PASSWORD = "Your_WiFi_Password"

# ThingSpeak (if using)
THINGSPEAK_API_KEY = "Your_Write_API_Key"

# Station information
STATION_NAME = "My Weather Station"
STATION_LOCATION = "City, State"
STATION_LATITUDE = 29.7030
STATION_LONGITUDE = -98.1245
STATION_ELEVATION = 190  # meters

# Sensor reading interval (seconds)
SENSOR_READ_INTERVAL = 300  # 5 minutes

# I2C address (check your BME280 - usually 0x76 or 0x77)
BME280_I2C_ADDR = 0x76
```

> 🚀 **See [QUICKSTART.md](QUICKSTART.md) for a simplified 5-minute setup guide**

## 🎯 Usage

### First Time Setup

1. **Test I2C Connection**:
```python
from machine import I2C, Pin
i2c = I2C(0, sda=Pin(0), scl=Pin(1))
print(i2c.scan())  # Should show [118] for 0x76 or [119] for 0x77
```

2. **Run Diagnostics**:
```python
import main
station = main.WeatherStation()
station.run_diagnostics()
```

3. **Test Single Reading**:
```python
station.run_once()
```

4. **Start Continuous Operation**:
```python
station.run_continuous()
```

### Running Automatically on Boot

To run automatically when powered on, create `boot.py`:

```python
# boot.py
import main
try:
    main.main()
except Exception as e:
    print(f"Error: {e}")
```

### Example Output

```
======================================================================
  Reading #1 - Station: Home Weather Station
======================================================================
  Temperature:       25.32°C
  Humidity:           52.3%
  Pressure:         1013.45 hPa
  Dew Point:         14.56°C
  Sea Level Press:  1035.62 hPa
----------------------------------------------------------------------
  Battery Voltage:    3.85V
  Battery Level:      70.8%
  Battery State:    NORMAL
----------------------------------------------------------------------
  Uptime:           120s
======================================================================

✓ Data transmitted successfully!
```

## 📊 Data Transmission Options

### ThingSpeak

1. Create account at [thingspeak.com](https://thingspeak.com)
2. Create new channel with fields:
   - Field 1: Temperature (°C)
   - Field 2: Humidity (%)
   - Field 3: Pressure (hPa)
   - Field 4: Battery Voltage (V)
   - Field 5: Battery Percentage (%)
3. Copy Write API Key to `config.py`
4. Set `USE_THINGSPEAK = True`

### HTTP POST (Custom Server)

Set in `config.py`:
```python
USE_HTTP_POST = True
HTTP_POST_URL = "https://your-server.com/api/weather"
HTTP_POST_API_KEY = "your_api_key"
```

Data format sent:
```json
{
  "station_name": "Home Weather Station",
  "location": "City, State",
  "timestamp": 1234567890,
  "data": {
    "temperature": 25.5,
    "humidity": 60.0,
    "pressure": 1013.25,
    "battery_voltage": 3.8,
    "battery_percent": 75.0
  }
}
```

### MQTT (Coming Soon)

MQTT support for Home Assistant and other platforms is planned for future releases.

## ⚙️ Calibration

### BME280 Calibration

Compare readings with reference instruments and adjust offsets in `config.py`:

```python
TEMP_OFFSET = 0.0  # Add/subtract degrees
HUMIDITY_OFFSET = 0.0  # Add/subtract percent
PRESSURE_OFFSET = 0.0  # Add/subtract hPa
```

### Battery Voltage Calibration

1. Measure actual battery voltage with multimeter
2. Run calibration:
```python
from power import PowerManager
pm = PowerManager()
pm.calibrate(actual_voltage=3.85)  # Use your measured voltage
```

The calibration factor will be displayed and stored in memory (not persistent - add to config if needed).

## 🔋 Power Consumption

| Mode | Current Draw | Notes |
|------|--------------|-------|
| Active (WiFi on) | 100-150mA | During transmission |
| Light sleep | 1-2mA | Between readings |
| Reading interval | 5 minutes | Configurable |
| Active time per cycle | ~10-15 seconds | Sensor read + transmit |

**Power Budget:**
- **Daily consumption estimate**: ~50-100mAh
- **Recommended battery**: 3000-5000mAh (30-60 days backup)
- **Solar panel**: 5-10W sufficient for continuous operation

## 🐛 Troubleshooting

<details>
<summary><b>BME280 Not Found</b></summary>

- Check I2C wiring (SDA/SCL not swapped)
- Verify I2C address with `i2c.scan()`
- Try address 0x77 if 0x76 doesn't work
- Check 3.3V power connection
</details>

<details>
<summary><b>WiFi Connection Fails</b></summary>

- Verify SSID and password in `config.py`
- Check WiFi signal strength (2.4GHz only)
- Ensure router allows new devices
- Check for special characters in password
</details>

<details>
<summary><b>Data Not Transmitting</b></summary>

- Verify API keys are correct
- Check internet connectivity
- Look for buffered data: `wifi_manager.data_buffer`
- Enable debug mode: `DEBUG_MODE = True`
</details>

<details>
<summary><b>Battery Reading Incorrect</b></summary>

- Check voltage divider resistor values
- Verify ADC pin connection
- Run battery calibration
- Check for loose connections
</details>

<details>
<summary><b>Sensor Readings Seem Wrong</b></summary>

- Allow sensor to stabilize (5-10 minutes)
- Check for direct sunlight on sensor
- Verify proper ventilation
- Apply calibration offsets
</details>

## 📁 File Structure

```
weather_station/
├── main.py              # Main program and orchestration
├── config.py            # Configuration settings
├── bme280.py            # BME280 sensor driver
├── power.py             # Battery monitoring and power management
├── wifi_manager.py      # WiFi and data transmission
├── wind.py              # (Future) Wind sensor handling
├── rain.py              # (Future) Rain gauge handling
├── README.md            # This file
├── QUICKSTART.md        # Quick setup guide
└── WIRING.md            # Detailed wiring diagrams
```

## 📚 API Reference

### WeatherStation Class

```python
station = WeatherStation()

# Run single reading cycle
data = station.run_once()

# Run continuous operation
station.run_continuous()

# Run diagnostics
station.run_diagnostics()

# Manual sensor reading
data = station.read_sensors()

# Manual data transmission
success = station.transmit_data(data)
```

### BME280 Class

```python
from machine import I2C, Pin
from bme280 import BME280

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
bme = BME280(i2c, addr=0x76)

# Read all data
temp, pressure, humidity = bme.read_compensated_data()

# Read individual values
temp = bme.read_temperature()
pressure = bme.read_pressure()
humidity = bme.read_humidity()

# Calculate derived values
dew_point = bme.calculate_dew_point(temp, humidity)
altitude = bme.calculate_altitude(pressure)
sea_level = bme.calculate_sea_level_pressure(elevation_m)
```

### PowerManager Class

```python
from power import PowerManager

pm = PowerManager()

# Get battery voltage
voltage = pm.read_battery_voltage()

# Get battery percentage
percent = pm.get_battery_percentage()

# Get full status
status = pm.get_battery_status()

# Check battery health
is_ok = pm.is_battery_ok()

# Get suggested sleep time
sleep_time = pm.get_suggested_sleep_time()
```

### WiFiManager Class

```python
from wifi_manager import WiFiManager

wm = WiFiManager()

# Connect to WiFi
wm.connect()

# Send data
data = {'temperature': 25.5, 'humidity': 60.0}
wm.send_data(data)

# Check connection
info = wm.get_connection_info()

# Sync time
wm.sync_time_ntp()
```

## 🚀 Future Enhancements

- [ ] Wind speed and direction sensors (anemometer, wind vane)
- [ ] Rainfall measurement (tipping bucket rain gauge)
- [ ] Local data logging to SD card
- [ ] Web interface for configuration
- [ ] MQTT support
- [ ] Home Assistant integration
- [ ] Weather forecasting based on pressure trends
- [ ] Multiple sensor support (daisy-chaining)
- [ ] Display support (OLED/E-ink)

## 📄 License

This project is open source and available under the MIT License. Feel free to modify and distribute.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 💬 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review configuration settings in `config.py`
3. Enable debug mode for detailed output: `DEBUG_MODE = True`
4. Check sensor datasheets for specifications
5. Open an issue on GitHub

## 🏆 Acknowledgments

- Built with [MicroPython](https://micropython.org/)
- BME280 sensor by Bosch Sensortec
- Inspired by DIY weather station projects worldwide

## 📊 Version History

### v1.0 (2024-02-15)
- ✅ BME280 sensor support
- ✅ Power management with battery monitoring
- ✅ WiFi transmission (ThingSpeak)
- ✅ Data buffering for offline operation
- ✅ Diagnostic tools and calibration
- ✅ Solar power optimization

---

**Made with ❤️ for weather enthusiasts and IoT hobbyists**

⭐ Star this repo if you find it helpful!

