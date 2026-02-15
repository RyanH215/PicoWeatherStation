# hardware_sim.py - Hardware Simulation for Testing
# Simulates Raspberry Pi Pico W hardware for testing in standard Python environment

import time
import random

class SimulatedPin:
    """Simulates machine.Pin"""
    OUT = 1
    IN = 0
    
    def __init__(self, pin_num, mode=None):
        self.pin_num = pin_num
        self.mode = mode
        self.value_state = 0
        
    def on(self):
        self.value_state = 1
        print(f"[LED] Pin {self.pin_num} ON")
    
    def off(self):
        self.value_state = 0
        print(f"[LED] Pin {self.pin_num} OFF")
    
    def value(self, val=None):
        if val is not None:
            self.value_state = val
        return self.value_state


class SimulatedADC:
    """Simulates machine.ADC for battery voltage reading"""
    
    def __init__(self, pin):
        self.pin = pin
        # Simulate battery voltage around 3.7V (typical Li-ion)
        self.base_voltage = 3.7
        
    def read_u16(self):
        # Simulate voltage with small random variations
        voltage = self.base_voltage + random.uniform(-0.1, 0.1)
        # Convert to 16-bit ADC value
        # voltage = (adc_value / 65535) * 3.3 * 2 (voltage divider)
        # adc_value = voltage * 65535 / (3.3 * 2)
        adc_value = int((voltage / 2.0) * 65535 / 3.3)
        return adc_value


class SimulatedI2C:
    """Simulates machine.I2C for BME280 communication"""
    
    def __init__(self, bus, sda=None, scl=None, freq=400000):
        self.bus = bus
        self.sda = sda
        self.scl = scl
        self.freq = freq
        self.devices = [0x76]  # BME280 address
        
        # Simulated BME280 registers
        self.registers = {
            0xD0: 0x60,  # Chip ID
            0xF7: 0x50, 0xF8: 0x80, 0xF9: 0x00,  # Pressure
            0xFA: 0x80, 0xFB: 0x00, 0xFC: 0x00,  # Temperature
            0xFD: 0x70, 0xFE: 0x00,  # Humidity
        }
        
        # Store calibration data (simplified)
        self._init_calibration_data()
        
    def _init_calibration_data(self):
        """Initialize fake but realistic calibration data"""
        # These are typical values that will give reasonable readings
        calib_data = {
            # Temperature calibration
            0x88: 0x70, 0x89: 0x6B,  # dig_T1 = 27504
            0x8A: 0x43, 0x8B: 0x67,  # dig_T2 = 26435
            0x8C: 0x18, 0x8D: 0xFC,  # dig_T3 = -1000
            
            # Pressure calibration  
            0x8E: 0x5F, 0x8F: 0x8E,  # dig_P1 = 36447
            0x90: 0xAF, 0x91: 0xD6,  # dig_P2 = -10577
            0x92: 0x0B, 0x93: 0x30,  # dig_P3 = 3083
            0x94: 0x93, 0x95: 0x89,  # dig_P4 = -30317
            0x96: 0x04, 0x97: 0x00,  # dig_P5 = 4
            0x98: 0x08, 0x99: 0x00,  # dig_P6 = 8
            0x9A: 0x00, 0x9B: 0x00,  # dig_P7 = 0
            0x9C: 0x00, 0x9D: 0x00,  # dig_P8 = 0
            0x9E: 0x88, 0x9F: 0x00,  # dig_P9 = 136
            
            # Humidity calibration
            0xA1: 0x4B,  # dig_H1 = 75
            0xE1: 0x64, 0xE2: 0x01,  # dig_H2 = 356
            0xE3: 0x00,  # dig_H3 = 0
            0xE4: 0x10, 0xE5: 0x00, 0xE6: 0x1E,  # dig_H4, dig_H5
            0xE7: 0x1E,  # dig_H6 = 30
        }
        self.registers.update(calib_data)
    
    def scan(self):
        """Return list of I2C device addresses"""
        print(f"[I2C] Scanning bus {self.bus}...")
        return self.devices
    
    def readfrom_mem(self, addr, reg, length):
        """Read from device memory"""
        if addr not in self.devices:
            raise OSError(f"Device {hex(addr)} not found")
        
        # Special handling for sensor data registers
        if reg == 0xF7:  # Pressure/Temp/Humidity data burst read
            # Simulate realistic sensor readings
            # Temperature ~25°C, Pressure ~1013 hPa, Humidity ~50%
            temp_raw = 519888  # About 25°C
            press_raw = 329728  # About 1013 hPa
            hum_raw = 28672   # About 50%
            
            # Add some randomness
            temp_raw += random.randint(-1000, 1000)
            press_raw += random.randint(-500, 500)
            hum_raw += random.randint(-500, 500)
            
            # Pack into 8 bytes
            data = bytearray(8)
            data[0] = (press_raw >> 12) & 0xFF
            data[1] = (press_raw >> 4) & 0xFF
            data[2] = (press_raw << 4) & 0xF0
            data[3] = (temp_raw >> 12) & 0xFF
            data[4] = (temp_raw >> 4) & 0xFF
            data[5] = (temp_raw << 4) & 0xF0
            data[6] = (hum_raw >> 8) & 0xFF
            data[7] = hum_raw & 0xFF
            
            return bytes(data)
        
        # For other registers, return stored values
        result = bytearray(length)
        for i in range(length):
            result[i] = self.registers.get(reg + i, 0)
        return bytes(result)
    
    def writeto_mem(self, addr, reg, data):
        """Write to device memory"""
        if addr not in self.devices:
            raise OSError(f"Device {hex(addr)} not found")
        
        # Store written values
        if isinstance(data, (bytes, bytearray)):
            for i, byte in enumerate(data):
                self.registers[reg + i] = byte
        else:
            self.registers[reg] = data


class SimulatedWLAN:
    """Simulates network.WLAN"""
    STA_IF = 0
    
    def __init__(self, interface):
        self.interface = interface
        self.active_state = False
        self.connected = False
        self.ssid = None
        self.password = None
        
    def active(self, state=None):
        if state is not None:
            self.active_state = state
            if state:
                print("[WiFi] WLAN activated")
            else:
                print("[WiFi] WLAN deactivated")
        return self.active_state
    
    def connect(self, ssid, password):
        print(f"[WiFi] Connecting to '{ssid}'...")
        self.ssid = ssid
        self.password = password
        # Simulate connection delay
        time.sleep(1)
        self.connected = True
        print(f"[WiFi] Connected to '{ssid}'")
    
    def disconnect(self):
        if self.connected:
            print(f"[WiFi] Disconnected from '{self.ssid}'")
        self.connected = False
    
    def isconnected(self):
        return self.connected
    
    def ifconfig(self):
        if self.connected:
            return ('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8')
        return ('0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0')
    
    def status(self, param=None):
        if param == 'rssi':
            return random.randint(-75, -45)  # Signal strength
        return 3 if self.connected else 0


class SimulatedHTTPResponse:
    """Simulates HTTP response"""
    def __init__(self, status_code=200, text="OK"):
        self.status_code = status_code
        self.text = text
    
    def close(self):
        pass


# Simulated urequests module
class SimulatedRequests:
    """Simulates urequests module"""
    
    @staticmethod
    def get(url, **kwargs):
        print(f"[HTTP] GET {url}")
        # Simulate ThingSpeak response
        if 'thingspeak.com' in url:
            return SimulatedHTTPResponse(200, "1")  # Entry ID
        return SimulatedHTTPResponse(200, "OK")
    
    @staticmethod
    def post(url, **kwargs):
        print(f"[HTTP] POST {url}")
        if 'json' in kwargs:
            print(f"[HTTP] Data: {kwargs['json']}")
        return SimulatedHTTPResponse(201, '{"status":"success"}')


# Create machine module simulation
class machine:
    """Simulated machine module"""
    Pin = SimulatedPin
    ADC = SimulatedADC
    I2C = SimulatedI2C
    
    @staticmethod
    def lightsleep(duration_ms):
        print(f"[POWER] Entering light sleep for {duration_ms}ms")
        # Don't actually sleep in simulation
        # time.sleep(duration_ms / 1000.0)


# Create network module simulation
class network:
    """Simulated network module"""
    WLAN = SimulatedWLAN
    STA_IF = SimulatedWLAN.STA_IF


# Simulated urequests
urequests = SimulatedRequests


# Helper to check if we're in simulation mode
def is_simulation():
    return True


print("[SIM] Hardware simulation loaded")
print("[SIM] Use 'from hardware_sim import machine, network, urequests' in your code")

