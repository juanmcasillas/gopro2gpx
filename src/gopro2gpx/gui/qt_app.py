import argparse
import configparser
import os
import sys
from typing import Callable

from PyQt6.QtCore import QObject, QThread, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gopro2gpx.gopro2gpx import main_core
from gopro2gpx.gui.i18n import load_texts


class SignalWriter:
    def __init__(self, emit: Callable[[str], None]):
        self._emit = emit

    def write(self, text: str) -> None:
        if text:
            self._emit(text)

    def flush(self) -> None:
        return


class ProcessingWorker(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    error = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(self, jobs: list[argparse.Namespace], verbose_enabled: bool):
        super().__init__()
        self.jobs = jobs
        self.verbose_enabled = verbose_enabled

    def run(self) -> None:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_exit = sys.exit
        try:
            sys.exit = lambda code=0: None
            if self.verbose_enabled:
                sys.stdout = SignalWriter(self.log.emit)
                sys.stderr = SignalWriter(self.log.emit)

            total = len(self.jobs)
            for index, job in enumerate(self.jobs, start=1):
                try:
                    main_core(job)
                except SystemExit:
                    pass
                except Exception as exc:
                    self.error.emit(str(exc))
                finally:
                    self.progress.emit(index, total)
        finally:
            sys.exit = old_exit
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.done.emit()


class GoPro2GPXMainWindow(QMainWindow):
    def __init__(self, language: str | None = None):
        super().__init__()
        self.t = load_texts(language)

        self.config_path = self._config_path()
        self.config_parser = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.config_parser.read(self.config_path)
        if "Paths" not in self.config_parser:
            self.config_parser["Paths"] = {}

        self.last_video_dir = self.config_parser["Paths"].get("last_video_dir", "C:\\")
        self.last_output_dir = self.config_parser["Paths"].get("last_output_dir", "C:\\")

        self.setWindowTitle(self.t["title"])
        self.resize(800, 400)

        self._thread: QThread | None = None
        self._worker: ProcessingWorker | None = None

        self._build_ui()

    @staticmethod
    def _config_path() -> str:
        if os.name == "nt":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
            conf_dir = os.path.join(base, "gopro2gpx")
        else:
            conf_dir = os.path.join(os.path.expanduser("~"), ".config", "gopro2gpx")
        os.makedirs(conf_dir, exist_ok=True)
        return os.path.join(conf_dir, "gui.ini")

    def _build_ui(self) -> None:
        tabs = QTabWidget()
        tabs.currentChanged.connect(self._on_tab_change)

        descriptor_widget = self._build_descriptor_tab()
        main_widget = self._build_main_tab()

        tabs.addTab(descriptor_widget, self.t["descriptor_tab"])
        tabs.addTab(main_widget, self.t["main_tab"])

        self.setCentralWidget(tabs)

    def _build_descriptor_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        browser = QLabel()
        browser.setTextFormat(Qt.TextFormat.RichText)
        browser.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        browser.setOpenExternalLinks(False)
        browser.linkActivated.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
        browser.setWordWrap(True)
        browser.setText(self.t["about_html"])

        layout.addWidget(browser)
        return widget

    def _build_main_tab(self) -> QWidget:
        widget = QWidget()
        root = QVBoxLayout(widget)

        paths_box = QGroupBox(self.t["paths"])
        paths_layout = QGridLayout(paths_box)

        self.input_dir_edit = QLineEdit()
        self.output_dir_edit = QLineEdit()

        browse_input = QPushButton(self.t["browse"])
        browse_input.clicked.connect(self._select_input_dir)
        browse_output = QPushButton(self.t["browse"])
        browse_output.clicked.connect(self._select_output_dir)

        paths_layout.addWidget(QLabel(self.t["video_dir"]), 0, 0)
        paths_layout.addWidget(self.input_dir_edit, 0, 1)
        paths_layout.addWidget(browse_input, 0, 2)
        paths_layout.addWidget(QLabel(self.t["output_dir"]), 1, 0)
        paths_layout.addWidget(self.output_dir_edit, 1, 1)
        paths_layout.addWidget(browse_output, 1, 2)

        options_box = QGroupBox(self.t["options"])
        options_layout = QFormLayout(options_box)

        self.verbose_checkbox = QCheckBox(self.t["verbose"])
        self.verbose_checkbox.setChecked(True)
        self.binary_checkbox = QCheckBox(self.t["binary"])
        self.skip_checkbox = QCheckBox(self.t["skip"])
        self.skip_checkbox.setChecked(True)
        self.skip_dop_checkbox = QCheckBox(self.t["skip_dop"])

        self.dop_limit_spin = QSpinBox()
        self.dop_limit_spin.setRange(0, 100000)
        self.dop_limit_spin.setValue(2000)

        options_layout.addRow(self.verbose_checkbox)
        options_layout.addRow(self.binary_checkbox)
        options_layout.addRow(self.skip_checkbox)
        options_layout.addRow(self.skip_dop_checkbox)
        options_layout.addRow(self.t["dop_limit"], self.dop_limit_spin)

        output_box = QGroupBox(self.t["output_format"])
        output_layout = QHBoxLayout(output_box)
        output_layout.addWidget(QLabel(self.t["select_format"]))
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["GPX", "CSV", "KML"])
        output_layout.addWidget(self.output_format_combo)

        camera_box = QGroupBox(self.t["camera"])
        camera_layout = QHBoxLayout(camera_box)
        camera_layout.addWidget(QLabel(self.t["select_camera"]))
        self.camera_combo = QComboBox()
        self.camera_combo.addItems([self.t["camera_old"], self.t["camera_new"]])
        camera_layout.addWidget(self.camera_combo)

        self.process_button = QPushButton(self.t["process"])
        self.process_button.clicked.connect(self._on_process)

        progress_box = QGroupBox(self.t["progress"])
        progress_layout = QVBoxLayout(progress_box)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        progress_layout.addWidget(self.progress)

        verbose_box = QGroupBox(self.t["verbose_output"])
        verbose_layout = QVBoxLayout(verbose_box)
        self.verbose_output = QPlainTextEdit()
        self.verbose_output.setReadOnly(True)
        verbose_layout.addWidget(self.verbose_output)

        root.addWidget(paths_box)
        root.addWidget(options_box)
        root.addWidget(output_box)
        root.addWidget(camera_box)
        root.addWidget(self.process_button)
        root.addWidget(progress_box)
        root.addWidget(verbose_box, stretch=1)

        return widget

    def _on_tab_change(self, index: int) -> None:
        if index == 0:
            self.resize(650, 300)
        else:
            self.resize(800, 650)

    def _select_input_dir(self) -> None:
        current = self.input_dir_edit.text().strip() or self.last_video_dir
        selected = QFileDialog.getExistingDirectory(self, self.t["select_video"], current)
        if selected:
            self.input_dir_edit.setText(selected)
            self.last_video_dir = selected
            self._save_config()

    def _select_output_dir(self) -> None:
        current = self.output_dir_edit.text().strip() or self.last_output_dir
        selected = QFileDialog.getExistingDirectory(self, self.t["select_output"], current)
        if selected:
            self.output_dir_edit.setText(selected)
            self.last_output_dir = selected
            self._save_config()

    def _save_config(self) -> None:
        self.config_parser["Paths"]["last_video_dir"] = self.last_video_dir
        self.config_parser["Paths"]["last_output_dir"] = self.last_output_dir
        with open(self.config_path, "w", encoding="utf-8") as configfile:
            self.config_parser.write(configfile)

    def _on_process(self) -> None:
        input_dir = self.input_dir_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()

        if not input_dir:
            QMessageBox.critical(self, self.t["error"], self.t["missing_video"])
            return
        if not output_dir:
            QMessageBox.critical(self, self.t["error"], self.t["missing_output"])
            return

        video_files = [
            os.path.join(input_dir, name)
            for name in sorted(os.listdir(input_dir))
            if name.lower().endswith((".mp4", ".mov", ".avi"))
        ]
        if not video_files:
            QMessageBox.critical(self, self.t["error"], self.t["no_videos"])
            return

        selected_format = self.output_format_combo.currentText()

        jobs = []
        for video_file in video_files:
            output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(video_file))[0])
            args = argparse.Namespace()
            args.verbose = 1 if self.verbose_checkbox.isChecked() else 0
            args.binary = self.binary_checkbox.isChecked()
            args.skip = self.skip_checkbox.isChecked()
            args.skip_dop = self.skip_dop_checkbox.isChecked()
            args.dop_limit = self.dop_limit_spin.value()
            args.files = [video_file]
            args.outputfile = output_file
            args.gui = True
            args.time_shift = 0

            args.gpx = selected_format == "GPX"
            args.csv = selected_format == "CSV"
            args.kml = selected_format == "KML"
            jobs.append(args)

        self.progress.setMaximum(len(jobs))
        self.progress.setValue(0)
        self.verbose_output.clear()
        self.process_button.setEnabled(False)

        self._thread = QThread(self)
        self._worker = ProcessingWorker(jobs, self.verbose_checkbox.isChecked())
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._on_done)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _append_log(self, text: str) -> None:
        self.verbose_output.insertPlainText(text)

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, self.t["error"], message)

    def _on_done(self) -> None:
        self.process_button.setEnabled(True)
        QMessageBox.information(self, self.t["completed_title"], self.t["completed_msg"])


def run_app(language: str | None = None) -> int:
    app = QApplication(sys.argv)
    window = GoPro2GPXMainWindow(language=language)
    window.show()
    return app.exec()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en", "es"], default=None, help="UI language override")
    args = parser.parse_args()
    return run_app(language=args.lang)


if __name__ == "__main__":
    raise SystemExit(main())
