# status_visualization.py

import sys
import math
import json
import paho.mqtt.client as mqtt

from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QFont

'''
def get_mqtt_config():
    settings = {'mqtt_broker_address': "localhost", 'mqtt_port': 1883}
    broker = settings['mqtt_broker_address']
    port = settings['mqtt_port']
    return {"broker": broker, "port": port}
'''

class StatusVisualization(QWidget):
    update_drone_received = Signal(dict)

    def __init__(self, drone_id):
        super().__init__()
        self.drone_id = drone_id

        self.initUI()

        # Connect signals to slots
        # self.update_drone_received.connect(self.update_status_received)

        # self.setup_mqtt()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Create the QTextEdit for displaying status
        self.text_widget = QTextEdit(self)
        self.text_widget.setReadOnly(True)
        # Make the font smaller
        self.text_widget.setFont(QFont('Arial', 8))
        self.text_widget.setHtml("<p style='text-align:center; font-size:14px;'>Waiting for data</p>")
        self.layout.addWidget(self.text_widget)

    @Slot(dict)
    def update_status_received(self, drone_id, data):
        if drone_id != self.drone_id:
            return

        formatted_data = self.formatData(data)
        self.text_widget.setHtml(formatted_data)

    def get_drone_color(self, drone_id):
        # Map drone IDs to colors
        UAV_COLOR_MAP = {
            "Orange": "#FFA500",
            "Blue": "#0000FF",
            "Red": "#FF0000",
            "Lime": "#00FF00",
            "Aqua": "#00FFFF",
            "Violet": "#EE82EE",
            "Fuchsia": "#FF00FF",
            "Gold": "#FFD700",
            "DodgerBlue": "#1E90FF",
            "Black": "#000000"
        }
        return UAV_COLOR_MAP.get(drone_id, "#000000")

    def formatData(self, data):
        # Format the data into HTML
        uavid = data.get('uavid', 'N/A')
        color = self.get_drone_color(uavid)
        status = data.get('status', {})
        if not status:
            return ''
        # Formatting latitude, longitude, and altitude with 3 decimal places
        try:
            speed = f"{(float(status.get('speed', '0'))*2.237):.3f}"  # converts m/s to mph
        except (TypeError, ValueError):
            speed = "N/A"
        try:
            latitude = f"{float(status.get('location', {}).get('latitude', 0)):.5f}"
            longitude = f"{float(status.get('location', {}).get('longitude', 0)):.5f}"
            altitude = f"{float(status.get('location', {}).get('altitude', 0)):.3f}"
        except (TypeError, ValueError):
            latitude = longitude = altitude = "N/A"
        # Drone Heading
        try:
            radians = float(status.get('drone_heading', '0')) % (2 * math.pi)  # Normalize radians between 0 and 2π
            directions = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"]
            sector_size = 2 * math.pi / len(directions)  # Divide 360 degrees into 8 sectors
            dir_index = int((radians + sector_size / 2) // sector_size) % len(directions)
            drone_heading = directions[dir_index]
        except (TypeError, ValueError):
            drone_heading = "N/A"

        try:
            battery_voltage = f"{float(status.get('battery', {}).get('voltage', 0)):.2f}"
        except (TypeError, ValueError):
            battery_voltage = "N/A"
        try:
            battery_level = int(float(status.get('battery', {}).get('level', '0'))*100)
        except (TypeError, ValueError):
            battery_level = "N/A"

        formatted_text = f"""
            <h1 style="text-align: center; color: {color}; margin: 0;">{uavid}</h1>
            <p style="font-size: 20px; line-height: 20px;"><b>Status:</b> {status.get('status', 'N/A')}<br>
            <b>Mode:</b> {status.get('mode', 'N/A')}<br>
            <b>Onboard Pilot:</b> {status.get('onboard_pilot', 'N/A')}<br><br>
            <b>Armed:</b> {status.get('armed', 'N/A')}<br>
            <b>Geofence:</b> {status.get('geofence', 'N/A')}<br><br>
            <b>LAT:</b> {latitude}
            &nbsp;&nbsp;&nbsp;&nbsp;<b>LON:</b> {longitude}<br>
            <b>ALT:</b> {altitude}<br><br>
            <b>Speed:</b> {speed} mph<br>
            <b>Drone Heading:</b> {drone_heading}<br><br>
            <b>Battery Voltage:</b> {battery_voltage} V
            &nbsp;&nbsp;&nbsp;&nbsp;<b>Current:</b> {status.get('battery', {}).get('current', 'N/A')} A<br>
            <b>Battery Level:</b> {battery_level}%</p>
            """

        return formatted_text
    '''
    def setup_mqtt(self):
        # Create MQTT client and set up callbacks
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        mqtt_config = get_mqtt_config()
        self.client.connect(mqtt_config["broker"], mqtt_config["port"])
        # Start the loop in a separate thread
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            # Subscribe to update_drone topic
            self.client.subscribe("update_drone")
        else:
            pass

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode('utf-8')

        if topic == "update_drone":
            # Parse the update_drone message and emit signal
            try:
                update = json.loads(payload)
                if update.get('uavid') == self.drone_id:
                    self.update_drone_received.emit(update)
            except json.JSONDecodeError:
                pass

    def closeEvent(self, event):
        # Stop MQTT client loop when closing the application
        self.client.loop_stop()
        self.client.disconnect()
        event.accept()
    '''