# main.py
import sys, os, json, time, shutil
from PySide6 import QtCore, QtGui, QtWidgets
from commands import COMMANDS
from runner import CommandRunner

APP_TITLE = "Recon to Master — Bug Bounty GUI (Upgraded)"
CONFIG_FILE = "config.json"

class IconDelegate(QtWidgets.QStyledItemDelegate):
    # optional custom delegate to show icons (no-op for now)
    pass

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 750)
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.config = self.load_config()
        self.runner = CommandRunner(on_output=self.append_output, on_finished=self.on_cmd_finished, logs_dir=self.logs_dir)
        self._build_ui()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        top_row = QtWidgets.QHBoxLayout()
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search tools or commands...")
        self.search.textChanged.connect(self.on_search_change)
        top_row.addWidget(self.search)

        self.fav_btn = QtWidgets.QPushButton("★ Favorites")
        self.fav_btn.setCheckable(True)
        self.fav_btn.clicked.connect(self.on_fav_toggle)
        top_row.addWidget(self.fav_btn)

        self.terminal_toggle = QtWidgets.QCheckBox("Run in external terminal")
        top_row.addWidget(self.terminal_toggle)

        self.pty_toggle = QtWidgets.QCheckBox("Use PTY (interactive)")
        self.pty_toggle.setChecked(True)
        top_row.addWidget(self.pty_toggle)

        main_layout.addLayout(top_row)

        splitter = QtWidgets.QSplitter()
        main_layout.addWidget(splitter, 1)

        # Left - categories
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        self.cat_list = QtWidgets.QListWidget()
        self.cat_list.addItems(sorted(COMMANDS.keys()))
        self.cat_list.currentItemChanged.connect(self.on_category_changed)
        left_layout.addWidget(QtWidgets.QLabel("Categories"))
        left_layout.addWidget(self.cat_list)
        splitter.addWidget(left_widget)

        # Middle - tools
        mid_widget = QtWidgets.QWidget()
        mid_layout = QtWidgets.QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0,0,0,0)
        mid_layout.addWidget(QtWidgets.QLabel("Tools / Commands"))
        self.tool_list = QtWidgets.QListWidget()
        self.tool_list.currentItemChanged.connect(self.on_tool_changed)
        mid_layout.addWidget(self.tool_list)
        splitter.addWidget(mid_widget)

        # Right - command preview & output
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)

        form = QtWidgets.QFormLayout()
        self.target_input = QtWidgets.QLineEdit()
        self.target_input.setPlaceholderText("example.com or comma-separated targets")
        form.addRow("Target(s):", self.target_input)
        self.extra_input = QtWidgets.QLineEdit()
        self.extra_input.setPlaceholderText("Extra placeholders (json) e.g. {\"cidr\":\"1.2.3.0/24\"}")
        form.addRow("Extras:", self.extra_input)
        right_layout.addLayout(form)

        self.command_preview = QtWidgets.QPlainTextEdit()
        self.command_preview.setPlaceholderText("Command preview (edited before run)")
        right_layout.addWidget(self.command_preview)

        btn_row = QtWidgets.QHBoxLayout()
        self.run_btn = QtWidgets.QPushButton("Run")
        self.run_btn.clicked.connect(self.run_command)
        self.copy_btn = QtWidgets.QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_command)
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_command)
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.stop_btn)
        right_layout.addLayout(btn_row)

        # progress spinner
        self.spinner = QtWidgets.QLabel()
        movie = QtGui.QMovie(os.path.join("resources","spinner.gif")) if os.path.exists(os.path.join("resources","spinner.gif")) else None
        if movie:
            self.spinner.setMovie(movie)
            movie.start()
        else:
            self.spinner.setText("")

        right_layout.addWidget(self.spinner)

        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        right_layout.addWidget(QtWidgets.QLabel("Output:"))
        right_layout.addWidget(self.output, 1)

        splitter.addWidget(right_widget)
        splitter.setSizes([200, 300, 700])

        # status bar
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        # initial selection
        if self.cat_list.count() > 0:
            self.cat_list.setCurrentRow(0)
            self.on_category_changed()

        self.apply_dark_theme()

    def on_search_change(self, txt):
        txt = txt.lower().strip()
        # filter categories and tools
        for i in range(self.cat_list.count()):
            cat = self.cat_list.item(i)
            cat.setHidden(False)
        # filter tools within current category
        for i in range(self.tool_list.count()):
            it = self.tool_list.item(i)
            it.setHidden(txt not in it.text().lower())

    def on_fav_toggle(self, checked=False):
        # show favorites by moving favorite items to top
        # favorites stored in config as list of "Category::Tool" strings
        favs = set(self.config.get("favorites", []))
        self.tool_list.clear()
        cat_item = self.cat_list.currentItem()
        if not cat_item:
            return
        tools = COMMANDS.get(cat_item.text(), {})
        # order favorites first
        favored = []
        others = []
        for t in sorted(tools.keys()):
            key = f"{cat_item.text()}::{t}"
            if key in favs:
                favored.append(t)
            else:
                others.append(t)
        for t in favored + others:
            self.tool_list.addItem(t)

    def on_category_changed(self):
        self.tool_list.clear()
        item = self.cat_list.currentItem()
        if not item:
            return
        tools = COMMANDS.get(item.text(), {})
        for t in sorted(tools.keys()):
            self.tool_list.addItem(t)

    def on_tool_changed(self):
        cat_item = self.cat_list.currentItem()
        tool_item = self.tool_list.currentItem()
        if not cat_item or not tool_item:
            self.command_preview.setPlainText("")
            return
        cmd = COMMANDS[cat_item.text()][tool_item.text()]
        self.command_preview.setPlainText(cmd)

    def run_command(self):
        cmd_template = self.command_preview.toPlainText().strip()
        if not cmd_template:
            QtWidgets.QMessageBox.warning(self, "No command", "No command to run. Select a tool and target first.")
            return
        targets = self.target_input.text().strip()
        extras_txt = self.extra_input.text().strip()
        extras = {}
        if extras_txt:
            try:
                extras = json.loads(extras_txt)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Extras parse error", f"Extras must be JSON. Error: {e}")
                return
        # simple replacement logic
        cmd = cmd_template
        if "{target}" in cmd and not targets:
            QtWidgets.QMessageBox.warning(self, "Missing target", "Command requires {target}. Please provide a target.")
            return
        if targets:
            # replace for single target only in preview; for list execution we will run per target
            single = targets.split(",")[0].strip()
            cmd = cmd.replace("{target}", single)
        for k,v in extras.items():
            cmd = cmd.replace("{" + k + "}", str(v))
        # confirm
        reply = QtWidgets.QMessageBox.question(self, "Confirm Run", f"Run the following command?\n\n{cmd}", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply != QtWidgets.QMessageBox.Yes:
            return
        # run per-target if comma-separated and if template contains {target}
        run_in_terminal = self.terminal_toggle.isChecked()
        use_pty = self.pty_toggle.isChecked()
        if "{target}" in cmd_template and targets and "," in targets:
            self.output.appendPlainText(f"[runner] launching for multiple targets: {targets}\\n")
            for t in [x.strip() for x in targets.split(",") if x.strip()]:
                c = cmd_template.replace("{target}", t)
                for k,v in extras.items():
                    c = c.replace("{" + k + "}", str(v))
                self.output.appendPlainText(f"$ {c}\\n")
                self.runner.run(c, use_pty=use_pty, run_in_terminal=run_in_terminal)
                time.sleep(0.1)
        else:
            self.output.appendPlainText(f"$ {cmd}\\n")
            self.runner.run(cmd, use_pty=use_pty, run_in_terminal=run_in_terminal)

    def copy_command(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.command_preview.toPlainText())

    def stop_command(self):
        self.runner.stop()

    def append_output(self, data):
        # called from runner thread; use invokeMethod to update GUI thread
        QtCore.QMetaObject.invokeMethod(self, "_append", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, data))

    @QtCore.Slot(str)
    def _append(self, data):
        self.output.moveCursor(QtGui.QTextCursor.End)
        self.output.insertPlainText(data)
        self.output.moveCursor(QtGui.QTextCursor.End)

    def on_cmd_finished(self, code):
        QtCore.QMetaObject.invokeMethod(self, "_finished", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(int, code))

    @QtCore.Slot(int)
    def _finished(self, code):
        self.output.appendPlainText(f"\\n[Process exited with code {code}]\\n")

    def apply_dark_theme(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(30,30,30))
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(220,220,220))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(20,20,20))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(45,45,45))
        palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255,255,255))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(220,220,220))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(45,45,45))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(220,220,220))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(38,79,120))
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255,255,255))
        self.setPalette(palette)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
