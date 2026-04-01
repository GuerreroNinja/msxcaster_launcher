import sys
import os
import subprocess
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QFileDialog,
    QHBoxLayout, QVBoxLayout, QWidget, QComboBox, QTextEdit, QSizePolicy
)
from PyQt6.QtGui import QIcon

CAST_EXEC = "cast"
CONFIG_FILE = os.path.expanduser("~/.config/msxcaster_launcher/msxcaster_launcher.json")


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSX CAS Launcher")
        self.setGeometry(300, 300, 900, 500)

        self.cas_path = None
        self.profiles = []
        self.last_dir = ""
        self.last_profile = "default"
        self.initializing_profiles = True

        # ---------------- Crear config si no existe ----------------
        self.ensure_config_exists()

        # ---------------- Widgets ----------------
        self.select_btn = QPushButton("Select CAS")
        self.select_btn.clicked.connect(self.select_cas)

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play)
        self.play_btn.setEnabled(False)

        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.profile_changed)

        self.info_lbl = QLabel("No file loaded")
        self.game_lbl = QLabel("Game: -")
        self.command_lbl = QLabel("Command: -")

        self.cas_info = QTextEdit()
        self.cas_info.setReadOnly(True)
        self.cas_info.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.profile_info = QTextEdit()
        self.profile_info.setReadOnly(True)
        self.profile_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # ---------------- Layout ----------------
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Profile:"))
        top_layout.addWidget(self.profile_combo)
        top_layout.addWidget(self.select_btn)
        top_layout.addWidget(self.play_btn)

        labels_layout = QHBoxLayout()
        labels_layout.addWidget(self.info_lbl)
        labels_layout.addWidget(self.game_lbl)
        labels_layout.addWidget(self.command_lbl)

        # Layout horizontal para CAS info (1/3) y Profile info (2/3)
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.cas_info, 1)  # 1/3
        main_layout.addWidget(self.profile_info, 2)  # 2/3

        # Layout general
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(labels_layout)
        layout.addLayout(main_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # ---------------- Init ----------------
        self.load_config()
        self.load_profiles()
        self.initializing_profiles = False

        # Mostrar info del profile por defecto al iniciar
        if self.profile_combo.currentData():
            self.update_profile_info()

    # ---------------- Crear config si no existe ----------------
    def ensure_config_exists(self):
        folder = os.path.dirname(CONFIG_FILE)
        os.makedirs(folder, exist_ok=True)
        if not os.path.exists(CONFIG_FILE):
            data = {"last_dir": "", "last_profile": "default"}
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump(data, f)
            except Exception as e:
                print(f"Error creando archivo de configuración: {e}")

    # ---------------- Select CAS ----------------
    def select_cas(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CAS", self.last_dir or "", "CAS Files (*.cas)"
        )
        if not path:
            return
        self.cas_path = path
        self.last_dir = os.path.dirname(path)
        # Resaltamos el nombre del archivo
        file_name = os.path.basename(path)
        self.info_lbl.setText(f'Selected: <b><span style="color:blue">{file_name}</span></b>')
        self.extract_game_command()
        self.update_cas_info()
        self.play_btn.setEnabled(True)
        self.save_config()

    # ---------------- Load profiles ----------------
    def load_profiles(self):
        try:
            result = subprocess.run(
                [CAST_EXEC, "profiles"], stdout=subprocess.PIPE, text=True
            )
            self.profiles.clear()
            self.profile_combo.clear()

            for line in result.stdout.splitlines():
                raw = line.strip()
                if not raw or raw.startswith("=") or raw.endswith(":") or "Available" in raw:
                    continue
                parts = raw.split(None, 1)
                name = parts[0]
                desc = parts[1] if len(parts) > 1 else ""
                display = f"{name} — {desc}" if desc else name
                self.profile_combo.addItem(display, name)
                self.profiles.append(name)

            # Seleccionar último profile guardado si existe, sino default
            profile_to_select = self.last_profile if self.last_profile in self.profiles else "default"
            if profile_to_select in self.profiles:
                idx = self.profiles.index(profile_to_select)
                self.profile_combo.setCurrentIndex(idx)

        except Exception:
            # Fallback
            self.profile_combo.addItem("default", "default")
            self.profiles = ["default"]
            self.profile_combo.setCurrentIndex(0)

    # ---------------- Profile changed ----------------
    def profile_changed(self):
        if self.initializing_profiles:
            return
        profile = self.profile_combo.currentData()
        if profile:
            self.last_profile = profile
            self.save_config()
            self.update_profile_info()

    # ---------------- Extract Game / Command ----------------
    def extract_game_command(self):
        if not self.cas_path:
            self.game_lbl.setText("Found: -")
            self.command_lbl.setText("Command: -")
            return
        try:
            result = subprocess.run(
                [CAST_EXEC, "list", self.cas_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True
            )
            lines = result.stdout.splitlines()
            game = "-"
            command = "-"
            for line in lines:
                line = line.strip()
                if line and line[0].isdigit() and "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        game = parts[2]
                        block_type = parts[1]
                        if "BINARY" in block_type.upper():
                            command = 'BLOAD"CAS:",R'
                        elif "ASCII" in block_type.upper():
                            command = 'RUN"CAS:"'
                        else:
                            command = '-'
                        break
            self.game_lbl.setText(f"Found: {game}")
            # Resaltamos el comando
            self.command_lbl.setText(f'Command: <b><span style="color:green">{command}</span></b>')
        except Exception:
            self.game_lbl.setText("Found: -")
            self.command_lbl.setText("Command: -")

    # ---------------- Update CAS Info con coloreado ----------------
    def update_cas_info(self):
        if not self.cas_path:
            self.cas_info.clear()
            return
        try:
            result = subprocess.run(
                [CAST_EXEC, "list", self.cas_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True
            )
            lines = result.stdout.splitlines()
            html_lines = []
            for line in lines:
                l = line.strip()
                if l and "|" in l:
                    parts = [p.strip() for p in l.split("|")]
                    if len(parts) >= 2:
                        block_type = parts[1].upper()
                        if "BINARY" in block_type:
                            color = "blue"
                        elif "ASCII" in block_type:
                            color = "green"
                        else:
                            color = "black"
                        html_line = " | ".join(
                            f'<span style="color:{color}">{p}</span>' if i == 1 else p
                            for i, p in enumerate(parts)
                        )
                        html_lines.append(html_line)
                    else:
                        html_lines.append(l)
                else:
                    html_lines.append(l)
            self.cas_info.setHtml("<pre>"+ "\n".join(html_lines) + "</pre>")
        except Exception as e:
            self.cas_info.setText(f"Error extracting CAS info: {e}")

    # ---------------- Update Profile Info ----------------
    def update_profile_info(self):
        profile = self.profile_combo.currentData()
        self.profile_info.clear()  # borrar contenido anterior
        if profile:
            try:
                result = subprocess.run(
                    [CAST_EXEC, "profiles", profile],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True
                )
                self.profile_info.setText(result.stdout)
            except Exception as e:
                self.profile_info.setText(f"Error fetching profile info: {e}")

    # ---------------- Play ----------------
    def play(self):
        if not self.cas_path:
            return
        profile = self.profile_combo.currentData() or "default"
        cmd = [CAST_EXEC, "play", self.cas_path, "-p", profile]
        terminal_cmd = self.get_terminal_command(cmd)
        subprocess.Popen(terminal_cmd)

    # ---------------- Terminal command ----------------
    def get_terminal_command(self, cmd):
        term_candidates = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm", "lxterminal"]
        for term in term_candidates:
            if subprocess.run(["which", term], stdout=subprocess.DEVNULL).returncode == 0:
                if term in ["gnome-terminal", "xfce4-terminal"]:
                    return [term, "--", *cmd]
                else:
                    return [term, "-e", *cmd]
        return cmd

    # ---------------- Config ----------------
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                data = json.load(open(CONFIG_FILE))
                self.last_dir = data.get("last_dir", "")
                self.last_profile = data.get("last_profile", "default")
            except:
                self.last_dir = ""
                self.last_profile = "default"
        else:
            self.last_dir = ""
            self.last_profile = "default"

    def save_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        data = {"last_dir": self.last_dir, "last_profile": self.last_profile}
        try:
            json.dump(data, open(CONFIG_FILE, "w"))
        except:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec())
