import os, sys, time, threading, queue, subprocess, pathlib, tkinter as tk
from tkinter import filedialog, messagebox

# Check for display
try:
    test_root = tk.Tk()
    test_root.destroy()
except tk.TclError as e:
    print(f"No display available: {e}")
    sys.exit(1)

BASE = pathlib.Path(__file__).resolve().parent
SCRATCH = BASE / "tests" / "_scratch.kid"
RUNNER = BASE / "kidlang.py"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KidLang Mini IDE")
        self.geometry("1100x700")

        self.proc = None
        self.q = queue.Queue()
        self.current_file = None

        top = tk.Frame(self)
        top.pack(fill="x")

        self.btn_open = tk.Button(top, text="Open", command=self.open_file)
        self.btn_open.pack(side="left", padx=4, pady=4)

        self.btn_save = tk.Button(top, text="Save", command=self.save_file)
        self.btn_save.pack(side="left", padx=4, pady=4)

        self.btn_save_as = tk.Button(top, text="Save As", command=self.save_as)
        self.btn_save_as.pack(side="left", padx=4, pady=4)

        self.btn_run = tk.Button(top, text="Run", command=self.run_code)
        self.btn_run.pack(side="left", padx=12, pady=4)

        self.btn_stop = tk.Button(top, text="Stop", command=self.stop_run, state="disabled")
        self.btn_stop.pack(side="left", padx=4, pady=4)

        self.step_var = tk.BooleanVar(value=False)
        self.chk_step = tk.Checkbutton(top, text="Step mode", variable=self.step_var)
        self.chk_step.pack(side="left", padx=10)

        mid = tk.PanedWindow(self, orient="vertical", sashrelief="raised")
        mid.pack(fill="both", expand=True)

        editor_frame = tk.Frame(mid)
        output_frame = tk.Frame(mid)

        mid.add(editor_frame, stretch="always")
        mid.add(output_frame, stretch="always")

        self.editor = tk.Text(editor_frame, undo=True, wrap="none")
        self.editor.pack(fill="both", expand=True, side="left")

        ed_scroll_y = tk.Scrollbar(editor_frame, command=self.editor.yview)
        ed_scroll_y.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=ed_scroll_y.set)

        self.output = tk.Text(output_frame, height=12, wrap="word", bg="#0f0f0f", fg="#e8e8e8")
        self.output.pack(fill="both", expand=True, side="top")

        out_scroll_y = tk.Scrollbar(output_frame, command=self.output.yview)
        out_scroll_y.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=out_scroll_y.set)

        bottom = tk.Frame(output_frame)
        bottom.pack(fill="x")

        tk.Label(bottom, text="stdin:").pack(side="left", padx=4)
        self.stdin_entry = tk.Entry(bottom)
        self.stdin_entry.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.stdin_entry.bind("<Return>", self.send_stdin)

        self.btn_send = tk.Button(bottom, text="Send", command=self.send_stdin_btn)
        self.btn_send.pack(side="left", padx=4)

        self._seed_text()
        self.after(50, self._drain_queue)

    def _seed_text(self):
        if self.editor.get("1.0", "end-1c").strip():
            return
        demo = (
            'say("Welcome!")\n'
            'let name = ask("Your name? ")\n'
            'say("Hello " + name)\n'
            '\n'
            'repeat 3 times\n'
            '  say("Repeat!")\n'
            'end\n'
            '\n'
            'let x = 1\n'
            'while x <= 5 do\n'
            '  if x == 3 then\n'
            '    say("three")\n'
            '  else\n'
            '    say(x)\n'
            '  end\n'
            '  x = x + 1\n'
            'end\n'
        )
        self.editor.insert("1.0", demo)

    def write_out(self, s):
        self.output.insert("end", s)
        self.output.see("end")

    def clear_out(self):
        self.output.delete("1.0", "end")

    def open_file(self):
        path = filedialog.askopenfilename(
            initialdir=str(BASE),
            filetypes=[("KidLang files", "*.kid"), ("All files", "*.*")]
        )
        if not path:
            return
        p = pathlib.Path(path)
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))
            return
        self.current_file = p
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", txt)
        self.write_out(f"\n[opened] {p}\n")

    def save_file(self):
        if self.current_file is None:
            return self.save_as()
        try:
            self.current_file.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return
        self.write_out(f"\n[saved] {self.current_file}\n")

    def save_as(self):
        path = filedialog.asksaveasfilename(
            initialdir=str(BASE),
            defaultextension=".kid",
            filetypes=[("KidLang files", "*.kid"), ("All files", "*.*")]
        )
        if not path:
            return
        self.current_file = pathlib.Path(path)
        self.save_file()

    def _ensure_scratch(self):
        SCRATCH.parent.mkdir(parents=True, exist_ok=True)
        SCRATCH.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")

    def run_code(self):
        if not RUNNER.exists():
            messagebox.showerror("Missing kidlang.py", f"Not found: {RUNNER}")
            return
        if self.proc is not None:
            self.write_out("\n[busy] already running\n")
            return

        self._ensure_scratch()
        self.clear_out()

        args = [sys.executable, str(RUNNER), str(SCRATCH)]
        if self.step_var.get():
            args.append("--step")

        self.write_out(f"[run] {' '.join(args)}\n\n")

        try:
            self.proc = subprocess.Popen(
                args,
                cwd=str(BASE),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        except Exception as e:
            self.proc = None
            self.write_out(f"[error] {e}\n")
            return

        self.btn_run.config(state="disabled")
        self.btn_stop.config(state="normal")

        t = threading.Thread(target=self._reader_thread, daemon=True)
        t.start()

    def _reader_thread(self):
        p = self.proc
        try:
            for line in p.stdout:
                self.q.put(line)
        except Exception as e:
            self.q.put(f"\n[io error] {e}\n")
        finally:
            try:
                rc = p.wait(timeout=0.2)
            except Exception:
                rc = None
            self.q.put(f"\n[exit] {rc}\n")
            self.q.put(("__DONE__",))

    def _drain_queue(self):
        try:
            while True:
                item = self.q.get_nowait()
                if item == ("__DONE__",) or item == "__DONE__":
                    self.proc = None
                    self.btn_run.config(state="normal")
                    self.btn_stop.config(state="disabled")
                    break
                self.write_out(str(item))
        except queue.Empty:
            pass
        self.after(50, self._drain_queue)

    def stop_run(self):
        if self.proc is None:
            return
        try:
            self.proc.kill()
        except Exception:
            pass
        self.write_out("\n[stopped]\n")

    def send_stdin_btn(self):
        self.send_stdin(None)

    def send_stdin(self, _evt):
        if self.proc is None or self.proc.stdin is None:
            return
        s = self.stdin_entry.get()
        self.stdin_entry.delete(0, "end")
        try:
            self.proc.stdin.write(s + "\n")
            self.proc.stdin.flush()
        except Exception:
            pass

if __name__ == "__main__":
    App().mainloop()
