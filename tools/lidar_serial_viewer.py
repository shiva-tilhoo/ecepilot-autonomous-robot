import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import numpy as np

# ---- CONFIG ----
SERIAL_PORT = 'COM10'   # Replace with your serial port (not used in the simulation mode below)
BAUD_RATE = 115200
MAX_DISTANCE_M = 10.0   # drops points beyond 10m

# -------------------------------
# Minimal stand-in: simulated serial port
# -------------------------------
class SimSerial:
    """
    Simulates a serial device that sends LiDAR points as 'x,y' lines
    (in millimetres), followed by 'END' to close a scan.
    """
    def __init__(self, points_per_scan=360):
        self.points_per_scan = points_per_scan
        self.buffer = []

    @property
    def in_waiting(self):
        return len(self.buffer)

    def _generate_frame(self):
        n = self.points_per_scan
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        # uniform random distances in mm within [0, MAX_DISTANCE_M*1000]
        d_mm = np.random.uniform(0, MAX_DISTANCE_M * 1000.0, size=n)
        x = d_mm * np.cos(angles)
        y = d_mm * np.sin(angles)
        # Fill the buffer with 'x,y' lines (mm)
        for i in range(n):
            self.buffer.append(f"{x[i]:.1f},{y[i]:.1f}")
        self.buffer.append("END")

    def readline(self):
        if not self.buffer:
            self._generate_frame()
        line = self.buffer.pop(0)
        return (line + "\n").encode('utf-8')

# ---- SETUP SERIAL ----
# ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # (disabled for the simulation)
ser = SimSerial(points_per_scan=360)

# ---- SETUP PLOT ----

# ---- SETUP GUI ----
app = QtWidgets.QApplication([])
main_window = QtWidgets.QMainWindow()
main_window.setWindowTitle("2D LIDAR map")
main_window.resize(900, 700)

central_widget = QtWidgets.QWidget()
main_window.setCentralWidget(central_widget)
layout = QtWidgets.QVBoxLayout(central_widget)

# Plot area
plot_widget = pg.PlotWidget()
plot_widget.showGrid(x=True, y=True, alpha=0.3)
plot_widget.setLabel('left', 'Y (m)')
plot_widget.setLabel('bottom', 'X (m)')

plot_widget.setAspectLocked(False)
plot_widget.setBackground('w')
plot_widget.setXRange(-10, 10, padding=0)
plot_widget.setYRange(-10, 10, padding=0)

# List storing the previous scans
old_scans = []
max_old_scans = 20  # number of scans to keep

# Scatter for the current scan (red)
scatter_current = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,0,0,180))
plot_widget.addItem(scatter_current)

# Layout
layout.addWidget(plot_widget)

# Clear button
btn_clear = QtWidgets.QPushButton("Clear the map")
layout.addWidget(btn_clear)

def clear_map():
    global old_scans
    for s in old_scans:
        plot_widget.removeItem(s)
    old_scans = []
    scatter_current.setData([],[])
btn_clear.clicked.connect(clear_map)

# Coordinates info bar
coord_label = QtWidgets.QLabel("Coordinates: ")
layout.addWidget(coord_label)

# Navigation (zoom/pan)
plot_widget.setMouseEnabled(x=True, y=True)
plot_widget.getViewBox().setMouseMode(pg.ViewBox.PanMode)

# Cursor coordinates display
def mouseMoved(evt):
    pos = evt[0]  # QPointF
    if plot_widget.sceneBoundingRect().contains(pos):
        mouse_point = plot_widget.getViewBox().mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()
        coord_label.setText(f"Coordinates: X={x:.2f} m, Y={y:.2f} m")
    else:
        coord_label.setText("Coordinates: ")

proxy = pg.SignalProxy(plot_widget.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

main_window.show()

x_data, y_data = [], []

# ---- UPDATE FUNCTION ----
def update():
    global x_data, y_data
    while ser.in_waiting:
        raw = ser.readline()
        print(f"Raw: {raw}")
        try:
            line = raw.decode('utf-8').strip()
        except Exception as e:
            print(f"Decoding error: {e}")
            continue
        print(f"Decoded line: {line}")
        if line == "END":
            if len(x_data) == 0:
                x_data, y_data = [], []
                continue

            # Convert to metres
            x_m = np.array(x_data) / 1000.0
            y_m = np.array(y_data) / 1000.0

            # Filter out outliers
            mask = (np.abs(x_m) <= MAX_DISTANCE_M) & (np.abs(y_m) <= MAX_DISTANCE_M)
            x_m = x_m[mask]
            y_m = y_m[mask]

            # Update the scatter

            # Add the current scan to the previous ones (in grey)
            if len(x_m) > 0:
                scatter_old = pg.ScatterPlotItem(x=x_m, y=y_m, size=5, brush=pg.mkBrush(100,100,100,80))
                plot_widget.addItem(scatter_old)
                old_scans.append(scatter_old)
                if len(old_scans) > max_old_scans:
                    s = old_scans.pop(0)
                    plot_widget.removeItem(s)

            # Show the current scan in red
            scatter_current.setData(x=x_m, y=y_m)

            # The view stays fixed, no automatic re-centring

            x_data, y_data = [], []
        else:
            try:
                x_str, y_str = line.split(',')
                x_data.append(float(x_str))
                y_data.append(float(y_str))
            except:
                pass

# ---- TIMER ----
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(30)  # 30 ms → ~33 fps

# ---- START APPLICATION ----
app.exec_()
