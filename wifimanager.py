# wifi_manager.py - WiFi Management Module
# WiFi connection management and data transmission for weather station

import network
import time
import urequests
import json
import config

class WiFiManager:
    """
    WiFi connection manager and data transmission handler
    Supports multiple data transmission methods: ThingSpeak, MQTT, HTTP POST
    """
    
    def __init__(self):
        """Initialize WiFi manager"""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        self.is_connected = False
        self.connection_attempts = 0
        self.last_connection_time = 0
        self.failed_transmissions = 0
        
        # Data buffer for offline storage
        self.data_buffer = []
        
    def connect(self, ssid=None, password=None, timeout=None):
        """
        Connect to WiFi network
        
        Args:
            ssid: WiFi SSID (uses config if None)
            password: WiFi password (uses config if None)
            timeout: Connection timeout in seconds (uses config if None)
            
        Returns:
            bool: True if connected, False otherwise
        """
        if ssid is None:
            ssid = config.WIFI_SSID
        if password is None:
            password = config.WIFI_PASSWORD
        if timeout is None:
            timeout = config.WIFI_TIMEOUT
        
        # Check if already connected
        if self.wlan.isconnected():
            self.is_connected = True
            if config.DEBUG_MODE:
                print("Already connected to WiFi")
            return True
        
        if config.DEBUG_MODE:
            print(f"Connecting to WiFi: {ssid}")
        
        # Start connection
        self.wlan.connect(ssid, password)
        
        # Wait for connection
        start_time = time.time()
        while not self.wlan.isconnected():
            if time.time() - start_time > timeout:
                if config.DEBUG_MODE:
                    print("WiFi connection timeout")
                self.is_connected = False
                self.connection_attempts += 1
                return False
            
            time.sleep(0.5)
            if config.DEBUG_MODE and int(time.time() - start_time) % 5 == 0:
                print(".", end="")
        
        # Connection successful
        self.is_connected = True
        self.last_connection_time = time.time()
        self.connection_attempts = 0
        
        if config.DEBUG_MODE:
            print(f"\nConnected! IP: {self.wlan.ifconfig()[0]}")
            
        return True
    
    def disconnect(self):
        """Disconnect from WiFi to save power"""
        if self.wlan.isconnected():
            self.wlan.disconnect()
            if config.DEBUG_MODE:
                print("Disconnected from WiFi")
        self.wlan.active(False)
        self.is_connected = False
    
    def reconnect(self):
        """Attempt to reconnect to WiFi"""
        if not self.is_connected:
            return self.connect()
        return True
    
    def get_connection_info(self):
        """
        Get WiFi connection information
        
        Returns:
            dict: Connection information
        """
        if self.wlan.isconnected():
            ifconfig = self.wlan.ifconfig()
            return {
                'connected': True,
                'ip': ifconfig[0],
                'subnet': ifconfig[1],
                'gateway': ifconfig[2],
                'dns': ifconfig[3],
                'rssi': self.wlan.status('rssi') if hasattr(self.wlan, 'status') else None
            }
        else:
            return {'connected': False}
    
    def send_to_thingspeak(self, data):
        """
        Send data to ThingSpeak
        
        Args:
            data: Dictionary with sensor data
                  Keys should match: temp, humidity, pressure, etc.
                  
        Returns:
            bool: True if successful, False otherwise
        """
        if not config.USE_THINGSPEAK:
            return False
        
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            # Build ThingSpeak URL with parameters
            url = f"{config.THINGSPEAK_URL}?api_key={config.THINGSPEAK_API_KEY}"
            
            # Map data to ThingSpeak fields
            # Adjust field numbers based on your ThingSpeak channel setup
            if 'temperature' in data:
                url += f"&field1={data['temperature']:.2f}"
            if 'humidity' in data:
                url += f"&field2={data['humidity']:.2f}"
            if 'pressure' in data:
                url += f"&field3={data['pressure']:.2f}"
            if 'battery_voltage' in data:
                url += f"&field4={data['battery_voltage']:.2f}"
            if 'battery_percent' in data:
                url += f"&field5={data['battery_percent']:.1f}"
            
            # Add status message if present
            if 'status' in data:
                url += f"&status={data['status']}"
            
            if config.DEBUG_MODE:
                print(f"Sending to ThingSpeak...")
            
            # Send GET request
            response = urequests.get(url)
            
            if response.status_code == 200:
                entry_id = response.text.strip()
                if config.DEBUG_MODE:
                    print(f"ThingSpeak entry ID: {entry_id}")
                response.close()
                self.failed_transmissions = 0
                return True
            else:
                if config.DEBUG_MODE:
                    print(f"ThingSpeak error: {response.status_code}")
                response.close()
                self.failed_transmissions += 1
                return False
                
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"ThingSpeak transmission error: {e}")
            self.failed_transmissions += 1
            return False
    
    def send_http_post(self, data):
        """
        Send data via HTTP POST to custom server
        
        Args:
            data: Dictionary with sensor data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not config.USE_HTTP_POST:
            return False
        
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {config.HTTP_POST_API_KEY}'
            }
            
            # Add timestamp and station info
            payload = {
                'station_name': config.STATION_NAME,
                'location': config.STATION_LOCATION,
                'timestamp': time.time(),
                'data': data
            }
            
            if config.DEBUG_MODE:
                print(f"Sending HTTP POST to {config.HTTP_POST_URL}")
            
            response = urequests.post(
                config.HTTP_POST_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                if config.DEBUG_MODE:
                    print(f"HTTP POST successful: {response.text}")
                response.close()
                self.failed_transmissions = 0
                return True
            else:
                if config.DEBUG_MODE:
                    print(f"HTTP POST error: {response.status_code}")
                response.close()
                self.failed_transmissions += 1
                return False
                
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"HTTP POST error: {e}")
            self.failed_transmissions += 1
            return False
    
    def buffer_data(self, data):
        """
        Buffer data locally when transmission fails
        
        Args:
            data: Dictionary with sensor data
        """
        timestamp = time.time()
        buffered_entry = {
            'timestamp': timestamp,
            'data': data
        }
        
        self.data_buffer.append(buffered_entry)
        
        # Limit buffer size
        if len(self.data_buffer) > config.DATA_BUFFER_SIZE:
            self.data_buffer.pop(0)  # Remove oldest entry
        
        if config.DEBUG_MODE:
            print(f"Data buffered. Buffer size: {len(self.data_buffer)}")
    
    def transmit_buffered_data(self):
        """
        Attempt to transmit all buffered data
        
        Returns:
            int: Number of successfully transmitted entries
        """
        if not self.data_buffer:
            return 0
        
        if not self.is_connected:
            if not self.connect():
                return 0
        
        transmitted_count = 0
        failed_entries = []
        
        if config.DEBUG_MODE:
            print(f"Transmitting {len(self.data_buffer)} buffered entries...")
        
        for entry in self.data_buffer:
            success = False
            
            if config.USE_THINGSPEAK:
                success = self.send_to_thingspeak(entry['data'])
            elif config.USE_HTTP_POST:
                success = self.send_http_post(entry['data'])
            
            if success:
                transmitted_count += 1
            else:
                failed_entries.append(entry)
            
            # Small delay between transmissions
            time.sleep(1)
        
        # Keep only failed entries in buffer
        self.data_buffer = failed_entries
        
        if config.DEBUG_MODE:
            print(f"Transmitted {transmitted_count} entries. {len(self.data_buffer)} remaining.")
        
        return transmitted_count
    
    def send_data(self, data):
        """
        Send data using configured method
        Automatically buffers data if transmission fails
        
        Args:
            data: Dictionary with sensor data
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = False
        
        # Try to transmit any buffered data first
        if self.data_buffer:
            self.transmit_buffered_data()
        
        # Send current data
        if config.USE_THINGSPEAK:
            success = self.send_to_thingspeak(data)
        elif config.USE_HTTP_POST:
            success = self.send_http_post(data)
        
        # Buffer data if transmission failed
        if not success:
            self.buffer_data(data)
        
        return success
    
    def sync_time_ntp(self):
        """
        Synchronize time with NTP server
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            import ntptime
            if config.DEBUG_MODE:
                print("Syncing time with NTP server...")
            
            ntptime.host = config.NTP_SERVER
            ntptime.settime()
            
            if config.DEBUG_MODE:
                print("Time synchronized successfully")
            return True
            
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"NTP sync error: {e}")
            return False
    
    def get_signal_strength(self):
        """
        Get WiFi signal strength
        
        Returns:
            int: RSSI value (signal strength in dBm)
        """
        if self.wlan.isconnected():
            try:
                return self.wlan.status('rssi')
            except:
                return None
        return None
    
    def print_status(self):
        """Print WiFi status to console"""
        print("="*40)
        print("WiFi Status:")
        info = self.get_connection_info()
        if info['connected']:
            print(f"  Connected: Yes")
            print(f"  IP Address: {info['ip']}")
            print(f"  Gateway: {info['gateway']}")
            rssi = self.get_signal_strength()
            if rssi:
                print(f"  Signal: {rssi} dBm")
        else:
            print(f"  Connected: No")
        print(f"  Buffered entries: {len(self.data_buffer)}")
        print(f"  Failed transmissions: {self.failed_transmissions}")
        print("="*40)


# Standalone test function
def test_wifi_manager():
    """Test WiFi manager functionality"""
    print("Initializing WiFi Manager...")
    wm = WiFiManager()
    
    print("\nConnecting to WiFi...")
    if wm.connect():
        wm.print_status()
        
        # Test NTP sync
        if config.SYNC_TIME_ON_BOOT:
            wm.sync_time_ntp()
        
        # Test data transmission
        test_data = {
            'temperature': 25.5,
            'humidity': 60.0,
            'pressure': 1013.25,
            'battery_voltage': 3.8,
            'battery_percent': 75.0
        }
        
        print("\nTesting data transmission...")
        if wm.send_data(test_data):
            print("Data sent successfully!")
        else:
            print("Data transmission failed (buffered)")
        
        wm.disconnect()
    else:
        print("WiFi connection failed")


if __name__ == "__main__":
    test_wifi_manager()
