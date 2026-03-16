"""
Pestaña para cálculo de puntos fiduciales sobre señal PPG filtrada
cargada desde un archivo CSV externo.

Flujo de uso:
  1. Cargar un CSV con señal ya filtrada (columnas: tiempo, valor).
  2. Graficar la señal.
  3. Pulsar "Calcular puntos fiduciales" → se grafican onset y pico sistólico.
  4. Pulsar "Guardar resultados" → se exportan los CSV de fiduciales,
     parámetros y señal suavizada, igual que en AnalysisTab.
"""

import os
import pandas as pd
import numpy as np
import pyqtgraph as pg

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QPushButton, QLabel, QFileDialog, QMessageBox, QTextEdit,
    QSpinBox, QInputDialog
)
from PyQt5.QtCore import Qt
from datetime import datetime


class FiducialTab(QWidget):
    """Pestaña de detección de puntos fiduciales a partir de CSV filtrado"""

    def __init__(self, ppg_processor):
        """
        :param ppg_processor: Instancia de PPGProcessor para reutilizar
                              analyze_segment() sin tocar las otras pestañas.
        """
        super().__init__()
        self.ppg_processor = ppg_processor

        # Estado interno
        self.time_data = None       # array numpy con el eje temporal
        self.signal_data = None     # array numpy con la señal filtrada cargada
        self.analysis_result = None  # dict devuelto por analyze_segment

        self.setup_ui()

    # ------------------------------------------------------------------ #
    #  Construcción de la UI                                               #
    # ------------------------------------------------------------------ #

    def setup_ui(self):
        """Construye el layout principal con splitter horizontal"""
        layout = QHBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        control = self._build_control_panel()
        control.setMaximumWidth(340)
        control.setMinimumWidth(280)
        splitter.addWidget(control)

        plots = self._build_plots_panel()
        splitter.addWidget(plots)

        splitter.setSizes([340, 1060])

        layout.addWidget(splitter)
        self.setLayout(layout)

    def _build_control_panel(self):
        """Panel izquierdo con controles"""
        widget = QWidget()
        layout = QVBoxLayout()

        # ── Grupo: Cargar CSV ───────────────────────────────────────── #
        load_group = QGroupBox("Cargar CSV filtrado")
        load_layout = QVBoxLayout()

        self.load_btn = QPushButton("Abrir archivo CSV…")
        self.load_btn.clicked.connect(self.load_csv_file)
        self.load_btn.setStyleSheet(self._btn_style("#3498DB", "#2980B9"))
        load_layout.addWidget(self.load_btn)

        self.file_info_label = QLabel("Ningún archivo cargado")
        self.file_info_label.setWordWrap(True)
        self.file_info_label.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        load_layout.addWidget(self.file_info_label)

        self.clear_btn = QPushButton("Limpiar datos")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.setStyleSheet(self._btn_style("#95A5A6", "#7F8C8D"))
        load_layout.addWidget(self.clear_btn)

        load_group.setLayout(load_layout)
        layout.addWidget(load_group)

        # ── Grupo: Parámetros de muestreo ────────────────────────────── #
        fs_group = QGroupBox("Frecuencia de muestreo")
        fs_layout = QHBoxLayout()

        fs_layout.addWidget(QLabel("Fs (Hz):"))
        self.fs_spin = QSpinBox()
        self.fs_spin.setRange(10, 2000)
        self.fs_spin.setValue(100)
        self.fs_spin.setToolTip(
            "Frecuencia de muestreo de la señal cargada.\n"
            "Debe coincidir con la frecuencia con que fue adquirida."
        )
        fs_layout.addWidget(self.fs_spin)

        fs_group.setLayout(fs_layout)
        layout.addWidget(fs_group)

        # ── Grupo: Procesamiento ─────────────────────────────────────── #
        proc_group = QGroupBox("Procesamiento")
        proc_layout = QVBoxLayout()

        self.detect_btn = QPushButton("Calcular puntos fiduciales")
        self.detect_btn.setEnabled(False)
        self.detect_btn.clicked.connect(self.detect_fiducials)
        self.detect_btn.setStyleSheet(self._btn_style("#8B5CF6", "#7C3AED"))
        proc_layout.addWidget(self.detect_btn)

        # Información de resultados
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("color: #2C3E50; font-size: 11px;")
        proc_layout.addWidget(self.result_label)

        proc_group.setLayout(proc_layout)
        layout.addWidget(proc_group)

        # ── Grupo: Exportar ──────────────────────────────────────────── #
        export_group = QGroupBox("Exportar Resultados")
        export_layout = QVBoxLayout()

        self.save_btn = QPushButton("Guardar resultados CSV")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setStyleSheet(self._btn_style("#27AE60", "#229954"))
        export_layout.addWidget(self.save_btn)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # ── Log ─────────────────────────────────────────────────────── #
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(160)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _build_plots_panel(self):
        """Panel derecho con dos gráficos apilados verticalmente"""
        widget = QWidget()
        layout = QVBoxLayout()

        # ── Gráfico superior: señal filtrada + scatter fiduciales ─────── #
        self.signal_plot = pg.PlotWidget(title="Señal filtrada cargada")
        self.signal_plot.setLabel('left', 'Amplitud')
        self.signal_plot.setLabel('bottom', 'Tiempo (s)')
        self.signal_plot.showGrid(x=True, y=True)

        self.signal_curve = self.signal_plot.plot(
            pen=pg.mkPen('#4ECDC4', width=2), name="Señal filtrada"
        )

        # Picos sistólicos: círculos rojos
        self.scatter_systolic = pg.ScatterPlotItem(
            symbol='o', size=10,
            pen=pg.mkPen(None),
            brush=pg.mkBrush('#EF4444'),
            name="Pico sistólico"
        )
        self.signal_plot.addItem(self.scatter_systolic)

        # Onset / foot: triángulos azules
        self.scatter_foot = pg.ScatterPlotItem(
            symbol='t', size=10,
            pen=pg.mkPen(None),
            brush=pg.mkBrush('#3B82F6'),
            name="Onset (foot)"
        )
        self.signal_plot.addItem(self.scatter_foot)

        layout.addWidget(self.signal_plot)

        # ── Gráfico inferior: señal suavizada ──────────────────────────── #
        self.smooth_plot = pg.PlotWidget(title="Señal suavizada (Savitzky-Golay)")
        self.smooth_plot.setLabel('left', 'Amplitud')
        self.smooth_plot.setLabel('bottom', 'Tiempo (s)')
        self.smooth_plot.showGrid(x=True, y=True)

        self.smooth_curve = self.smooth_plot.plot(
            pen=pg.mkPen('#F59E0B', width=2), name="Señal suavizada"
        )
        layout.addWidget(self.smooth_plot)

        widget.setLayout(layout)
        return widget

    # ------------------------------------------------------------------ #
    #  Lógica de trabajo                                                   #
    # ------------------------------------------------------------------ #

    def load_csv_file(self):
        """Abre un CSV y carga las columnas de tiempo y señal"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar CSV filtrado", "", "Archivos CSV (*.csv)"
        )
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)

            if df.shape[1] >= 2:
                self.time_data = df.iloc[:, 0].values.astype(float)
                self.signal_data = df.iloc[:, 1].values.astype(float)
            elif df.shape[1] == 1:
                self.signal_data = df.iloc[:, 0].values.astype(float)
                self.time_data = np.arange(len(self.signal_data)) / self.fs_spin.value()
            else:
                raise ValueError("El archivo debe tener al menos una columna de datos")

            n = len(self.signal_data)
            duration = self.time_data[-1] - self.time_data[0]
            file_name = os.path.basename(file_path)

            self.file_info_label.setText(
                f"<b>{file_name}</b><br>"
                f"{n} puntos · {duration:.2f} s"
            )

            # Actualizar gráfico de la señal
            self.signal_curve.setData(self.time_data, self.signal_data)
            self.smooth_curve.setData([], [])
            self._clear_scatter()

            # Habilitar controles
            self.detect_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
            self.result_label.setText("")
            self.analysis_result = None

            self._log(f"CSV cargado: {file_name}  ({n} pts, {duration:.2f} s)")

        except Exception as e:
            QMessageBox.critical(self, "Error al cargar CSV", str(e))
            self._log(f"Error cargando CSV: {e}")

    def detect_fiducials(self):
        """Llama a ppg_processor.analyze_segment() y visualiza los resultados"""
        if self.signal_data is None or self.time_data is None:
            QMessageBox.warning(self, "Sin datos", "Cargue un archivo CSV primero.")
            return

        # Sincronizar la frecuencia de muestreo del procesador con la del spinner
        self.ppg_processor.fs = self.fs_spin.value()
        self.ppg_processor.sample_rate = self.fs_spin.value()

        try:
            analysis, parameters = self.ppg_processor.analyze_segment(
                self.time_data, self.signal_data
            )
        except Exception as e:
            QMessageBox.critical(self, "Error en análisis", str(e))
            self._log(f"Error en analyze_segment: {e}")
            return

        if not analysis:
            QMessageBox.information(
                self, "Sin resultado",
                "No se pudieron detectar puntos fiduciales.\n"
                "Verifique que la señal sea válida y la Fs sea correcta."
            )
            self._log("analyze_segment no encontró fiduciales.")
            return

        self.analysis_result = analysis

        # ── Graficar señal suavizada ───────────────────────────────── #
        ppg_smooth = analysis.get('ppg_smooth', [])
        if len(ppg_smooth):
            self.smooth_curve.setData(self.time_data, ppg_smooth)

        # ── Graficar puntos fiduciales ─────────────────────────────── #
        fid = analysis.get('fiducials', {})
        systolic_t = np.atleast_1d(fid.get('systolic_peak', []))
        foot_t = np.atleast_1d(fid.get('foot', []))

        def make_spots(t_array, sig, time_ref):
            spots = []
            for tv in t_array:
                idx = int(np.argmin(np.abs(time_ref - tv)))
                if 0 <= idx < len(sig):
                    spots.append({'pos': (time_ref[idx], sig[idx])})
            return spots

        self.scatter_systolic.setData(
            make_spots(systolic_t, self.signal_data, self.time_data)
        )
        self.scatter_foot.setData(
            make_spots(foot_t, self.signal_data, self.time_data)
        )

        # ── Habilitar guardado y actualizar info ───────────────────── #
        n_beats = len(analysis.get('beats', []))
        fc_str = parameters.get('FC (LPM)', 'N/A')
        ppi_str = parameters.get('PPI (s)', 'N/A')

        self.result_label.setText(
            f"<b>Latidos detectados:</b> {n_beats}<br>"
            f"<b>FC:</b> {fc_str} LPM<br>"
            f"<b>PPI:</b> {ppi_str} s"
        )

        self.save_btn.setEnabled(True)
        self._log(
            f"Fiduciales calculados — {n_beats} latidos · "
            f"FC={fc_str} LPM · PPI={ppi_str} s"
        )

    def save_results(self):
        """Guarda los resultados en archivos CSV dentro de una carpeta elegida"""
        if self.analysis_result is None:
            QMessageBox.warning(self, "Sin análisis", "Calcule los puntos fiduciales primero.")
            return

        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino", ""
        )
        if not directory:
            return

        base_name, ok = QInputDialog.getText(
            self, "Nombre base de archivos",
            "Ingrese un prefijo para los archivos:",
            text="analisis_ppg"
        )
        if not ok or not base_name.strip():
            return
        base_name = base_name.strip()

        saved = []

        try:
            # 1. Señal suavizada
            ppg_smooth = self.analysis_result.get('ppg_smooth', [])
            if len(ppg_smooth):
                df_smooth = pd.DataFrame({
                    'tiempo_s': self.time_data,
                    'senal_suavizada': ppg_smooth
                })
                path = os.path.join(directory, f"{base_name}_senal_suavizada.csv")
                df_smooth.to_csv(path, index=False)
                saved.append(f"• {base_name}_senal_suavizada.csv ({len(df_smooth)} pts)")

            # 2. Parámetros
            parameters = self.analysis_result.get('parameters', {})
            if parameters:
                df_params = pd.DataFrame(
                    list(parameters.items()),
                    columns=['Parametro', 'Valor']
                )
                path = os.path.join(directory, f"{base_name}_parametros.csv")
                df_params.to_csv(path, index=False)
                saved.append(f"• {base_name}_parametros.csv")

            # 3. Puntos fiduciales por latido
            beat_rows = self.analysis_result.get('beats', [])
            if beat_rows:
                rows = []
                for i, row in enumerate(beat_rows, start=1):
                    rows.append({
                        'latido':      i,
                        'onset_idx':   row['onset_idx'],
                        'onset_time':  row['onset_time'],
                        'onset_amp':   row['onset_amp'],
                        'sys_idx':     row['sys_idx'],
                        'sys_time':    row['sys_time'],
                        'sys_amp':     row['sys_amp'],
                    })
                df_fid = pd.DataFrame(
                    rows,
                    columns=['latido', 'onset_idx', 'onset_time', 'onset_amp',
                             'sys_idx', 'sys_time', 'sys_amp']
                )
                path = os.path.join(directory, f"{base_name}_fiduciales.csv")
                df_fid.to_csv(path, index=False)
                saved.append(
                    f"• {base_name}_fiduciales.csv ({len(df_fid)} latidos)"
                )

            files_list = "\n".join(saved) if saved else "Ningún archivo generado."
            self._log(f"Resultados guardados en: {directory}")
            QMessageBox.information(
                self, "Guardado exitoso",
                f"Archivos creados en:\n{directory}\n\n{files_list}"
            )

        except Exception as e:
            self._log(f"Error guardando resultados: {e}")
            QMessageBox.critical(self, "Error al guardar", str(e))

    # ------------------------------------------------------------------ #
    #  Utilidades internas                                                 #
    # ------------------------------------------------------------------ #

    def clear_all(self):
        """Limpia todos los datos y gráficos"""
        self.time_data = None
        self.signal_data = None
        self.analysis_result = None

        self.signal_curve.setData([], [])
        self.smooth_curve.setData([], [])
        self._clear_scatter()

        self.file_info_label.setText("Ningún archivo cargado")
        self.result_label.setText("")
        self.detect_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)

        self._log("Datos limpiados.")

    def _clear_scatter(self):
        self.scatter_systolic.clear()
        self.scatter_foot.clear()

    def _log(self, message: str):
        """Agrega una entrada con timestamp al log"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {message}")
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    @staticmethod
    def _btn_style(color: str, hover: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:disabled {{
                background-color: #BDC3C7;
                color: #7F8C8D;
            }}
        """
