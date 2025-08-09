# runner.py
# Executes shell commands. Supports PTY mode for interactive commands and option to run in system terminal.
import os
import subprocess
import threading
import time
import shlex
import pty
import select

class CommandRunner:
    def __init__(self, on_output=None, on_finished=None, logs_dir=None):
        # on_output(line: str)
        self.on_output = on_output
        self.on_finished = on_finished
        self.process = None
        self._stop_requested = False
        self.logs_dir = logs_dir or os.path.join(os.getcwd(), "logs")
        os.makedirs(self.logs_dir, exist_ok=True)

    def _save_log(self, name, content):
        ts = time.strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in name if c.isalnum() or c in "._-")[:50]
        fn = os.path.join(self.logs_dir, f"{safe}_{ts}.log")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(content)
        return fn

    def run(self, cmd, use_pty=True, cwd=None, run_in_terminal=False, terminal_cmd=None):
        # If run_in_terminal is True, open an external terminal and run command there (linux-specific)
        if run_in_terminal:
            # Try common terminal emulators
            terminals = [
                ["gnome-terminal", "--"],
                ["konsole", "-e"],
                ["x-terminal-emulator", "-e"],
                ["xterm", "-e"],
                ["alacritty", "-e"],
                ["tilix", "-e"],
            ]
            for term in terminals:
                try:
                    full = term + ["/bin/bash", "-lc", cmd]
                    subprocess.Popen(full)
                    if self.on_output:
                        self.on_output(f"[runner] opened external terminal: {' '.join(term)}\n")
                    if self.on_finished:
                        self.on_finished(0)
                    return None
                except Exception:
                    continue
            # fallback to running normally
        if not use_pty:
            return self._run_simple(cmd, cwd)
        else:
            return self._run_pty(cmd, cwd)

    def _run_simple(self, cmd, cwd):
        # simple subprocess capture (not interactive)
        def target():
            try:
                self.process = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, executable='/bin/bash')
                out = []
                for line in self.process.stdout:
                    out.append(line)
                    if self.on_output:
                        self.on_output(line)
                self.process.wait()
                if self.on_finished:
                    self.on_finished(self.process.returncode)
                self._save_log("command", "".join(out))
            except Exception as e:
                if self.on_output:
                    self.on_output(f"[runner error] {e}\\n")
                if self.on_finished:
                    self.on_finished(-1)
        t = threading.Thread(target=target, daemon=True)
        t.start()
        return t

    def _run_pty(self, cmd, cwd):
        # Run command with a PTY so interactive programs can be used.
        def target():
            try:
                master_fd, slave_fd = pty.openpty()
                # Start process attached to slave fd
                self.process = subprocess.Popen(cmd, cwd=cwd, shell=True, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, universal_newlines=True, bufsize=0, executable='/bin/bash')
                os.close(slave_fd)
                output_buf = []
                while True:
                    r, _, _ = select.select([master_fd], [], [], 0.1)
                    if master_fd in r:
                        try:
                            data = os.read(master_fd, 1024)
                            if not data:
                                break
                            text = data.decode(errors='ignore')
                            output_buf.append(text)
                            if self.on_output:
                                self.on_output(text)
                        except OSError:
                            break
                    if self.process.poll() is not None:
                        break
                    if self._stop_requested:
                        try:
                            self.process.terminate()
                        except Exception:
                            pass
                        break
                # read remaining
                try:
                    while True:
                        data = os.read(master_fd, 1024)
                        if not data:
                            break
                        text = data.decode(errors='ignore')
                        output_buf.append(text)
                        if self.on_output:
                            self.on_output(text)
                except Exception:
                    pass
                if self.process:
                    rc = self.process.poll()
                else:
                    rc = -1
                if self.on_finished:
                    self.on_finished(rc)
                self._save_log("command", "".join(output_buf))
            except Exception as e:
                if self.on_output:
                    self.on_output(f"[pty runner error] {e}\\n")
                if self.on_finished:
                    self.on_finished(-1)
        self._stop_requested = False
        t = threading.Thread(target=target, daemon=True)
        t.start()
        return t

    def stop(self):
        self._stop_requested = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
