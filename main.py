# main.py

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PySide6.QtCore import Signal, Slot
import sys
import paho.mqtt.client as mqtt
import json
from drone_widget import DroneWidget

def get_mqtt_config():
    settings = {'mqtt_broker_address': "localhost", 'mqtt_port': 1883}
    broker = settings['mqtt_broker_address']
    port = settings['mqtt_port']
    return {"broker": broker, "port": port}

class MainWindow(QMainWindow):
    drone_data_received = Signal(str)
    mission_spec_received = Signal(str, dict)  # Signal for mission-spec (drone_id, data)
    update_drone_received = Signal(str, dict)  # Signal for update_drone (drone_id, data)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Application")
        # List of all possible drone IDs/colors
        self.all_drone_ids = ["Red", "Lime", "Aqua", "Gold", "DodgerBlue", "Orange", "Violet", "Fuchsia"]
        self.drone_widgets = {}  # Map from drone_id to DroneWidget
        self.initUI()
        self.setup_mqtt()

        self.drone_data_received.connect(self.handle_drone_data_received)

    def initUI(self):
        # Create the central widget and set it as the main window's central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create the grid layout
        self.grid_layout = QGridLayout()
        self.central_widget.setLayout(self.grid_layout)

        # Initialize empty grid cells (2 rows x 3 columns)
        self.rows = 2
        self.columns = 3
        self.cell_positions = {}  # Map from drone_id to column

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
            # Subscribe to update_drone topic to detect active drones
            self.client.subscribe("update_drone")
            for drone_id in self.all_drone_ids:
                self.client.subscribe(f"drone/{drone_id}/mission-spec")
        else:
            pass  # Handle connection failure if needed

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode('utf-8')

        if topic == "update_drone":
            # Parse the update_drone message
            try:
                update = json.loads(payload)
                drone_id = update.get('uavid')
                if drone_id and drone_id in self.all_drone_ids:
                    # Emit signal to handle drone data received
                    self.drone_data_received.emit(drone_id)
                    self.update_drone_received.emit(drone_id, update)
            except json.JSONDecodeError:
                pass
        elif topic.startswith("drone/") and topic.endswith("/mission-spec"):
            drone_id = topic.split('/')[1]
            try:
                mission_spec = json.loads(payload)
                print(f"Received mission spec: {mission_spec}")
                self.mission_spec_received.emit(drone_id, mission_spec)
            except json.JSONDecodeError:
                pass

    @Slot(str)
    def handle_drone_data_received(self, drone_id):
        # Check if we already have a DroneWidget for this drone
        if drone_id in self.drone_widgets:
            return

        # Determine the column based on the color/drone_id
        colors_in_order = self.all_drone_ids
        color_index = colors_in_order.index(drone_id)
        column = color_index % self.columns

        # Check if the column is already occupied
        occupied_columns = [pos for pos in self.cell_positions.values()]
        if column in occupied_columns:
            # Find the next available column
            for col in range(self.columns):
                if col not in occupied_columns:
                    column = col
                    break
            else:
                # No available columns
                return

        self.cell_positions[drone_id] = column

        # Create the DroneWidget for this drone
        drone_widget = DroneWidget(drone_id)
        self.drone_widgets[drone_id] = drone_widget

        # Connect MainWindow signals to DroneWidget
        self.mission_spec_received.connect(drone_widget.mission_visualizer.handle_mission_spec)
        self.update_drone_received.connect(drone_widget.status_widget.update_status_received)
        self.update_drone_received.connect(drone_widget.mission_visualizer.handle_update_drone)

        # Add the MissionVisualizer and StatusVisualization to the grid
        self.grid_layout.addWidget(drone_widget.mission_visualizer, 0, column)  # Top row
        self.grid_layout.addWidget(drone_widget.status_widget, 1, column)       # Bottom row

    def closeEvent(self, event):
        # Close the application and clean up resources
        self.client.loop_stop()
        self.client.disconnect()
        for drone_widget in self.drone_widgets.values():
            drone_widget.closeEvent(event)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())