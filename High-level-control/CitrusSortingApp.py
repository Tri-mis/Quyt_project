import os
import threading
import time
import csv
import random
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import ttkbootstrap as tb
import joblib
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS_DIR = os.path.join(BASE_DIR, "models")
PRESETS_DIR = os.path.join(BASE_DIR, "presets")
LIBS_DIR = os.path.join(BASE_DIR, "libs")
WRAPPERS_DIR = os.path.join(BASE_DIR, "wrappers")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----- Configuration file handling -----
PRESET_FILENAME = os.path.join(PRESETS_DIR, "presets.txt")

# ----- Prediction model and preprocessing -----
MODEL_PATH = os.path.join(MODELS_DIR, "citrus_brix_model.pkl")
SCALER_PATH = os.path.join(MODELS_DIR,"citrus_brix_scaler.pkl")

default_presets = {
    "save_measured_data": "True",
    "save_data_path": OUTPUT_DIR,
    "preset_measure_times": "4",
    "current_fruit_number": "1",
    "preset_conveyor_speed": "50"
}

def load_presets(filename=PRESET_FILENAME):
    if not os.path.exists(filename):
        save_presets(filename, default_presets)
        return dict(default_presets)
    d = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    # ensure defaults for missing keys
    for k, v in default_presets.items():
        if k not in d:
            d[k] = v
    return d

def save_presets(filename=PRESET_FILENAME, presets=None):
    if presets is None:
        presets = default_presets
    with open(filename, "w", encoding="utf-8") as f:
        for k, v in presets.items():
            f.write(f"{k}={v}\n")

# ----- Helper: Thread-safe logger queue for UI -----
log_queue = queue.Queue()

def enqueue_log(text):
    log_queue.put(text)

# ----- Main Application -----
class CitrusSortingApp:
    def __init__(self, root):
        self.root = root
        root.title("NIR Control App")

        # load presets
        presets = load_presets()
        self.save_measured_data = tk.BooleanVar(value=(presets["save_measured_data"].lower() == "true"))
        self.save_data_path = tk.StringVar(value=presets["save_data_path"])
        self.preset_measure_times = tk.IntVar(value=int(presets["preset_measure_times"]))
        self.current_fruit_number = tk.IntVar(value=int(presets["current_fruit_number"]))
        self.preset_conveyor_speed = tk.IntVar(value=int(presets["preset_conveyor_speed"]))

        # ESP and NIR state
        self.esp_serial = None
        self.esp_connected = False
        self.nir = None
        self.nir_connected = False
        self.esp_listen_thread = None
        self.esp_stop_event = threading.Event()

        # UI setup
        self._build_ui()

        # Matplotlib data placeholders
        self.current_wavelength = []
        self.current_spectrum = []

        # start periodic UI update for log queue
        self.root.after(100, self._poll_log_queue)

        # start communications
        self._start_communications()

        # prediction model and preprocessing
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)

    def _build_ui(self):
        # === Main wrapper ===
        # <-- BORDER ADDED
        frm_main = ttk.Frame(self.root, padding=8, borderwidth=1, relief="solid")
        frm_main.pack(fill="both", expand=True)

        # --- Top row: frm_top ---
        # <-- BORDER ADDED
        frm_top = ttk.Frame(frm_main, borderwidth=1, relief="solid")
        frm_top.pack(fill="x", expand=True)

        # Left = controls
        # <-- BORDER ADDED
        frm_left = ttk.Frame(frm_top, padding=8, width=800, borderwidth=1, relief="solid")
        frm_left.pack(side="left", anchor="n")
        
        # Divider
        divider = ttk.Separator(frm_top, orient="vertical")
        divider.pack(side="left", fill="y", padx=5)

        # Right = graph
        # <-- BORDER ADDED
        frm_right = ttk.Frame(frm_top, padding=(20, 20, 20, 20), width = 800, borderwidth=1, relief="solid")
        frm_right.pack(side="left", fill="both", expand=True)
        frm_right.pack_propagate(False)

        divider = ttk.Separator(frm_main, orient="horizontal")
        # Changed side to "bottom" so it appears *before* the bottom frame
        divider.pack(side="bottom", fill="x", padx=5, pady=5)

        # === BOTTOM ROW (log only) ===
        # <-- BORDER ADDED
        frm_bottom = ttk.Frame(frm_main, padding=(8, 8, 8, 8), borderwidth=1, relief="solid")
        frm_bottom.pack(side="bottom", fill="x")

        # -------------------------------------------------------
        # ------- PLACE ALL LEFT-SIDE CONTROLS IN frm_left --
        # -------------------------------------------------------

        frm_controls = ttk.Frame(frm_left)
        frm_controls.pack(fill="x")
        frm_controls.columnconfigure(0, weight=1)

        r = 0
        chk = ttk.Checkbutton(frm_controls, text="Save measured data",
                            variable=self.save_measured_data)
        chk.grid(row=r, column=0, sticky="w", pady=(20,20))
        r += 1

        ttk.Label(frm_controls, text="Save data path:").grid(row=r, column=0, sticky="w", pady=(8,2))
        r += 1
        ent_path = ttk.Entry(frm_controls, textvariable=self.save_data_path, width=40)
        ent_path.grid(row=r, column=0, sticky="we")
        ttk.Button(frm_controls, text="Browse", command=self._browse_save_path)\
            .grid(row=r, column=1, padx=4, sticky="w")
        r += 1

        ttk.Label(frm_controls, text="Preset measure times:").grid(row=r, column=0, sticky="w", pady=(8,2))
        r += 1
        ent_times = ttk.Entry(frm_controls, textvariable=self.preset_measure_times, width=12)
        ent_times.grid(row=r, column=0, sticky="w")
        r += 1

        ttk.Label(frm_controls, text="Current fruit number:").grid(row=r, column=0, sticky="w", pady=(8,2))
        r += 1
        ent_first = ttk.Entry(frm_controls, textvariable=self.current_fruit_number, width=12)
        ent_first.grid(row=r, column=0, sticky="w", pady=(0,20))
        r += 1

        # Slider & speed label row
        self._speed_label_var = tk.StringVar(
            value=f"Preset conveyor speed: {self.preset_conveyor_speed.get()}%"
        )
        ttk.Label(frm_controls, textvariable=self._speed_label_var)\
            .grid(row=r, column=0, sticky="w", pady=(8,2))
        r += 1

        sld = ttk.Scale(frm_controls, from_=0, to=100,
                        variable=self.preset_conveyor_speed, orient="horizontal", length=220)
        sld.grid(row=r, column=0, sticky="we", pady=(0,20))
        try:
            self.preset_conveyor_speed.trace_add("write",
                lambda *a: self._speed_label_var.set(
                    f"Preset conveyor speed: {self.preset_conveyor_speed.get()}%"
            ))
        except Exception:
            self.preset_conveyor_speed.trace("w",
                lambda *a: self._speed_label_var.set(
                    f"Preset conveyor speed: {self.preset_conveyor_speed.get()}%"
            ))
        r += 1

        # Buttons
        frm_btn = ttk.Frame(frm_left, padding=(0,8,0,0))
        frm_btn.pack(fill="x")
        self.btn_start = ttk.Button(frm_btn, text="START", command=self._on_start, width=12)
        self.btn_start.grid(row=0, column=0, padx=4, pady=20, ipadx=10, ipady=5)
        self.btn_stop = ttk.Button(frm_btn, text="STOP", command=self._on_stop,
                                state="disabled", width=12)
        self.btn_stop.grid(row=0, column=1, padx=4, pady=20, ipadx=10, ipady=5)

        # LEDs
        frm_led = ttk.Frame(frm_left, padding=(0,4,0,8))
        frm_led.pack(fill="x")
        ttk.Label(frm_led, text="ESP32:").grid(row=0, column=0, sticky="w")
        self.canvas_esp_led = tk.Canvas(frm_led, width=20, height=20, highlightthickness=0)
        self.esp_led_item = self.canvas_esp_led.create_oval(2,2,18,18, fill="red")
        self.canvas_esp_led.grid(row=0, column=1, padx=(4,12), pady=20)

        ttk.Label(frm_led, text="NIR:").grid(row=0, column=2, sticky="w", padx=(30,0))
        self.canvas_nir_led = tk.Canvas(frm_led, width=20, height=20, highlightthickness=0)
        self.nir_led_item = self.canvas_nir_led.create_oval(2,2,18,18, fill="red")
        self.canvas_nir_led.grid(row=0, column=3, padx=4, pady=20)

        # Radio buttons under the graph
        frm_radio_right = ttk.Frame(frm_right, padding=(4,8,4,4))
        frm_radio_right.pack(side="bottom", fill="x")
        self.data_type = tk.IntVar(value=1)
        inner_frame = ttk.Frame(frm_radio_right)
        inner_frame.pack(anchor="center")
        ttk.Label(inner_frame, text="Plot data:").pack(side="left", padx=(0,8))
        ttk.Radiobutton(inner_frame, text="Intensity", variable=self.data_type, value=1).pack(side="left", padx=6)
        ttk.Radiobutton(inner_frame, text="Reflectance", variable=self.data_type, value=2).pack(side="left", padx=6)
        ttk.Radiobutton(inner_frame, text="Absorbance", variable=self.data_type, value=3).pack(side="left", padx=6)

        # Graph on right
        self.fig = Figure(figsize=(3,4), constrained_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Spectrum")
        self.ax.set_xlabel("Wavelength")
        self.ax.set_ylabel("Intensity")
        self.canvas = FigureCanvasTkAgg(self.fig, master=frm_right)
        self.canvas.get_tk_widget().pack(fill="both", expand = False)

        # LOG on bottom row
        ttk.Label(frm_bottom, text="Log:").pack(anchor="w")
        # --- FIXED TYPO: heigh -> height ---
        self.txt_log = scrolledtext.ScrolledText(frm_bottom, height=15, state="disabled", wrap="none")
        self.txt_log.pack(fill="both", expand=True)

    def _browse_save_path(self):
        p = filedialog.askdirectory(initialdir=self.save_data_path.get() or os.getcwd())
        if p:
            self.save_data_path.set(p)
            # persist presets
            self._persist_presets()

    def _persist_presets(self):
        presets = {
            "save_measured_data": str(self.save_measured_data.get()),
            "save_data_path": self.save_data_path.get(),
            "preset_measure_times": str(self.preset_measure_times.get()),
            "current_fruit_number": str(self.current_fruit_number.get()),
            "preset_conveyor_speed": str(self.preset_conveyor_speed.get())
        }
        save_presets(PRESET_FILENAME, presets)

    def _poll_log_queue(self):
        """Periodically check the log queue and flush to UI in main thread."""
        try:
            while True:
                text = log_queue.get_nowait()
                self._append_log_to_ui(text)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log_queue)

    def _append_log_to_ui(self, text):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"{time.strftime('%m/%d %H:%M')} {text}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _brix_prediction(self, combined_df, input_data_type):
        
        # takes either intensity / reflectance / absorbance
        intensity_df = combined_df[combined_df["data_type"] == input_data_type]

        # take all columns name including "current_point" and "data_type"
        numeric_cols = intensity_df.select_dtypes(include="number").columns.tolist()

        # trim off the "current_point" and "data_type"
        for col in ["current_point", "data_type"]:
            if col in numeric_cols:
                numeric_cols.remove(col)

        # take only the first 125 wavelengths
        wavelength_cols = numeric_cols[:125]
        selected_df = intensity_df[wavelength_cols]

        # average across all measurement points
        avg_values = selected_df.mean(axis=0).values.reshape(1, -1)

        # preprocessing
        avg_values = self.scaler.transform(avg_values)

        # make prediction
        brix_pred = self.model.predict(avg_values)[0]

        # type decision
        fruit_type = 1 if brix_pred >= 25 else 2

        return brix_pred, fruit_type

    # ----- Communications start -----
    def _start_communications(self):
        # Persist presets when starting
        self._persist_presets()

        # Start NIR comm
        threading.Thread(target=self._init_nir, daemon=True).start()

        # Start ESP comm
        threading.Thread(target=self._init_esp, daemon=True).start()

    def _init_nir(self):
        try:
            enqueue_log("[PC -> LOG] Starting NIR connection attempt...")
            # Import NIR_wrapper and create instance
            try:
                from wrappers.NIR_wrapper import NIR_SPECTROMETER
            except Exception as e:
                enqueue_log(f"[PC -> LOG] Failed to import NIR_wrapper: {e}")
                return
            try:
                self.nir = NIR_SPECTROMETER()  # assume constructor signature; user must adapt
            except Exception as e:
                enqueue_log(f"[PC -> LOG] Failed to create NIR_SPECTROMETER instance: {e}")
                return
            try:
                ok = False
                # call start_USB_communication if exists
                if hasattr(self.nir, "start_USB_communication"):
                    ok = self.nir.start_USB_communication()
                else:
                    enqueue_log("[PC -> LOG] NIR wrapper has no start_USB_communication()")
                if ok:
                    self.nir_connected = True
                    self._set_nir_led(True)
                    enqueue_log("[PC -> LOG] NIR connected")
                else:
                    enqueue_log(f"[PC -> LOG] NIR did not respond {ok}")
            except Exception as e:
                enqueue_log(f"[PC -> LOG] Exception when starting NIR USB: {e}")
            try:
                self.nir.fetch_reference(file_dir=PRESETS_DIR)
            except:
                enqueue_log("[PC -> LOG] Cannot load reference")
        except Exception as e:
            enqueue_log(f"[PC -> LOG] Unexpected NIR init error: {e}")

    def _set_nir_led(self, on: bool):
        color = "green" if on else "red"
        self.canvas_nir_led.itemconfig(self.nir_led_item, fill=color)

    def _init_esp(self):
        """Find a likely ESP32 port, open serial, send wake? and wait for awake."""
        enqueue_log("[PC -> LOG] Scanning serial ports for ESP32...")
        ports = list(serial.tools.list_ports.comports())
        candidate = None
        for p in ports:
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if "cp210" in desc:
                candidate = p.device
                break
        if candidate is None and ports:
            candidate = ports[0].device

        if not candidate:
            enqueue_log("[PC -> LOG] No serial ports found for ESP32.")
            return

        enqueue_log(f"[PC -> LOG] Trying serial port {candidate} ...")
        try:
            self.esp_serial = serial.Serial(candidate, 115200, timeout=0.5)
            # small delay
            time.sleep(0.2)
        except Exception as e:
            enqueue_log(f"[PC -> LOG] Failed to open serial {candidate}: {e}")
            return

        # Start listener thread
        self.esp_stop_event.clear()
        self.esp_listen_thread = threading.Thread(target=self._esp_listener_loop, daemon=True)
        self.esp_listen_thread.start()

        # send wake? and wait for awake
        try:
            enqueue_log('[PC -> LOG] Sending "wake?" to ESP')
            self._send_to_esp("wake?")
            # listen for awake but we don't log ESP messages until handshake completes
            start_t = time.time()
            while time.time() - start_t < 1:
                if self.esp_connected:
                    return
                time.sleep(0.1)
            enqueue_log("[PC -> LOG] ESP did not respond with 'awake' within timeout.")
        except Exception as e:
            enqueue_log(f"[PC -> LOG] Exception during ESP handshake: {e}")

    def _set_esp_led(self, on: bool):
        color = "green" if on else "red"
        self.canvas_esp_led.itemconfig(self.esp_led_item, fill=color)

    def _send_to_esp(self, text):
        """Send raw text to esp with newline."""
        if self.esp_serial and self.esp_serial.is_open:
            try:
                b = (text + "\n").encode("utf-8")
                self.esp_serial.write(b)
                enqueue_log(f"[PC -> ESP] {text}")  # local log of sending
            except Exception as e:
                enqueue_log(f"[PC -> LOG] Failed to send to ESP: {e}")
        else:
            enqueue_log("[PC -> LOG] Attempted to send but ESP serial not open")

    def _esp_listener_loop(self):
        """Continuously read from serial and dispatch messages."""
        handshake_done = False
        buffer = b""
        while not self.esp_stop_event.is_set():
            try:
                if not (self.esp_serial and self.esp_serial.is_open):
                    time.sleep(0.5)
                    continue
                data = self.esp_serial.read(1024)
                if not data:
                    time.sleep(0.05)
                    continue
                buffer += data
                # split on newline
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        s = line.decode("utf-8", errors="ignore").strip()
                    except:
                        s = repr(line)

                    # Before handshake: only watch for "awake" and do not enqueue other ESP logs
                    if not handshake_done:
                        if s.lower() == "awake":
                            handshake_done = True
                            self.esp_connected = True
                            self._set_esp_led(True)
                            enqueue_log(f"[ESP -> PC] {s}")  # log the awake line and start logging thereafter
                            # After handshake, continue to handle the message if it matches expected format
                            try:
                                self._handle_esp_message(s)
                            except Exception:
                                pass
                        # ignore other pre-handshake lines (no logging)
                        continue

                    # After handshake: log all incoming ESP messages and handle them
                    enqueue_log(f"[ESP -> PC] {s}")
                    try:
                        self._handle_esp_message(s)
                    except Exception as e:
                        enqueue_log(f"[PC -> LOG] Error handling ESP message: {e}")
            except Exception as e:
                enqueue_log(f"[PC -> LOG] Exception in ESP listener: {e}")
                time.sleep(0.2)

    def _handle_esp_message(self, msg):
        # parse simple format
        # Expected: <fruit_id>|<state>|<payload>
        try:
            parts = msg.split("|")
            fruit_id = parts[0]
            state = parts[1]
            payload = parts[2]
            if state == "MEASURE_PROCESSING":
                # payload is current measure point (string)
                try:
                    current_point = int(payload)
                except:
                    current_point = 0
                if current_point > 0:
                    # perform scan and processing
                    threading.Thread(target=self._process_measure_point,
                                     args=(fruit_id, current_point),
                                     daemon=True).start()
                else:
                    # just informational
                    pass
            elif state == "MEASURE_PASSED" and payload == "-1":
                # indicates all points measured; we should run ANN sim
                threading.Thread(target=self._process_measure_passed_all,
                                 args=(fruit_id,), daemon=True).start()
            else:
                enqueue_log(f"[ESP -> PC] {msg}")
                pass
        except Exception as e:
            enqueue_log(f"[PC -> LOG] Error parsing ESP message: {e}")

    def _process_measure_point(self, fruit_id, current_point):
        """Perform NIR scan, update plot, and append this point to a single temp file per fruit."""
        # enqueue_log(f"[PC -> LOG] Starting measurement for fruit {fruit_id} point {current_point}")
        if not self.nir:
            enqueue_log("[PC -> LOG] NIR object not available; skipping measurement")
            self._send_to_esp(f"{fruit_id}|MEASURE_PROCESSING|{current_point}")
            return

        try:
            if hasattr(self.nir, "perform_scan"):
                self.nir.perform_scan()
            if hasattr(self.nir, "data_cal"):
                self.nir.data_cal()
        except Exception as e:
            enqueue_log(f"[PC -> LOG] Exception during NIR scanning: {e}")

        wavelength = getattr(self.nir, "wavelength", None)
        sample_intensity = getattr(self.nir, "sample_intensity", None)
        reflectance = getattr(self.nir, "reflectance", None)
        absorbance = getattr(self.nir, "absorbance", None)

        # Convert numpy/array-like objects to Python lists so `if sample_intensity` and indexing work
        try:
            if wavelength is not None and hasattr(wavelength, "tolist"):
                wavelength = list(wavelength)
            if sample_intensity is not None and hasattr(sample_intensity, "tolist"):
                sample_intensity = list(sample_intensity)
            if reflectance is not None and hasattr(reflectance, "tolist"):
                reflectance = list(reflectance)
            if absorbance is not None and hasattr(absorbance, "tolist"):
                absorbance = list(absorbance)
        except Exception:
            pass

        # Fallback checks: if arrays are None, create a fake spectrum to allow GUI demo
        if wavelength is None or sample_intensity is None:
            wavelength = list(range(900, 1700, 20))
            sample_intensity = [random.random() * 100 for _ in wavelength]
            reflectance = [v / 100.0 for v in sample_intensity]
            absorbance = [0.001 * v for v in sample_intensity]

        try:
            n = len(wavelength)
        except Exception:
            n = 0

        if reflectance is None or len(reflectance) != n:
            if sample_intensity and len(sample_intensity) == n:
                reflectance = [v / 100.0 for v in sample_intensity]
            else:
                reflectance = ["" for _ in range(n)]

        if absorbance is None or len(absorbance) != n:
            if sample_intensity and len(sample_intensity) == n:
                absorbance = [0.001 * v for v in sample_intensity]
            else:
                absorbance = ["" for _ in range(n)]

        dtype = self.data_type.get()
        if dtype == 1:
            spec = sample_intensity
            y_label = "Intensity"
        elif dtype == 2:
            spec = reflectance
            y_label = "Reflectance"
        else:
            spec = absorbance
            y_label = "Absorbance"

        self.root.after(0, lambda: self._update_plot(wavelength, spec, y_label))

        # One temp file per fruit: temp_f{fruit_id}.csv
        save_folder = Path(self.save_data_path.get())
        save_folder.mkdir(parents=True, exist_ok=True)
        temp_path = save_folder / f"temp_f{fruit_id}.csv"

        # Prepare columns: current_point,data_type, then one column per wavelength (WL_<wl>)
        wl_cols = [f"WL_{w}" for w in wavelength]
        header = ["current_point", "data_type"] + wl_cols

        # Ensure all three spectra exist and have length n (use "" when missing)
        def safe_series(series, n):
            if series and len(series) == n:
                return [series[i] for i in range(n)]
            # if series is shorter but not None, fill missing with "" for safety
            if series:
                out = []
                for i in range(n):
                    out.append(series[i] if i < len(series) else "")
                return out
            return ["" for _ in range(n)]

        i_series = safe_series(sample_intensity, n)
        r_series = safe_series(reflectance, n)
        a_series = safe_series(absorbance, n)

        # Rows: three rows per save (Intensity -> data_type 1, Reflectance -> 2, Absorbance -> 3)
        intensity_row = [current_point, 1] + i_series
        reflectance_row = [current_point, 2] + r_series
        absorbance_row = [current_point, 3] + a_series

        # Write header if file doesn't exist, else append rows
        try:
            write_header = not temp_path.exists()
            with open(temp_path, "a", newline="", encoding="utf-8") as csvf:
                writer = csv.writer(csvf)
                if write_header:
                    writer.writerow(header)
                writer.writerow(intensity_row)
                writer.writerow(reflectance_row)
                writer.writerow(absorbance_row)
        except Exception as e:
            enqueue_log(f"[PC -> LOG] Failed to write temp file {temp_path}: {e}")

        # Echo back to ESP
        self._send_to_esp(f"{fruit_id}|MEASURE_PROCESSING|{current_point}")

    def _update_plot(self, wavelength, spec, y_label):
        self.ax.clear()
        self.ax.plot(wavelength[:125], spec[:125])
        self.ax.set_title("Spectrum", fontsize=11)
        self.ax.set_xlabel("Wavelength", fontsize=10, labelpad=8)
        self.ax.set_ylabel(y_label, fontsize=10)
        # nudge xlabel lower if necessary (make more negative to move further down)
        self.ax.xaxis.set_label_coords(0.5, -0.12)
        try:
            # first draw to create renderer, then let matplotlib compute layout
            self.canvas.draw()
            self.fig.tight_layout()
        except Exception:
            # fallback manual spacing
            try:
                self.fig.subplots_adjust(bottom=0.14)
            except Exception:
                pass
        # final draw
        self.canvas.draw_idle()

    def _process_measure_passed_all(self, fruit_id):
        """Combine temp rows (one file per fruit), choose type and move final file into yy/mm/dd folder."""
        enqueue_log(f"[PC -> LOG] Processing completed measurements for fruit {fruit_id} ...")
        folder = Path(self.save_data_path.get())

        # find temp file(s) for this fruit (legacy could have multiples)
        temp_files = list(folder.glob(f"temp_f{fruit_id}*.csv"))
        if not temp_files:
            enqueue_log(f"[PC -> LOG] No temporary files found for fruit {fruit_id}.")
            fruit_type = 1
            self._send_to_esp(f"{fruit_id}|MEASURE_PASSED|{fruit_type}")
            return

        # Read and combine numeric data from all temp files
        all_values = []
        combined_df = None
        for f in temp_files:
            try:
                df = pd.read_csv(f)
                if combined_df is None:
                    combined_df = df
                else:
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
            except Exception as e:
                enqueue_log(f"[PC -> LOG] Could not read temp file {f}: {e}")

        # make prediction and decide fruit type
        brix, fruit_type = self._brix_prediction(combined_df, 2)
        brix_scaled = round(brix * 100)

        # prepare date folder as "date_yy_mm_dd" under save folder
        date_dir = folder / f"date_{time.strftime('%y')}_{time.strftime('%m')}_{time.strftime('%d')}"
        date_dir.mkdir(parents=True, exist_ok=True)

        # final name: citrux_{fruit_id}_{brix_scaled}_{fruit_type}.csv (overwrite allowed)
        final_name = f"citrux_{fruit_id}_{brix_scaled}_{fruit_type}.csv"
        final_path = date_dir / final_name

        try:
            if combined_df is not None:
                # write combined dataframe directly to final path (overwrites existing)
                combined_df.to_csv(final_path, index=False)
                enqueue_log(f"[PC -> LOG] Saved combined measurements")
            else:
                # fallback: move the first temp file to final path (overwrite)
                temp_files[0].replace(final_path)
                enqueue_log(f"[PC -> LOG] Saved measurement")
            # remove any remaining temp files (if we wrote combined_df, delete originals)
            for f in temp_files:
                try:
                    if f.exists():
                        f.unlink()
                except Exception:
                    pass
        except Exception as e:
            enqueue_log(f"[PC -> LOG] Failed to create final file {final_path}: {e}")

        # Send result back to ESP
        self._send_to_esp(f"{fruit_id}|MEASURE_PASSED|{fruit_type}")
        enqueue_log(f"[PC -> LOG] Fruit: {fruit_id} | Brix: {brix} | Type: {fruit_type}")

        # update presets: set current_fruit_number to the next fruit (fruit_id + 1) and persist
        try:
            fid = int(fruit_id)
            self.current_fruit_number.set(fid + 1)
            self._persist_presets()
            # enqueue_log(f"[PC -> LOG] Updated current fruit number to {self.current_fruit_number.get()}")
        except Exception:
            # if fruit_id is not integer, ignore update
            pass

    # ----- UI actions: start/stop -----
    def _on_start(self):
        """Start or restart sequence. Only RESTART triggers reinit/handshake; normal START uses existing connection."""
        try:
            btn_text = self.btn_start.cget("text")
        except Exception:
            btn_text = "START"

        # RESTART path: reinitialize comms and perform handshake
        if btn_text.upper() == "RESTART":
            enqueue_log("[PC -> LOG] RESTART pressed — reinitializing ESP and NIR...")
            try:
                self._set_esp_led(False)
                self._set_nir_led(False)
            except Exception:
                pass

            # stop/close existing comms
            try:
                self.esp_stop_event.set()
                if self.esp_listen_thread and self.esp_listen_thread.is_alive():
                    self.esp_listen_thread.join(timeout=0.5)
            except Exception:
                pass
            try:
                if self.esp_serial and self.esp_serial.is_open:
                    self.esp_serial.close()
                    enqueue_log("[PC -> LOG] Closed ESP serial for restart")
            except Exception:
                pass
            self.esp_connected = False

            try:
                if self.nir and hasattr(self.nir, "stop_USB_communication"):
                    self.nir.stop_USB_communication()
                    enqueue_log("[PC -> LOG] Stopped NIR communication for restart")
            except Exception:
                pass
            self.nir_connected = False

            # start comms and wait for handshake!
            self._start_communications()
            time.sleep(1)

            if self.esp_connected == False and self.nir_connected == False:
                enqueue_log("[PC -> LOG] Cannot restart: ESP and NIR not connected.")
                messagebox.showwarning("ESP and NIR not connected", "ESP and NIR did not respond. Check connection and try again.")
                self.btn_start.configure(state="normal", text="RESTART")
                return
            if self.esp_connected == False and self.nir_connected == True:
                enqueue_log("[PC -> LOG] Cannot restart: ESP not connected.")
                messagebox.showwarning("ESP not connected", "ESP did not respond. Check connection and try again.")
                self.btn_start.configure(state="normal", text="RESTART")
                return
            if self.esp_connected == True and self.nir_connected == False:
                enqueue_log("[PC -> LOG] Cannot restart: NIR not connected.")
                messagebox.showwarning("NIR not connected", "NIR did not respond. Check connection and try again.")
                self.btn_start.configure(state="normal", text="RESTART")
                return

            # wait briefly for NIR init and update LED
            start = time.time()
            while time.time() - start < 6:
                if getattr(self, "nir_connected", False):
                    try:
                        self._set_nir_led(True)
                    except Exception:
                        pass
                    break
                time.sleep(0.1)
            else:
                enqueue_log("[PC -> LOG] NIR did not initialize within timeout.")

            # reset button text
            self.btn_start.configure(text="START")

        # Check connection
        if self.esp_connected == False and self.nir_connected == False:
            enqueue_log("[PC -> LOG] Cannot start: ESP and NIR not connected.")
            messagebox.showwarning("ESP and NIR not connected", "ESP and NIR did not respond. Check connection and try again.")
            self.btn_start.configure(state="normal", text="RESTART")
            return
        if self.esp_connected == False and self.nir_connected == True:
            enqueue_log("[PC -> LOG] Cannot start: ESP not connected.")
            messagebox.showwarning("ESP not connected", "ESP did not respond. Check connection and try again.")
            self.btn_start.configure(state="normal", text="RESTART")
            return
        if self.esp_connected == True and self.nir_connected == False:
            enqueue_log("[PC -> LOG] Cannot start: NIR not connected.")
            messagebox.showwarning("NIR not connected", "NIR did not respond. Check connection and try again.")
            self.btn_start.configure(state="normal", text="RESTART")
            return

        # proceed with sending config using current UI values
        initial = self.current_fruit_number.get()
        times = self.preset_measure_times.get()
        speed = self.preset_conveyor_speed.get()
        msg = f"confirm|{initial}|{times}|{speed}"
        self._send_to_esp(msg)
        enqueue_log("[PC -> LOG] send configuration to ESP")

        # disable inputs and update buttons
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._set_inputs_state("disabled")
        # persist current presets (keeps file in sync)
        self._persist_presets()

    def _on_stop(self):
        # send stop to ESP (best-effort)
        try:
            self._send_to_esp("stop")
        except Exception:
            pass
        enqueue_log("[PC -> LOG] SYSTEM STOPPED")


        # Change START to RESTART and enable it; disable STOP
        try:
            self.btn_start.configure(state="normal", text="RESTART")
            self.btn_stop.configure(state="disabled")
        except Exception:
            pass

        # re-enable inputs
        self._set_inputs_state("normal")

    def _set_inputs_state(self, state):
        # There is no straightforward handle saved for every entry; just re-create logic:
        # We'll iterate children and set state where appropriate (Entry, Scale)
        for child in self.root.winfo_children():
            pass
        # Simpler: enable/disable the elements we know: entries and scale by walking widget tree
        def recurse(widget):
            for w in widget.winfo_children():
                cls = w.__class__.__name__
                if cls in ("Entry", "Scale"):
                    try:
                        w.configure(state=state)
                    except Exception:
                        pass
                recurse(w)
        recurse(self.root)

    # ----- Cleanup -----
    def close(self):
        try:
            self.esp_stop_event.set()
            if self.esp_listen_thread and self.esp_listen_thread.is_alive():
                self.esp_listen_thread.join(timeout=0.5)
            if self.esp_serial and self.esp_serial.is_open:
                self.esp_serial.close()
        except:
            pass
        self.root.destroy()

# ----- Start application -----
if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    app = CitrusSortingApp(root)

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            app.close()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

