# mission_visualizer.py

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QPixmap, QFont
from PySide6.QtWidgets import (
    QWidget, QGraphicsView, QVBoxLayout, QGraphicsScene, QLabel, QPushButton, QHBoxLayout
)
import paho.mqtt.client as mqtt
import json
from graphviz import Digraph
import re
'''
def get_mqtt_config():
    settings = {'mqtt_broker_address': "localhost", 'mqtt_port': 1883}
    broker = settings['mqtt_broker_address']
    port = settings['mqtt_port']
    return {"broker": broker, "port": port}
'''

class MissionVisualizer(QWidget):
    mission_spec_received = Signal(dict)
    update_drone_received = Signal(dict)

    def __init__(self, drone_id):
        super().__init__()
        self.drone_id = drone_id
        self.mission_spec = None
        self.current_state = None

        self.initUI()

        # Connect signals to slots
        # self.mission_spec_received.connect(self.handle_mission_spec)
        # self.update_drone_received.connect(self.handle_update_drone)

        # self.setup_mqtt()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Create the QGraphicsView for displaying the mission graph
        self.graph_view = QGraphicsView(self)
        # Create empty scene with placeholder text
        empty_scene = QGraphicsScene()
        empty_label = QLabel("No mission data")
        empty_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        empty_label.setFont(font)
        empty_scene.addWidget(empty_label)
        self.graph_view.setScene(empty_scene)
        self.layout.addWidget(self.graph_view)

        # Create the buttons in a horizontal layout
        self.button_layout = QHBoxLayout()
        self.rtl_button = QPushButton("RTL", self)
        self.rtl_button.setEnabled(False)
        self.button_layout.addWidget(self.rtl_button)
        self.land_button = QPushButton("Land", self)
        self.land_button.setEnabled(False)
        self.button_layout.addWidget(self.land_button)
        self.loiter_button = QPushButton("Loiter", self)
        self.loiter_button.setEnabled(False)
        self.button_layout.addWidget(self.loiter_button)
        self.human_control_button = QPushButton("Human Control", self)
        self.human_control_button.setEnabled(False)
        self.button_layout.addWidget(self.human_control_button)
        self.layout.addLayout(self.button_layout)
    
    @Slot(dict)
    def handle_mission_spec(self, drone_id, mission_spec):
        if drone_id != self.drone_id:
            return

        self.mission_spec = mission_spec
        # Buttons remain disabled
        self.display_mission_graph()

    @Slot(dict)
    def handle_update_drone(self, drone_id, update):
        if drone_id != self.drone_id:
            return
        self.current_state = update.get('status', {}).get('onboard_pilot', 'N/A')
        mode = update.get('status', {}).get('mode', 'N/A')
        # Update the mission graph
        self.display_mission_graph()

        # Update the buttons
        # Reset button styles
        for button in [self.rtl_button, self.land_button, self.loiter_button, self.human_control_button]:
            if button:
                button.setStyleSheet("")

        drone_color = self.get_drone_color(self.drone_id)

        # Update 'HumanControl' button if onboard_pilot contains 'HumanControl'
        if 'humancontrol' in self.current_state.lower():
            if self.human_control_button:
                self.human_control_button.setStyleSheet(f"background-color: {drone_color}")

        # Update mode buttons
        mode_upper = mode.upper()
        if mode_upper == 'LAND':
            if self.land_button:
                self.land_button.setStyleSheet(f"background-color: {drone_color}")
        elif mode_upper == 'LOITER':
            if self.loiter_button:
                self.loiter_button.setStyleSheet(f"background-color: {drone_color}")
        elif mode_upper == 'RTL':
            if self.rtl_button:
                self.rtl_button.setStyleSheet(f"background-color: {drone_color}")

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
    
    def normalize_state(self, state_name):
        # Remove known suffixes and prefixes
        state_name = state_name.lower()
        # Remove known suffixes
        known_suffixes = ['px4', 'ardupilot']
        for suffix in known_suffixes:
            if state_name.endswith(suffix):
                state_name = state_name[:-len(suffix)]
        # Remove any non-alphanumeric characters
        state_name = re.sub(r'\W+', '', state_name)
        return state_name.strip()

    def display_mission_graph(self):
        if not self.mission_spec:
            return

        mission_spec = self.mission_spec
        current_state = self.current_state

        # Create a new directed graph with 'png' format
        dot = Digraph('StateMachine', format='png')
        dot.attr('graph', ranksep='0.3 equally', dpi='150', bgcolor='transparent', nodesep='1 equally')  # Transparent background
        dot.attr('node', shape='rectangle', style='filled', fillcolor='transparent', color='black', fontcolor='black')
        dot.attr('edge', color='black', fontcolor='black')
        dot.attr(splines='lines') # lines or otho to straight edges
        dot.attr(rankdir='TB')  # Top to bottom layout

        nodes = set()

        # Store normalized state names for matching
        state_name_mapping = {}  # Maps normalized state names to actual state names

        for state in mission_spec.get('states', []):
            state_name = state['name']
            nodes.add(state_name)
            # Normalize state name for matching
            normalized_state_name = self.normalize_state(state_name)
            state_name_mapping[normalized_state_name] = state_name
            if 'transitions' in state:
                for transition in state['transitions']:
                    target = transition['target']
                    condition = transition.get('condition', '')
                    dot.edge(state_name, target, label=condition)
                    nodes.add(target)
                    # Normalize target state name
                    normalized_target_name = self.normalize_state(target)
                    state_name_mapping[normalized_target_name] = target

        # Normalize current_state for matching
        current_state_normalized = self.normalize_state(current_state) if current_state else ''

        # **START OF MODIFICATIONS**

        # Check if current_state is not already a node in the graph
        if current_state and current_state_normalized not in state_name_mapping:
            # Check if 'RunTasks' is in nodes to connect DynamicState
            if 'RunTasks' in nodes:
                # Add a dynamic state node called 'DynamicState' with label as current_state
                dynamic_state_name = 'DynamicState'
                nodes.add(dynamic_state_name)
                # Add edges between 'RunTasks' and 'DynamicState'
                dot.edge('RunTasks', dynamic_state_name)
                dot.edge(dynamic_state_name, 'RunTasks')
                # Map normalized dynamic state name to 'DynamicState'
                state_name_mapping[current_state_normalized] = dynamic_state_name
            else:
                # If 'RunTasks' is not in nodes, just add the dynamic state without connections
                dynamic_state_name = current_state
                nodes.add(dynamic_state_name)
                # Map normalized dynamic state name to current_state
                state_name_mapping[current_state_normalized] = dynamic_state_name

        # **END OF MODIFICATIONS**

        # Find matching state(s)
        matched_state = None
        # current_state_normalized = self.current_state.lower() if self.current_state else ''
        for normalized_state_name, actual_state_name in state_name_mapping.items():
            if normalized_state_name in current_state_normalized or current_state_normalized in normalized_state_name:
                matched_state = actual_state_name
                break

        # Apply styling to nodes
        drone_color = self.get_drone_color(self.drone_id)
        for node in nodes:
            node_attrs = {}
            # Default label is node name
            node_label = node
            # **MODIFICATION: For DynamicState, set the label to current_state**
            if node == 'DynamicState':
                node_label = current_state if current_state else ''
            node_attrs['label'] = node_label
            # Check if this node is the matched_state
            if node == matched_state:
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = drone_color
                node_attrs['fontcolor'] = 'black'
            # Add the node with attributes
            dot.node(node, **node_attrs)
        
        # Render the graph to an in-memory image
        png_data = dot.pipe(format='png')

        # Load the image into a QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(png_data)

        if pixmap.isNull():
            return

        # Display the pixmap in the QGraphicsView
        scene = QGraphicsScene()
        # Do not set background to black; keep it transparent
        scene.addPixmap(pixmap)
        self.graph_view.setScene(scene)
        self.graph_view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)

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
            # Subscribe to topics for this drone
            self.client.subscribe(f"drone/{self.drone_id}/mission-spec")
            self.client.subscribe("update_drone")
        else:
            pass

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode('utf-8')

        if topic == f"drone/{self.drone_id}/mission-spec":
            # Parse the mission-spec message and emit signal
            try:
                mission_spec = json.loads(payload)
                self.mission_spec_received.emit(mission_spec)
            except json.JSONDecodeError:
                pass
        elif topic == "update_drone":
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