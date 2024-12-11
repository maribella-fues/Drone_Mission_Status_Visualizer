# Drone Mission and Status Visualizer - Code Functionality

To run: python ./main.py

This application visualizes multiple actively-running drones' real-time mission plans and statuses received from MQTT messages. It consists of four main classes:

- `MainWindow`: Acts as the controller and central hub for the application. Manages multiple drones and their widgets, and handles MQTT communication.
- `DroneWidget`: Represents an individual drone. Comprises two visualization components: `MissionVisualizer` and `StatusVisualization`.
- `MissionVisualizer`: Displays mission-specific information for a drone (e.g., waypoints, objectives).
- `StatusVisualization`: Displays telemetry and operational status of a drone (e.g., speed, location, battery level).

Below is an explanation of each class, their methods, attributes, and how they interact.

## Classes and Their Interactions

### 1. MainWindow
**Purpose**: Acts as the central application window, managing the display and interaction of drone widgets. It connects to an MQTT broker to receive and process drone mission specifications and status updates dynamically.

**Inheritance**: Inherits from `QMainWindow`.

#### Attributes:
- `all_drone_ids`: List of all possible drone IDs/colors that the application recognizes.
- `drone_widgets`: Dictionary mapping drone_id to a `DroneWidget` instance for easy lookup and management.
- `cell_positions`: Dictionary mapping each drone_id to its assigned column position in the grid layout.
- `grid_layout`: A `QGridLayout` that sets the 3x3 grid layout for the GUI display.
- `rows`: Number of rows for the grid
- `columns`: Number of columns for the grid.
- `central_widget`: A `QWidget` that dictates the main window's central widget
- `client`: The MQTT client that connects, subscribes, and receives messages fromt the MQTT

### Signals:
- `drone_data_received`: Emitted when a new drone ID is detected in the received data.
- `mission_spec_received`: Emitted when a mission specification for a drone is received (drone_id, mission_spec).
- `update_drone_received`: Emitted when a status update for a drone is received (drone_id, update).

#### Methods:
- `__init__()`: Initializes the main application window. Sets up the UI layout, MQTT client, and signal-slot connections. Prepares to manage up to rows * columns drones in the grid.
- `initUI()`: Configures the central widget and grid layout to organize drone widgets.
- `setup_mqtt()`: Creates and configures the MQTT client for communication with the broker. Starts the MQTT loop in a separate thread.
- `on_connect(client, userdata, flags, rc)`: Subscribes to relevant topics upon successfully connecting to the MQTT broker. Monitors `update_drone` for active drone detection and `mission-spec` topics for individual drones.
- `on_message(client, userdata, message)`: Handles incoming MQTT messages. Decodes the payload and emits signals for drone data or mission specifications.
- `handle_drone_data_received(drone_id)`: A `Slot` that adds a new `DroneWidget` to the grid when a previously unseen drone ID is detected. Assigns the widget to a column based on the drone ID or finds an available column. Connects `MainWindow` signals to the appropriate slots in the `DroneWidget`.
- `closeEvent(event)`: Gracefully shuts down the application, stopping the MQTT loop and disconnecting the client. Calls cleanup for all `DroneWidget` instances before exiting.

#### Interactions:
- **With MQTT**: Receives drone mission specifications and status updates via subscribed topics. Decodes and routes data to the appropriate `DroneWidget`.
- **With DroneWidget**: Dynamically creates and manages widgets for each active drone. Adds the widgets to a grid layout with separate rows for mission visualization and status display. Passes mission specifications and updates to DroneWidget components via signals.
- **With MissionVisualizer**: Uses signals to send the mission-spec information and status updates to the `MissionVisualizer` to generate the graph and current state/mode for each of the `DroneWidget` instances.
- **With StatusVisualizer**: Uses signals to sends the status update information to the `StatusVisualizer` to display the statuses for each of the `DroneWidget` instances.

---

### 2. DroneWidget

**Purpose**: Encapsulates the visual components for displaying and managing data related to a single drone. It serves as a container for `MissionVisualizer` and `StatusVisualization`, which handle `mission-specific` and `status updates`, respectively.

**Inheritance**: Inherits from `QWidget`.

#### Attributes:
- `drone_id`: A unique identifier for the drone (e.g., color name or ID).
- `mission_visualizer`: An instance of `MissionVisualizer` for displaying mission-related data.
- `status_widget`: An instance of `StatusVisualization` for showing drone status updates.

#### Methods:
- `__init__(drone_id)`: Initializes the widget with the given drone_id. Creates a `MissionVisualizer` and `StatusVisualization` specifically tied to this drone.
- `closeEvent(event)`: Ensures clean closure of resources associated with the drone. Delegates the 'closeEvent' handling to `MissionVisualizer` and `StatusVisualization`. Accepts the closure event after cleanup.

#### Interactions:
- **With MainWindow**: Is dynamically created and managed by the `MainWindow `when a new drone is detected. Receives mission specification and status updates via signals connected by the `MainWindow`.
- **With MissionVisualizer**: Handles mission-specific data for the drone (e.g., paths, waypoints, objectives). Updates the visualizer whenever new mission data is received.
- **With StatusVisualizer**: Manages the display of the drone's current status (e.g., battery, location, or other telemetry). Updates dynamically in response to new status messages.

---

### 3. MissionVisualizer

**Purpose**: Visualizes the mission specification and current state of a specific drone in a graphical format, allowing for dynamic updates based on received data. Includes a set of buttons to display the drone's mode, with styles updated dynamically based on its current status.

**Inheritance**: Inherits from `QWidget`.

#### Attributes:
- `drone_id`: Identifier for the specific drone being visualized.
- `mission_spec`: The current mission specification received for the drone (dictionary).
- `current_state`: The drone's current state or mode (string).
- `layout`: A `QVBoxLayout` that arranges the components vertically.
- `graph_view`: A `QGraphicsView` that displays the mission graph visualization.
- `button_layout`: A `QHBoxLayout` that holds the control buttons.
- Control Buttons:
  - `rtl_button`: Represents the "Return to Launch" mode.
  - `land_button`: Represents the "Land" mode.
  - `loiter_button`: Represents the "Loiter" mode.
  - `human_control_button`: Indicates if the drone is in "Human Control" mode.

#### Methods:
- `__init__(drone_id)`: Initializes the `MissionVisualizer` for a given drone ID., sets up the UI layout and initializes attributes.
- `initUI()`: Sets up the visual components (graph, buttons) and their layout.
- `handle_mission_spec(drone_id, mission_spec)`: A `Slot` that updates the mission specification if the drone ID matches and triggers graph visualization with the new mission specification.
- `handle_update_drone(drone_id, update)`: A `Slot` that processes updates for the drone's status and mode, highlights the relevant button based on the drone's current mode, and updates the mission graph if necessary.
- `get_drone_color(drone_id)`: Returns a unique color corresponding to the drone ID using a predefined color map.
- `normalize_state(state_name)`: Cleans up state names by removing known suffixes, prefixes, and non-alphanumeric characters.
- `display_mission_graph()`: Generates and displays a state machine diagram using `Graphviz`, dynamically adds nodes and edges based on the mission specification, and highlights the current state or dynamically adds it if missing.

#### Interactions:
- **With MQTT**: Updates the drone's mission specification display and current state in real time upon receiving data published to a relevant topic. Filters incoming data to ensure it pertains to the associated drone_id.
- **With DroneWidget**: Managed as part of a `DroneWidget` instance to visualize flight missions and current states for a single drone. Connected to `MainWindow` signals for receiving live updates.

---

### 4. StatusVisualization

**Purpose**: Provides a visual representation of a drone's status, including telemetry, location, and battery information, in a neatly formatted HTML widget. Dynamically updates its display in response to incoming drone data.

**Inheritance**: Inherits from `QWidget`.

#### Attributes:
- `drone_id`: A unique identifier for the drone (e.g., color name or ID).
- `update_drone_received`: A signal used to handle incoming status updates for the drone.
- `layout`: A vertical box layout (`QVBoxLayout`) that contains the status display widget.
- `text_widget`: A `QTextEdit` widget used to display the drone's status in HTML format.

#### Methods:
- `__init__(drone_id)`: Initializes the widget for the given drone ID. Sets up the UI layout and creates the text display widget.
- `initUI()`: Configures the layout and initializes the QTextEdit to display drone status. Sets the text area to read-only and formats it for a smaller font and centered placeholder text.
- `update_status_received(drone_id, data)`: A `Slot` that processes incoming drone status updates. Updates the text_widget with formatted data if the drone_id matches this widget's drone ID.
- `get_drone_color(drone_id)`: Maps a drone ID to a specific color using a predefined dictionary (UAV_COLOR_MAP). Defaults to black if no color is found for the given drone ID.
- `formatData(data)`: Converts the incoming status data into an HTML-formatted string for display in the text_widget. Handles missing or malformed data gracefully by substituting "N/A." Extracts and processes:
  - Drone identity (e.g., ID, status).
  - Location (latitude, longitude, altitude).
  - Speed (converting from m/s to mph).
  - Drone heading (converts radians to a compass direction like North, East, etc.).
  - Battery information (level, voltage, current).

#### Interactions:
- **With MQTT**: Updates the drone's status display in real time upon receiving data published to a relevant topic. Filters incoming data to ensure it pertains to the associated drone_id.
- **With DroneWidget**: Managed as part of a `DroneWidget` instance to visualize status updates for a single drone. Connected to `MainWindow` signals for receiving live updates.

---

## How They Work Together

### MQTT Communication in MainWindow
- MainWindow establishes an MQTT connection using the `paho-mqtt` library.
- It subscribes to topics such as:
  - `update_drone`: General updates about drones (e.g., active/inactive status).
  - `drone/<drone_id>/mission-spec`: Mission-specific data for individual drones.
- Incoming MQTT messages trigger `MainWindow` slots (`on_message`), which parse the payload and emit corresponding signals:
  - `drone_data_received` for drone activation.
  - `mission_spec_received` and `update_drone_received` for mission and status updates.

### Dynamic Drone Management
- When a drone is detected (via an `update_drone` message), `MainWindow`:
1. Creates a new `DroneWidget` instance if it doesn't already exist for the drone ID.
2. Assigns the widget a position in a grid layout.
3. Establishes connections between MainWindow's signals and the widget's components:
    - **Mission data** (`mission_spec_received`): Passed to the `MissionVisualizer` inside the DroneWidget.
    - **Status updates** (`update_drone_received`): Passed to the `StatusVisualization` inside the `DroneWidget`.
  
### DroneWidget Composition
- A `DroneWidget` is a container for:
  - `MissionVisualizer`: Handles and visualizes mission specifications like flight paths.
  - `StatusVisualization`: Displays live telemetry and operational data.
- Signals from `MainWindow` are routed to the appropriate visualization component within the `DroneWidget`:
  - Mission updates modify the mission visualization.
  - Status updates modify the telemetry display.

---

## Data Flow

### 1. MQTT Message Reception (`MainWindow`):
- The MQTT client in `MainWindow` receives messages from subscribed topics.
- The `on_message` method parses the topic and payload, determining the type of data received.
- `MainWindow` emits a corresponding signal (e.g., `update_drone_received`).
### 2. Signal Routing to DroneWidget:
- If the signal corresponds to an existing drone ID:
  - `mission_spec_received` is sent to the `MissionVisualizer` in the `DroneWidget`.
  - `update_drone_received` is sent to the `StatusVisualization` in the `DroneWidget`.
### 3. Visualization Updates:
- **MissionVisualizer** updates its display (e.g., waypoints or mission progress) based on the mission data.
- **StatusVisualization** updates its telemetry display (e.g., speed, location, battery) based on the status data.
### 4. Dynamic Widget Management:
- If a new drone becomes active, `MainWindow` dynamically creates a new `DroneWidget` and adds it to the grid layout.
- Each `DroneWidget` operates independently while being managed centrally by `MainWindow`.
