from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget
import pyqtgraph as pg


class SimulationPlot(QWidget):
    """Виджет графика аналитического решения и метода RK4."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.plot = pg.PlotWidget()
        self.plot.setLabel("left", "Uc", units="V")
        self.plot.setLabel("bottom", "t", units="s")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.addLegend()

        layout.addWidget(self.plot)

    def draw(self, analytical, numerical, t95=None, Um=None):
        self.plot.clear()
        self.plot.addLegend()

        xa = [t for t, _ in analytical]
        ya = [u for _, u in analytical]
        xn = [t for t, _ in numerical]
        yn = [u for _, u in numerical]

        self.plot.plot(
            xa,
            ya,
            pen=pg.mkPen(width=2),
            name="Аналитика",
        )

        self.plot.plot(
            xn,
            yn,
            pen=pg.mkPen(
                style=Qt.PenStyle.DashLine,
                width=2,
            ),
            name="RK4",
        )

        if t95 is not None:
            self.plot.addLine(
                x=t95,
                pen=pg.mkPen(style=Qt.PenStyle.DotLine),
            )

        if Um is not None:
            self.plot.addLine(
                y=Um,
                pen=pg.mkPen(style=Qt.PenStyle.DotLine),
            )

        # Автоматически подбираем диапазоны обеих осей
        # по отображаемым данным после каждого расчёта.
        self.plot.getViewBox().autoRange(padding=0.08)
