"""Constants for Big Blue integration."""

DOMAIN = "bigblue"

# API Configuration
API_BASE_URL = "http://www.powafree.com"  # Using HTTP (port 80) instead of HTTPS (port 443)
API_TIMEOUT = 30

# Default values
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1

# Modbus registers for Big Blue battery
# These will need to be updated based on actual Big Blue documentation
REGISTER_BATTERY_VOLTAGE = 0x1000
REGISTER_BATTERY_CURRENT = 0x1001
REGISTER_BATTERY_SOC = 0x1002
REGISTER_BATTERY_TEMPERATURE = 0x1003
REGISTER_BATTERY_STATUS = 0x1004
REGISTER_BATTERY_CAPACITY = 0x1005

# Sensor names
SENSOR_VOLTAGE = "voltage"
SENSOR_CURRENT = "current"
SENSOR_SOC = "state_of_charge"
SENSOR_TEMPERATURE = "temperature"
SENSOR_STATUS = "status"
SENSOR_CAPACITY = "capacity"
