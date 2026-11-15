import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import numpy as np

# ---- CONFIG ----
SERIAL_PORT = 'COM10'   # Remplace par ton port série (non utilisé en mode simulation ci-dessous)
BAUD_RATE = 115200
MAX_DISTANCE_M = 10.0   # filtre les points >10m

# -------------------------------
# Remplacement minimal : Serial simulé
# -------------------------------
class SimSerial:
    """
    Simule un périphérique série qui émet des points LiDAR sous forme de lignes 'x,y'
    (en millimètres), suivis de 'END' pour clore un scan.
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
        # distances aléatoires uniformes en mm dans [0, MAX_DISTANCE_M*1000]
        d_mm = np.random.uniform(0, MAX_DISTANCE_M * 1000.0, size=n)
        x = d_mm * np.cos(angles)
        y = d_mm * np.sin(angles)
        # Remplir le buffer sous forme 'x,y' (mm)
        for i in range(n):
            self.buffer.append(f"{x[i]:.1f},{y[i]:.1f}")
        self.buffer.append("END")

    def readline(self):
        if not self.buffer:
            self._generate_frame()
        line = self.buffer.pop(0)
        return (line + "\n").encode('utf-8')

# ---- SETUP SERIAL ----
# ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # (désactivé pour la simulation)
ser = SimSerial(points_per_scan=360)

# ---- SETUP PLOT ----

# ---- SETUP GUI ----
app = QtWidgets.QApplication([])
main_window = QtWidgets.QMainWindow()
main_window.setWindowTitle("Carte 2D LIDAR")
main_window.resize(900, 700)

central_widget = QtWidgets.QWidget()
main_window.setCentralWidget(central_widget)
layout = QtWidgets.QVBoxLayout(central_widget)

# Zone graphique
plot_widget = pg.PlotWidget()
plot_widget.showGrid(x=True, y=True, alpha=0.3)
plot_widget.setLabel('left', 'Y (m)')
plot_widget.setLabel('bottom', 'X (m)')

plot_widget.setAspectLocked(False)
plot_widget.setBackground('w')
plot_widget.setXRange(-10, 10, padding=0)
plot_widget.setYRange(-10, 10, padding=0)

# Liste pour stocker les anciens scans
old_scans = []
max_old_scans = 20  # nombre de scans à garder

# Scatter pour le scan courant (rouge)
scatter_current = pg.ScatterPlotItem(size=7, brush=pg.mkBrush(255,0,0,180))
plot_widget.addItem(scatter_current)

# Layout
layout.addWidget(plot_widget)

# Bouton pour effacer
btn_clear = QtWidgets.QPushButton("Effacer la carte")
layout.addWidget(btn_clear)

def clear_map():
    global old_scans
    for s in old_scans:
        plot_widget.removeItem(s)
    old_scans = []
    scatter_current.setData([],[])
btn_clear.clicked.connect(clear_map)

# Barre d'infos coordonnées
coord_label = QtWidgets.QLabel("Coordonnées : ")
layout.addWidget(coord_label)

# Navigation (zoom/pan)
plot_widget.setMouseEnabled(x=True, y=True)
plot_widget.getViewBox().setMouseMode(pg.ViewBox.PanMode)

# Affichage coordonnées curseur
def mouseMoved(evt):
    pos = evt[0]  # QPointF
    if plot_widget.sceneBoundingRect().contains(pos):
        mouse_point = plot_widget.getViewBox().mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()
        coord_label.setText(f"Coordonnées : X={x:.2f} m, Y={y:.2f} m")
    else:
        coord_label.setText("Coordonnées : ")

proxy = pg.SignalProxy(plot_widget.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

main_window.show()

x_data, y_data = [], []

# ---- UPDATE FUNCTION ----
def update():
    global x_data, y_data
    while ser.in_waiting:
        raw = ser.readline()
        print(f"Brut: {raw}")
        try:
            line = raw.decode('utf-8').strip()
        except Exception as e:
            print(f"Erreur décodage: {e}")
            continue
        print(f"Ligne décodée: {line}")
        if line == "END":
            if len(x_data) == 0:
                x_data, y_data = [], []
                continue

            # Conversion en mètres
            x_m = np.array(x_data) / 1000.0
            y_m = np.array(y_data) / 1000.0

            # Filtrage points aberrants
            mask = (np.abs(x_m) <= MAX_DISTANCE_M) & (np.abs(y_m) <= MAX_DISTANCE_M)
            x_m = x_m[mask]
            y_m = y_m[mask]

            # Mise à jour scatter

            # Ajoute le scan courant à la liste des anciens (en gris)
            if len(x_m) > 0:
                scatter_old = pg.ScatterPlotItem(x=x_m, y=y_m, size=5, brush=pg.mkBrush(100,100,100,80))
                plot_widget.addItem(scatter_old)
                old_scans.append(scatter_old)
                if len(old_scans) > max_old_scans:
                    s = old_scans.pop(0)
                    plot_widget.removeItem(s)

            # Affiche le scan courant en rouge
            scatter_current.setData(x=x_m, y=y_m)

            # La vue reste fixe, pas de recentrage automatique

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
