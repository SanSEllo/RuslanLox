from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFormLayout, QDoubleSpinBox, QPushButton,
    QLabel, QFileDialog, QHBoxLayout, QVBoxLayout, QMessageBox
)
from core.models import RCParameters
from core.simulation import run_simulation
from export.exporters import save_csv, save_json
from .simulation_plot import SimulationPlot


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VirtualLab — Заряд конденсатора в RC-цепи")
        self.resize(1100, 700)
        self.last_parameters = None
        self.last_result = None

        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)

        controls = QFormLayout()

        self.um = self._spin(0, 1e6, 220, 1)
        self.r = self._spin(0.001, 1e12, 50_000, 100)
        self.c = self._spin(1e-15, 1, 1e-7, 1e-8)
        self.uc0 = self._spin(-1e6, 1e6, 0, 1)
        self.dt = self._spin(1e-9, 10, 1e-4, 1e-5)
        self.t_end = self._spin(1e-9, 100, 0.025, 1e-3)

        controls.addRow("Um, В:", self.um)
        controls.addRow("R, Ом:", self.r)
        controls.addRow("C, Ф:", self.c)
        controls.addRow("Uc(0), В:", self.uc0)
        controls.addRow("dt, с:", self.dt)
        controls.addRow("t_end, с:", self.t_end)

        self.run_button = QPushButton("Рассчитать")
        self.run_button.clicked.connect(self.calculate)
        controls.addRow(self.run_button)

        buttons = QHBoxLayout()
        self.csv_button = QPushButton("CSV")
        self.json_button = QPushButton("JSON")
        self.csv_button.clicked.connect(self.export_csv)
        self.json_button.clicked.connect(self.export_json)
        self.csv_button.setEnabled(False)
        self.json_button.setEnabled(False)
        buttons.addWidget(self.csv_button)
        buttons.addWidget(self.json_button)

        left = QVBoxLayout()
        left.addLayout(controls)
        left.addLayout(buttons)

        self.tau_label = QLabel("τ = —")
        self.t95_label = QLabel("t95 = —")
        self.error_label = QLabel("max |RK4 − аналитика| = —")
        left.addWidget(self.tau_label)
        left.addWidget(self.t95_label)
        left.addWidget(self.error_label)
        left.addStretch()

        main.addLayout(left, 1)

        self.graph = SimulationPlot()
        main.addWidget(self.graph, 3)

    @staticmethod
    def _spin(minimum, maximum, value, step):
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        box.setSingleStep(step)
        box.setDecimals(12)
        box.setMinimumWidth(150)
        return box

    def calculate(self):
        try:
            p = RCParameters(
                Um=self.um.value(),
                R=self.r.value(),
                C=self.c.value(),
                Uc0=self.uc0.value(),
            )
            if p.tau <= 0:
                raise ValueError("RC должно быть положительным.")
            result = run_simulation(p, self.t_end.value(), self.dt.value())

            max_error = max(
                abs(a[1] - n[1])
                for a, n in zip(result.analytical, result.numerical)
            )

            from core.rc_circuit import RCCircuit
            circuit = RCCircuit(p)

            self.last_parameters = p
            self.last_result = result
            self.tau_label.setText(f"τ = {p.tau:.6g} с ({p.tau*1000:.4g} мс)")
            self.t95_label.setText(f"t95 = {circuit.t95():.6g} с ({circuit.t95()*1000:.4g} мс)")
            self.error_label.setText(f"max |RK4 − аналитика| = {max_error:.3e} В")

            self.graph.draw(result.analytical, result.numerical, circuit.t95(), p.Um)
            self.csv_button.setEnabled(True)
            self.json_button.setEnabled(True)

        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def export_csv(self):
        if not self.last_result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "rc_simulation.csv", "CSV (*.csv)")
        if path:
            save_csv(path, self.last_parameters, self.last_result)

    def export_json(self):
        if not self.last_result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить JSON", "rc_simulation.json", "JSON (*.json)")
        if path:
            save_json(path, self.last_parameters, self.last_result)
