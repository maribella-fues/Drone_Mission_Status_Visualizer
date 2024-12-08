# drone_widget.py

from PySide6.QtWidgets import QWidget
from mission_visualizer import MissionVisualizer
from status_visualization import StatusVisualization

class DroneWidget(QWidget):
    def __init__(self, drone_id):
        super().__init__()
        self.drone_id = drone_id

        # Create the MissionVisualizer and StatusVisualization for this drone
        self.mission_visualizer = MissionVisualizer(self.drone_id)
        self.status_widget = StatusVisualization(self.drone_id)

    def closeEvent(self, event):
        # Close resources if needed
        self.mission_visualizer.closeEvent(event)
        self.status_widget.closeEvent(event)
        event.accept()
