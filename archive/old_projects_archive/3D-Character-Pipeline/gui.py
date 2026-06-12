import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import sys
import json
import traceback
from pathlib import Path
import queue

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def _load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    base_dir = Path(config_path).parent
    config["workspace_dir"] = str(base_dir / config.get("workspace_dir", "./workspace"))
    config["output_dir"] = str(base_dir / config.get("output_dir", "./workspace/output"))
    config["logs_dir"] = str(base_dir / config.get("logs_dir", "./logs"))
    return config


def _show_uv_map_window(uv_path):
    uv_path = Path(uv_path)
    if not uv_path.exists():
        messagebox.showerror("UV Map", f"File not found:\n{uv_path}")
        return

    win = tk.Toplevel()
    win.title("UV Map")
    win.geometry("800x500")

    try:
        from PIL import Image, ImageTk
        img = Image.open(uv_path)
        win_w = win.winfo_screenwidth() * 3 // 4
        ratio = win_w / img.width
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img_resized)
        label = ttk.Label(win, image=tk_img)
        label.image = tk_img
        label.pack(padx=8, pady=8)
        ttk.Label(win, text=f"UV Map — {uv_path.name}",
                  font=("Segoe UI", 9)).pack()
    except ImportError:
        ttk.Label(win, text="UV Map (PIL not available for preview)",
                  font=("Segoe UI", 10, "bold")).pack(pady=12)
        ttk.Label(win, text=f"File: {uv_path}", font=("Segoe UI", 9)).pack(pady=6)
        ttk.Label(win, text="Install Pillow to view images:\n"
                  "  pip install Pillow",
                  font=("Segoe UI", 9), foreground="gray").pack(pady=6)


class PipelineGUI:
    def __init__(self):
        self.args = None
        self.config = None
        self.cancelled = False
        self._queue = queue.Queue()
        self._last_run_dir = None
        self.skin_images = []

        self.root = tk.Tk()
        self.root.title("3D Character Pipeline")
        self.root.geometry("820x640")
        self.root.minsize(600, 480)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Add images and press Start")
        status_label = ttk.Label(main_frame, textvariable=self.status_var,
                                 font=("Segoe UI", 11, "bold"))
        status_label.pack(fill=tk.X, pady=(0, 6))

        self.progress = ttk.Progressbar(main_frame, mode="determinate", value=0)
        self.progress.pack(fill=tk.X, pady=(0, 10))

        input_frame = ttk.LabelFrame(main_frame, text="Input", padding=8)
        input_frame.pack(fill=tk.X, pady=(0, 8))

        face_row = ttk.Frame(input_frame)
        face_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(face_row, text="Face image:", width=12).pack(side=tk.LEFT)
        self.face_image_var = tk.StringVar()
        ttk.Entry(face_row, textvariable=self.face_image_var, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(face_row, text="Browse...",
                   command=self._browse_face).pack(side=tk.RIGHT)

        multi_row = ttk.Frame(input_frame)
        multi_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(multi_row, text="Skin references:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(multi_row, text="Add Images...",
                   command=self._add_skin_images).pack(side=tk.LEFT, padx=(0, 6))
        self.remove_skin_btn = ttk.Button(
            multi_row, text="Remove Selected",
            command=self._remove_skin_selected, state=tk.DISABLED)
        self.remove_skin_btn.pack(side=tk.LEFT)

        self.skin_listbox = tk.Listbox(input_frame, height=4, selectmode=tk.EXTENDED)
        self.skin_listbox.pack(fill=tk.X, pady=(0, 4))
        self.skin_listbox.bind("<<ListboxSelect>>", self._on_skin_select)

        opts_row = ttk.Frame(input_frame)
        opts_row.pack(fill=tk.X)

        self.skip_daz_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_row, text="Skip DAZ Studio",
                        variable=self.skip_daz_var).pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(opts_row, text="Config:").pack(side=tk.LEFT, padx=(0, 4))
        self.config_path_var = tk.StringVar(value="config.json")
        ttk.Combobox(opts_row, textvariable=self.config_path_var,
                      values=["config.json"], width=20, state="readonly").pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.log_area = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12,
            font=("Consolas", 9), state=tk.DISABLED,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self._start_pipeline)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.cancel_btn = ttk.Button(btn_frame, text="Cancel",
                                      command=self._cancel_pipeline, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)

        self.uv_btn = ttk.Button(btn_frame, text="Show UV Map",
                                  command=self._show_uv, state=tk.DISABLED)
        self.uv_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.close_btn = ttk.Button(btn_frame, text="Close", command=self._on_close)
        self.close_btn.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # image management
    # ------------------------------------------------------------------

    def _browse_face(self):
        path = filedialog.askopenfilename(
            title="Select face reference image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*")],
        )
        if path:
            self.face_image_var.set(path)

    def _add_skin_images(self):
        paths = filedialog.askopenfilenames(
            title="Select skin reference images",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*")],
        )
        for p in paths:
            if p not in self.skin_images:
                self.skin_images.append(p)
                self.skin_listbox.insert(tk.END, Path(p).name)
        if self.skin_images:
            self._set_status(f"{len(self.skin_images)} skin reference(s) loaded")

    def _remove_skin_selected(self):
        selected = self.skin_listbox.curselection()
        for i in reversed(selected):
            del self.skin_images[i]
            self.skin_listbox.delete(i)
        self.remove_skin_btn.config(state=tk.DISABLED if not self.skin_images else tk.NORMAL)

    def _on_skin_select(self, event):
        sel = self.skin_listbox.curselection()
        self.remove_skin_btn.config(state=tk.NORMAL if sel else tk.DISABLED)

    def _get_all_skin_paths(self):
        paths = []
        face = self.face_image_var.get().strip()
        if face and Path(face).exists():
            paths.append(face)
        paths.extend(self.skin_images)
        return paths

    # ------------------------------------------------------------------
    # logging / progress
    # ------------------------------------------------------------------

    def _log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def _set_status(self, text):
        self.status_var.set(text)

    def _set_progress(self, value):
        self.progress["value"] = value

    def _progress_callback(self, pct, message):
        self._queue.put(("progress", pct, message))

    def _process_queue(self):
        try:
            while True:
                item = self._queue.get_nowait()
                if item[0] == "progress":
                    _, pct, msg = item
                    self._set_progress(pct)
                    self._set_status(msg)
                    self._log(msg)
                elif item[0] == "result":
                    _, success, run_dir = item
                    self._last_run_dir = run_dir
                    self._on_complete(success)
                elif item[0] == "error":
                    _, msg = item
                    self._log(f"ERROR: {msg}")
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def _show_uv(self):
        if not self._last_run_dir:
            return
        uv_path = Path(self._last_run_dir) / "uv_map.png"
        _show_uv_map_window(uv_path)

    # ------------------------------------------------------------------
    # pipeline lifecycle
    # ------------------------------------------------------------------

    def _start_pipeline(self):
        face_path = self.face_image_var.get().strip()
        if not face_path:
            self._log("ERROR: No face image selected")
            return
        if not Path(face_path).exists():
            self._log(f"ERROR: Face image not found: {face_path}")
            return

        config_path = Path(self.config_path_var.get().strip())
        if not config_path.exists():
            self._log(f"ERROR: Config not found: {config_path}")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.uv_btn.config(state=tk.DISABLED)
        self.cancelled = False
        self._set_progress(0)
        self._set_status("Starting pipeline...")
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state=tk.DISABLED)

        config = _load_config(config_path)
        skip_daz = self.skip_daz_var.get()
        all_skin = self._get_all_skin_paths()

        def task():
            try:
                from pipeline import check_dependencies, setup_logging
                check_dependencies()

                log_dir = Path(config["logs_dir"])
                setup_logging(log_dir)

                import argparse
                ns = argparse.Namespace(
                    image=face_path,
                    batch=None,
                    multi_images=",".join(all_skin) if len(all_skin) > 1 else None,
                    config=str(config_path),
                    skip_daz=skip_daz,
                    dry_run=False,
                    preview=False,
                    gui=False,
                    parallel=False,
                    no_cache=False,
                    keep_going=False,
                )

                if ns.multi_images:
                    self._queue.put(("progress", 0,
                                     f"Multi-image mode: {len(all_skin)} sources"))

                from pipeline import run_pipeline
                success, run_dir = run_pipeline(ns, config, self._progress_callback)
                self._queue.put(("result", success, run_dir))
            except Exception as e:
                tb = traceback.format_exc()
                self._queue.put(("error", f"{e}\n{tb}"))
                self._queue.put(("result", False, None))

        self._thread = threading.Thread(target=task, daemon=True)
        self._thread.start()

    def _cancel_pipeline(self):
        self.cancelled = True
        self._set_status("Cancelling...")
        self._log("Pipeline cancelled by user")
        self.cancel_btn.config(state=tk.DISABLED)

    def _on_close(self):
        self.cancelled = True
        self.root.destroy()

    def _on_complete(self, success):
        self.cancel_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        if success:
            self._set_status("Pipeline completed successfully")
            self._log("=" * 60)
            self._log("PIPELINE COMPLETED SUCCESSFULLY")
            if self._last_run_dir:
                self._log(f"Output: {self._last_run_dir}")
                uv = Path(self._last_run_dir) / "uv_map.png"
                if uv.exists():
                    self.uv_btn.config(state=tk.NORMAL)
                    self._log(f"UV map: {uv}")
            self._log("=" * 60)
        else:
            self._set_status("Pipeline failed - check log for details")
            self._log("=" * 60)
            self._log("PIPELINE FAILED")
            self._log("=" * 60)
        self._set_progress(100 if success else 0)

    def run(self):
        self.root.after(100, self._process_queue)
        self.root.mainloop()
        return 0


if __name__ == "__main__":
    gui = PipelineGUI()
    sys.exit(gui.run())
