# power.py - Power Management Module
# Battery monitoring and power management for solar-powered weather station

from machine import ADC, Pin
import time
import config

class PowerManager:
    """
    Power management system for battery monitoring and power control
    Monitors battery voltage and manages power states
    """
    
    def __init__(self, adc_pin=config.BATTERY_ADC_PIN):
        """
        Initialize power manager
        
        Args:
            adc_pin: GPIO pin number for battery voltage monitoring (ADC capable)
        """
        self.adc = ADC(Pin(adc_pin))
        self.voltage_divider_ratio = config.BATTERY_VOLTAGE_DIVIDER_RATIO
        self.vref = config.VREF
        
        # Voltage thresholds
        self.low_voltage = config.BATTERY_LOW_VOLTAGE
        self.critical_voltage = config.BATTERY_CRITICAL_VOLTAGE
        self.full_voltage = config.BATTERY_FULL_VOLTAGE
        
        # Battery state
        self.current_voltage = 0.0
        self.battery_percentage = 0.0
        self.is_low_battery = False
        self.is_critical_battery = False
        
        # Calibration factor (adjust after measuring with multimeter)
        self.calibration_factor = 1.0
        
        # Moving average for stable readings
        self.voltage_samples = []
        self.max_samples = 10
        
    def read_raw_adc(self):
        """
        Read raw ADC value
        
        Returns:
            int: Raw ADC value (0-65535 for Pico's 16-bit ADC)
        """
        return self.adc.read_u16()
    
    def read_battery_voltage(self, averaged=True):
        """
        Read battery voltage
        
        Args:
            averaged: Use moving average for stable readings
            
        Returns:
            float: Battery voltage in volts
        """
        # Read raw ADC value (16-bit: 0-65535)
        raw_value = self.read_raw_adc()
        
        # Convert to voltage
        # voltage = (raw_value / 65535) * VREF * voltage_divider_ratio * calibration
        voltage = (raw_value / 65535.0) * self.vref * self.voltage_divider_ratio * self.calibration_factor
        
        if averaged:
            # Add to moving average
            self.voltage_samples.append(voltage)
            if len(self.voltage_samples) > self.max_samples:
                self.voltage_samples.pop(0)
            
            # Calculate average
            voltage = sum(self.voltage_samples) / len(self.voltage_samples)
        
        self.current_voltage = voltage
        return voltage
    
    def get_battery_percentage(self):
        """
        Calculate battery percentage based on voltage
        Uses simple linear interpolation between critical and full voltage
        
        Returns:
            float: Battery percentage (0-100)
        """
        voltage = self.read_battery_voltage()
        
        # Linear interpolation between critical and full voltage
        if voltage >= self.full_voltage:
            percentage = 100.0
        elif voltage <= self.critical_voltage:
            percentage = 0.0
        else:
            voltage_range = self.full_voltage - self.critical_voltage
            voltage_above_critical = voltage - self.critical_voltage
            percentage = (voltage_above_critical / voltage_range) * 100.0
        
        self.battery_percentage = percentage
        return percentage
    
    def get_battery_status(self):
        """
        Get comprehensive battery status
        
        Returns:
            dict: Battery status information
        """
        voltage = self.read_battery_voltage()
        percentage = self.get_battery_percentage()
        
        # Determine battery state
        if voltage <= self.critical_voltage:
            state = "CRITICAL"
            self.is_critical_battery = True
            self.is_low_battery = True
        elif voltage <= self.low_voltage:
            state = "LOW"
            self.is_low_battery = True
            self.is_critical_battery = False
        elif voltage >= self.full_voltage * 0.95:  # Within 5% of full
            state = "FULL"
            self.is_low_battery = False
            self.is_critical_battery = False
        else:
            state = "NORMAL"
            self.is_low_battery = False
            self.is_critical_battery = False
        
        return {
            'voltage': voltage,
            'percentage': percentage,
            'state': state,
            'is_low': self.is_low_battery,
            'is_critical': self.is_critical_battery
        }
    
    def is_battery_ok(self):
        """
        Check if battery is above critical level
        
        Returns:
            bool: True if battery is OK, False if critical
        """
        voltage = self.read_battery_voltage()
        return voltage > self.critical_voltage
    
    def should_enter_low_power(self):
        """
        Determine if system should enter low power mode
        
        Returns:
            bool: True if should enter low power mode
        """
        return self.is_low_battery
    
    def get_suggested_sleep_time(self):
        """
        Get suggested sleep time based on battery level
        Lower battery = longer sleep time to conserve power
        
        Returns:
            int: Suggested sleep time in seconds
        """
        percentage = self.get_battery_percentage()
        base_interval = config.SENSOR_READ_INTERVAL
        
        if self.is_critical_battery:
            # Critical: sleep 4x longer
            return base_interval * 4
        elif self.is_low_battery:
            # Low: sleep 2x longer
            return base_interval * 2
        else:
            # Normal: use configured interval
            return base_interval
    
    def calibrate(self, actual_voltage):
        """
        Calibrate voltage reading with actual measured voltage
        Measure battery voltage with multimeter and call this function
        
        Args:
            actual_voltage: Actual voltage measured with multimeter
        """
        measured_voltage = self.read_battery_voltage(averaged=False)
        if measured_voltage > 0:
            self.calibration_factor = actual_voltage / measured_voltage
            print(f"Calibration factor set to: {self.calibration_factor:.4f}")
            return self.calibration_factor
        else:
            print("Error: Measured voltage is 0")
            return None
    
    def print_status(self):
        """Print battery status to console"""
        status = self.get_battery_status()
        print("="*40)
        print("Battery Status:")
        print(f"  Voltage:    {status['voltage']:.2f}V")
        print(f"  Percentage: {status['percentage']:.1f}%")
        print(f"  State:      {status['state']}")
        print(f"  Low Battery: {status['is_low']}")
        print(f"  Critical:    {status['is_critical']}")
        print("="*40)
    
    def monitor_loop(self, interval=5):
        """
        Continuous monitoring loop for testing
        
        Args:
            interval: Time between readings in seconds
        """
        print("Starting battery monitoring... (Ctrl+C to stop)")
        try:
            while True:
                self.print_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")


# Standalone test function
def test_power_manager():
    """Test power manager functionality"""
    print("Initializing Power Manager...")
    pm = PowerManager()
    
    print("\nReading battery voltage...")
    for i in range(5):
        voltage = pm.read_battery_voltage()
        print(f"Reading {i+1}: {voltage:.3f}V")
        time.sleep(1)
    
    print("\nBattery Status:")
    pm.print_status()
    
    print("\nSuggested sleep time:", pm.get_suggested_sleep_time(), "seconds")
    
    # Uncomment below to run continuous monitoring
    # pm.monitor_loop(interval=5)


if __name__ == "__main__":
    test_power_manager()
