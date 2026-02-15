# bme280.py - BME280 Sensor Driver
# Driver for Bosch BME280 temperature, humidity, and pressure sensor
# Compatible with Raspberry Pi Pico W

from machine import I2C, Pin
import time
import struct

class BME280:
    """
    BME280 sensor driver for temperature, humidity, and pressure measurements.
    Uses I2C communication protocol.
    """
    
    # BME280 Register addresses
    REG_DIG_T1 = 0x88
    REG_DIG_H1 = 0xA1
    REG_DIG_H2 = 0xE1
    REG_CHIPID = 0xD0
    REG_VERSION = 0xD1
    REG_SOFTRESET = 0xE0
    REG_CONTROL_HUM = 0xF2
    REG_CONTROL = 0xF4
    REG_CONFIG = 0xF5
    REG_PRESSURE_DATA = 0xF7
    REG_TEMP_DATA = 0xFA
    REG_HUMIDITY_DATA = 0xFD
    
    # Oversampling settings
    OVERSAMPLE_X1 = 0x01
    OVERSAMPLE_X2 = 0x02
    OVERSAMPLE_X4 = 0x03
    OVERSAMPLE_X8 = 0x04
    OVERSAMPLE_X16 = 0x05
    
    # Operating modes
    MODE_SLEEP = 0x00
    MODE_FORCED = 0x01
    MODE_NORMAL = 0x03
    
    def __init__(self, i2c, addr=0x76):
        """
        Initialize BME280 sensor
        
        Args:
            i2c: machine.I2C object
            addr: I2C address (0x76 or 0x77)
        """
        self.i2c = i2c
        self.addr = addr
        
        # Check chip ID
        chip_id = self._read_byte(self.REG_CHIPID)
        if chip_id != 0x60:
            raise RuntimeError(f"BME280 not found. Chip ID: {chip_id:#x}, expected 0x60")
        
        # Load calibration data
        self._load_calibration()
        
        # Set default configuration
        self.set_mode(
            mode=self.MODE_NORMAL,
            temp_os=self.OVERSAMPLE_X2,
            hum_os=self.OVERSAMPLE_X1,
            press_os=self.OVERSAMPLE_X16
        )
        
        # Variables for compensated values
        self.t_fine = 0
        
    def _read_byte(self, reg):
        """Read a single byte from register"""
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
    
    def _read_bytes(self, reg, length):
        """Read multiple bytes from register"""
        return self.i2c.readfrom_mem(self.addr, reg, length)
    
    def _write_byte(self, reg, value):
        """Write a single byte to register"""
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))
    
    def _read_uint16_le(self, reg):
        """Read unsigned 16-bit little-endian value"""
        data = self._read_bytes(reg, 2)
        return struct.unpack('<H', data)[0]
    
    def _read_int16_le(self, reg):
        """Read signed 16-bit little-endian value"""
        data = self._read_bytes(reg, 2)
        return struct.unpack('<h', data)[0]
    
    def _load_calibration(self):
        """Load calibration coefficients from sensor"""
        # Temperature coefficients
        self.dig_T1 = self._read_uint16_le(self.REG_DIG_T1)
        self.dig_T2 = self._read_int16_le(self.REG_DIG_T1 + 2)
        self.dig_T3 = self._read_int16_le(self.REG_DIG_T1 + 4)
        
        # Pressure coefficients
        self.dig_P1 = self._read_uint16_le(self.REG_DIG_T1 + 6)
        self.dig_P2 = self._read_int16_le(self.REG_DIG_T1 + 8)
        self.dig_P3 = self._read_int16_le(self.REG_DIG_T1 + 10)
        self.dig_P4 = self._read_int16_le(self.REG_DIG_T1 + 12)
        self.dig_P5 = self._read_int16_le(self.REG_DIG_T1 + 14)
        self.dig_P6 = self._read_int16_le(self.REG_DIG_T1 + 16)
        self.dig_P7 = self._read_int16_le(self.REG_DIG_T1 + 18)
        self.dig_P8 = self._read_int16_le(self.REG_DIG_T1 + 20)
        self.dig_P9 = self._read_int16_le(self.REG_DIG_T1 + 22)
        
        # Humidity coefficients
        self.dig_H1 = self._read_byte(self.REG_DIG_H1)
        self.dig_H2 = self._read_int16_le(self.REG_DIG_H2)
        self.dig_H3 = self._read_byte(self.REG_DIG_H2 + 2)
        
        e4 = self._read_byte(self.REG_DIG_H2 + 3)
        e5 = self._read_byte(self.REG_DIG_H2 + 4)
        e6 = self._read_byte(self.REG_DIG_H2 + 5)
        
        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        if self.dig_H4 & 0x800:
            self.dig_H4 -= 4096
            
        self.dig_H5 = ((e5 >> 4) & 0x0F) | (e6 << 4)
        if self.dig_H5 & 0x800:
            self.dig_H5 -= 4096
            
        self.dig_H6 = self._read_byte(self.REG_DIG_H2 + 6)
        if self.dig_H6 > 127:
            self.dig_H6 -= 256
    
    def set_mode(self, mode=MODE_NORMAL, temp_os=OVERSAMPLE_X2, 
                 hum_os=OVERSAMPLE_X1, press_os=OVERSAMPLE_X16):
        """
        Set sensor operating mode and oversampling
        
        Args:
            mode: Operating mode (SLEEP, FORCED, NORMAL)
            temp_os: Temperature oversampling
            hum_os: Humidity oversampling
            press_os: Pressure oversampling
        """
        # Humidity oversampling must be set first
        self._write_byte(self.REG_CONTROL_HUM, hum_os)
        
        # Set temperature/pressure oversampling and mode
        ctrl_meas = (temp_os << 5) | (press_os << 2) | mode
        self._write_byte(self.REG_CONTROL, ctrl_meas)
        
        # Set config: standby time 1000ms, filter off
        self._write_byte(self.REG_CONFIG, 0xA0)
        
        # Wait for sensor to be ready
        time.sleep_ms(10)
    
    def _read_raw_data(self):
        """Read raw sensor data"""
        # Read all data registers at once (8 bytes)
        data = self._read_bytes(self.REG_PRESSURE_DATA, 8)
        
        press_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]
        
        return temp_raw, press_raw, hum_raw
    
    def _compensate_temperature(self, raw_temp):
        """Compensate temperature reading"""
        var1 = ((raw_temp / 16384.0) - (self.dig_T1 / 1024.0)) * self.dig_T2
        var2 = ((raw_temp / 131072.0) - (self.dig_T1 / 8192.0)) ** 2 * self.dig_T3
        self.t_fine = int(var1 + var2)
        return self.t_fine / 5120.0
    
    def _compensate_pressure(self, raw_press):
        """Compensate pressure reading"""
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        
        if var1 == 0:
            return 0
        
        press = 1048576.0 - raw_press
        press = ((press - var2 / 4096.0) * 6250.0) / var1
        var1 = self.dig_P9 * press * press / 2147483648.0
        var2 = press * self.dig_P8 / 32768.0
        press = press + (var1 + var2 + self.dig_P7) / 16.0
        
        return press / 100.0  # Convert Pa to hPa
    
    def _compensate_humidity(self, raw_hum):
        """Compensate humidity reading"""
        h = self.t_fine - 76800.0
        h = ((raw_hum - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * h)) *
             (self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * h *
             (1.0 + self.dig_H3 / 67108864.0 * h))))
        h = h * (1.0 - self.dig_H1 * h / 524288.0)
        
        if h > 100:
            h = 100
        elif h < 0:
            h = 0
            
        return h
    
    def read_compensated_data(self):
        """
        Read and compensate all sensor data
        
        Returns:
            tuple: (temperature_C, pressure_hPa, humidity_percent)
        """
        temp_raw, press_raw, hum_raw = self._read_raw_data()
        
        temperature = self._compensate_temperature(temp_raw)
        pressure = self._compensate_pressure(press_raw)
        humidity = self._compensate_humidity(hum_raw)
        
        return temperature, pressure, humidity
    
    def read_temperature(self):
        """Read temperature in Celsius"""
        temp, _, _ = self.read_compensated_data()
        return temp
    
    def read_pressure(self):
        """Read pressure in hPa"""
        _, press, _ = self.read_compensated_data()
        return press
    
    def read_humidity(self):
        """Read humidity in percent"""
        _, _, hum = self.read_compensated_data()
        return hum
    
    def calculate_altitude(self, pressure_hpa, sea_level_pressure=1013.25):
        """
        Calculate altitude from pressure
        
        Args:
            pressure_hpa: Current pressure in hPa
            sea_level_pressure: Sea level pressure in hPa (default: 1013.25)
            
        Returns:
            float: Altitude in meters
        """
        altitude = 44330.0 * (1.0 - (pressure_hpa / sea_level_pressure) ** 0.1903)
        return altitude
    
    def calculate_sea_level_pressure(self, altitude_m):
        """
        Calculate sea level pressure from current pressure and altitude
        
        Args:
            altitude_m: Station altitude in meters
            
        Returns:
            float: Sea level pressure in hPa
        """
        _, pressure, _ = self.read_compensated_data()
        sea_level = pressure / ((1.0 - (altitude_m / 44330.0)) ** 5.255)
        return sea_level
    
    def calculate_dew_point(self, temperature_c, humidity_percent):
        """
        Calculate dew point temperature
        
        Args:
            temperature_c: Temperature in Celsius
            humidity_percent: Relative humidity in percent
            
        Returns:
            float: Dew point in Celsius
        """
        a = 17.27
        b = 237.7
        
        alpha = ((a * temperature_c) / (b + temperature_c)) + (humidity_percent / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        
        return dew_point
    
    def soft_reset(self):
        """Perform soft reset of sensor"""
        self._write_byte(self.REG_SOFTRESET, 0xB6)
        time.sleep_ms(100)
        self._load_calibration()
