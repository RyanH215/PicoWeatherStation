# main.py - Weather Station Main Program
# Raspberry Pi Pico W Weather Station
# Measures temperature, humidity, and pressure with BME280
# Solar powered with battery monitoring
# WiFi data transmission

from machine import I2C, Pin, lightsleep
import time
import config
from bme280 import BME280
from power import PowerManager
from wifi_manager import WifiManager

class WeatherStation:
    """
    Main weather station controller
    Orchestrates sensor readings, power management, and data transmission
    """
    
    def __init__(self):
        """Initialize weather station components"""
        print("="*50)
        print("Weather Station Initializing...")
        print("="*50)
        
        # Status LED (optional)
        if config.USE_STATUS_LED:
            self.led = Pin(config.STATUS_LED_PIN, Pin.OUT)
            self.blink_led(times=3, delay=0.2)
        else:
            self.led = None
            
        #Initialize I2C for BME280
        print("Initializing I2C...")
        self.i2c = I2C(
            config.BME280_I2C_BUS,
            sda=Pin(config.BME280_SDA_PIN),
            scl=Pin(config.BME280_SCL_PIN),
            freq-config.BME280_I2C_FREQ
            )
        
        # Scan I2C bus
        devices = self.i2c.scab()
        if devices:
            print(f"I2C devices found: {[hex(d) for d in devices]}")
        else
            print("WARNING: No I2C devices found!")
        
        # Initialize BME280 senor
        print("Initializing BME280 sensor...")
        try:
            self.bme = BME280(self.i2c, addr=config.BME280_I2C_ADDR)
            print("BME280 initialized successfully")
        except Exception as e:
            print(f"ERROR: Failed to initialize BME280: {e}")
            self.bme = None
        
        # Initialize power mangera
        print("Initializing power manager...")
        self.power_manager = PowerManager()
        
        # Initialize WiFi manager
        print("Initializing WiFi manager...")
        self.wif_manager = WifiManager()
        
        # Counters and state
        self.reading_count = 0
        self.error_count = 0
        self.last_read_time = 0
        self.startup_time = time.time()
        
        # Connect to Wifi on startup
        if self.wifi_manager.connect():
            # Sync time with NTP
            if config.SYNC_TIME_ON_BOOT:
                self.wifi_manager.sync_time_ntp()
            # Disconnect to save power (will reconnect when needed)
            if config.USE_DEEP_SLEEP:
                self.wifi.manager.disconnect()
                
        print("="*50)
        print("Initialization Complete!")
        print("="*50)
        self.print_config()
    
    def blink_led(self, times=1, delay=0.5):
        """Blink status LED"""
        if self.led:
            for _ in range(times):
                self.led.on()
                time.sleep(delay)
                self.led.off()
                time.sleep(delay)
                
    def print_config(self):
        """Print current configuration"""
        print("\nConfiguration:")
        print(f"  Station: {config.STATION_NAME}")
        print(f"  Location: {config.STATION_LOCATION}")
        print(f"  Read interval: {config.SENSOR_READ_INTERVAL}s")
        print(f"  Deep sleep: {config.USE_DEEP_SLEEP}")
        print(f"  Transmission: ", end="")
        if config.USE_THINGSPEAK:
            print("ThingSpeak")
        elif config.USE_HTTP_POST:
            print("HTTP POST")
        else:
            print("None configured")
        print()
    
    def read_sensors(self):
        """
        Read all sensors and return data
        
        Returns:
            dict: Sensor readings or None if error
        """
        if not self.bme:
            print("ERROR: BME280 not initialized")
            return None
        
        try:
            # Read BME280 data
            temperature, pressure, humidity = self.bme.read_compensated_data()
            
            # Apply calibration offsets
            temperature += config.TEMP_OFFSET
            humidity += config.HUMIDITY_OFFSET
            pressure += config.PRESSURE_OFFSET
            
            # Calculate derived values
            dew_point = self.bme.calculate_dew_point(temperature, humidity)
            sea_level_pressure = self.bme.calculate_sea_level_pressure(config.STATION_ELEVATION)
            
            # Read battery status
            battery_status = self.power_manager.get_battery_status()
            
            # Compile data
            data = {
                'temperature': round(temperature, 2),
                'humidity': round(humidity, 1),
                'pressure': round(pressure, 2),
                'dew_point': round(dew_point, 2),
                'sea_level_pressure': round(sea_level_pressure, 2),
                'battery_voltage': round(battery_status['voltage'], 2),
                'battery_percent': round(battery_status['percentage'], 1),
                'battery_state': battery_status['state'],
                'reading_count': self.reading_count,
                'error_count': self.error_count,
                'uptime': int(time.time() - self.startup_time)
            }
            
            self.reading_count += 1
            self.last_read_time = time.time()
            
            return data
            
        except Exception as e:
            print(f"ERROR reading sensors: {e}")
            self.error_count += 1
            return None
    
    def print_readings(self, data):
        """Print sensor readings to console"""
        if not data:
            return
        
        print("\n" + "="*50)
        print(f"Reading #{data['reading_count']} - {time.localtime()}")
        print("="*50)
        print(f"Temperature:      {data['temperature']:.2f}°C")
        print(f"Humidity:         {data['humidity']:.1f}%")
        print(f"Pressure:         {data['pressure']:.2f} hPa")
        print(f"Dew Point:        {data['dew_point']:.2f}°C")
        print(f"Sea Level Press:  {data['sea_level_pressure']:.2f} hPa")
        print("-"*50)
        print(f"Battery Voltage:  {data['battery_voltage']:.2f}V")
        print(f"Battery Level:    {data['battery_percent']:.1f}%")
        print(f"Battery State:    {data['battery_state']}")
        print("-"*50)
        print(f"Uptime:           {data['uptime']}s")
        print(f"Errors:           {data['error_count']}")
        print("="*50 + "\n")
    
    def transmit_data(self, data):
        """
        Transmit data via WiFi
        
        Args:
            data: Dictionary with sensor readings
            
        Returns:
            bool: True if successful
        """
        if not data:
            return False
        
        try:
            # Blink LED during transmission
            if self.led:
                self.led.on()
            
            # Send data
            success = self.wifi_manager.send_data(data)
            
            if self.led:
                self.led.off()
            
            return success
            
        except Exception as e:
            print(f"ERROR transmitting data: {e}")
            if self.led:
                self.led.off()
            return False
    
    def enter_sleep(self, duration_ms):
        """
        Enter low power sleep mode
        
        Args:
            duration_ms: Sleep duration in milliseconds
        """
        if config.DEBUG_MODE:
            print(f"Entering sleep for {duration_ms/1000:.1f} seconds...")
        
        # Ensure WiFi is disconnected
        self.wifi_manager.disconnect()
        
        # Turn off LED
        if self.led:
            self.led.off()
        
        # Enter light sleep (deep sleep would reset the device)
        lightsleep(duration_ms)
        
        if config.DEBUG_MODE:
            print("Woke up from sleep")
    
    def run_once(self):
        """
        Single iteration of sensor reading and data transmission
        Used for testing or when not using sleep mode
        """
        # Blink LED to show activity
        self.blink_led(times=1, delay=0.1)
        
        # Read sensors
        print("\nReading sensors...")
        data = self.read_sensors()
        
        if data:
            # Print readings
            self.print_readings(data)
            
            # Check battery status
            if self.power_manager.is_critical_battery:
                print("WARNING: Critical battery level!")
            
            # Transmit data
            print("Transmitting data...")
            if self.transmit_data(data):
                print("Data transmitted successfully!")
            else:
                print("Data transmission failed (data buffered)")
        else:
            print("Failed to read sensors")
            self.error_count += 1
        
        return data
    
    def run_continuous(self):
        """
        Main continuous operation loop
        Reads sensors, transmits data, and sleeps according to configuration
        """
        print("\nStarting continuous operation...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Run one iteration
                data = self.run_once()
                
                # Determine sleep time based on battery level
                sleep_seconds = self.power_manager.get_suggested_sleep_time()
                
                # Check if we should continue or handle errors
                if self.error_count >= config.MAX_SENSOR_READ_FAILURES:
                    print(f"ERROR: Too many sensor failures ({self.error_count})")
                    print("Attempting sensor reset...")
                    try:
                        self.bme.soft_reset()
                        self.error_count = 0
                    except:
                        print("Sensor reset failed. Sleeping for extended period...")
                        sleep_seconds *= 2
                
                # Sleep until next reading
                if config.USE_DEEP_SLEEP:
                    self.enter_sleep(sleep_seconds * 1000)
                else:
                    print(f"\nWaiting {sleep_seconds} seconds until next reading...")
                    time.sleep(sleep_seconds)
                    
        except KeyboardInterrupt:
            print("\n\nShutdown requested...")
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown procedure"""
        print("Shutting down weather station...")
        
        # Try to transmit any buffered data
        if self.wifi_manager.data_buffer:
            print("Attempting to send buffered data...")
            self.wifi_manager.transmit_buffered_data()
        
        # Disconnect WiFi
        self.wifi_manager.disconnect()
        
        # Turn off LED
        if self.led:
            self.led.off()
        
        print("Shutdown complete")
    
    def run_diagnostics(self):
        """Run diagnostic tests on all components"""
        print("\n" + "="*50)
        print("Running Diagnostics")
        print("="*50)
        
        # Test BME280
        print("\n1. BME280 Sensor Test:")
        if self.bme:
            try:
                temp, press, hum = self.bme.read_compensated_data()
                print(f"   ✓ Temperature: {temp:.2f}°C")
                print(f"   ✓ Pressure: {press:.2f} hPa")
                print(f"   ✓ Humidity: {hum:.1f}%")
            except Exception as e:
                print(f"   ✗ Error: {e}")
        else:
            print("   ✗ Sensor not initialized")
        
        # Test Power Manager
        print("\n2. Power Manager Test:")
        try:
            self.power_manager.print_status()
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test WiFi
        print("\n3. WiFi Test:")
        try:
            if self.wifi_manager.connect():
                self.wifi_manager.print_status()
                signal = self.wifi_manager.get_signal_strength()
                if signal:
                    print(f"   Signal Quality: {signal} dBm")
                self.wifi_manager.disconnect()
            else:
                print("   ✗ Connection failed")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print("\n" + "="*50)
        print("Diagnostics Complete")
        print("="*50 + "\n")


def main():
    """Main entry point"""
    try:
        # Create weather station instance
        station = WeatherStation()
        
        # Run diagnostics if in debug mode
        if config.DEBUG_MODE:
            station.run_diagnostics()
        
        # Start continuous operation
        station.run_continuous()
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        print("System halted")


if __name__ == "__main__":
    main()
