# config.py - Weather Station Configuration
# Configuration file for Raspberry Pi Pico W Weather Station

# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
WIFI_TIMEOUT = 30  # seconds
WIFI_MAX_RETRIES = 3

# BME280 Configuration
BME280_I2C_BUS = 0  # I2C bus number
BME280_SDA_PIN = 0  # GPIO pin for I2C SDA
BME280_SCL_PIN = 1  # GPIO pin for I2C SCL
BME280_I2C_ADDR = 0x76  # Default address (can be 0x77)
BME280_I2C_FREQ = 400000  # I2C frequency in Hz

# Power Management Configuration
BATTERY_ADC_PIN = 27  # GPIO27 (ADC1) for battery voltage monitoring
BATTERY_VOLTAGE_DIVIDER_RATIO = 2.0  # R1/(R1+R2) if using voltage divider
BATTERY_LOW_VOLTAGE = 3.3  # Voltage threshold for low battery warning
BATTERY_CRITICAL_VOLTAGE = 3.0  # Voltage threshold for critical battery
BATTERY_FULL_VOLTAGE = 4.2  # Full charge voltage for Li-ion
VREF = 3.3  # Reference voltage for ADC

# Data Collection Configuration
SENSOR_READ_INTERVAL = 300  # seconds (5 minutes)
DATA_AVERAGING_SAMPLES = 5  # Number of samples to average
USE_DEEP_SLEEP = True  # Enable deep sleep between readings

# Data Transmission Configuration
TRANSMIT_INTERVAL = 300  # seconds (5 minutes)
DATA_BUFFER_SIZE = 50  # Number of readings to buffer if WiFi unavailable

# ThingSpeak Configuration (example - choose your platform)
USE_THINGSPEAK = True
THINGSPEAK_API_KEY = "YOUR_THINGSPEAK_WRITE_API_KEY"
THINGSPEAK_CHANNEL_ID = "YOUR_CHANNEL_ID"
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# MQTT Configuration (alternative to ThingSpeak)
USE_MQTT = False
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_BASE = "weather_station"
MQTT_CLIENT_ID = "pico_weather_001"
MQTT_USERNAME = ""  # Leave empty if no authentication
MQTT_PASSWORD = ""

# HTTP POST Configuration (alternative - custom server)
USE_HTTP_POST = False
HTTP_POST_URL = "https://your-server.com/api/weather"
HTTP_POST_API_KEY = "YOUR_API_KEY"

# Status LED Configuration
STATUS_LED_PIN = 28  # GPIO pin for status LED (optional)
USE_STATUS_LED = True

# Debug Configuration
DEBUG_MODE = True  # Enable debug print statements
LOG_TO_FILE = False  # Log data to local file (not implemented yet)

# Sensor Calibration Offsets (adjust after calibration)
TEMP_OFFSET = 0.0  # Temperature offset in °C
HUMIDITY_OFFSET = 0.0  # Humidity offset in %
PRESSURE_OFFSET = 0.0  # Pressure offset in hPa

# Time Configuration
TIMEZONE_OFFSET = -6  # Hours offset from UTC (e.g., -6 for CST)
NTP_SERVER = "pool.ntp.org"
SYNC_TIME_ON_BOOT = True

# Error Handling
MAX_SENSOR_READ_FAILURES = 5  # Maximum consecutive sensor read failures before reset
MAX_WIFI_FAILURES = 10  # Maximum consecutive WiFi failures before reset

# Location Information (optional - for data logging)
STATION_NAME = "My Weather Station"
STATION_LOCATION = "City, State"
STATION_LATITUDE = XX.XXXX # Paste your Latitude
STATION_LONGITUDE = -XX.XXXX # Paste your Lonitude
STATION_ELEVATION = 190  # meters
