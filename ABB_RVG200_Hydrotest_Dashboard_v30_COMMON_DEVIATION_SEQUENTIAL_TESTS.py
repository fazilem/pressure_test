
import csv
import os
import base64
import io
import re
import struct
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from pymodbus.client import ModbusTcpClient

# Optional packages used for graph and PDF certificate
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.image as mpimg
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    )
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False


# ============================================================
# DEFAULT SETTINGS
# ============================================================
DEFAULT_IP = "192.168.1.9"
DEFAULT_PORT = 502
DEFAULT_DEVICE_ID = 255
TOTAL_CHANNELS = 6

DEFAULT_SAMPLE_INTERVAL = 1.0
DEFAULT_TEST_DURATION = 15.0

WEATHERFORD_LOGO_FILENAME = "Weatherford-Logo.png"
WEATHERFORD_LOGO_BASE64 = "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"


# ============================================================
# ABB RVG200 MODBUS READING
# ============================================================
def _decode_float_pair(regs):
    """Return sensible float candidates from a two-register response."""
    candidates = []
    if not regs or len(regs) < 2:
        return candidates

    for pair in ((regs[0], regs[1]), (regs[1], regs[0])):
        try:
            value = struct.unpack(">f", struct.pack(">HH", *pair))[0]
            if (
                value == value
                and abs(value) < 99990
                and abs(value) > 1e-30
            ):
                candidates.append(value)
        except Exception:
            pass
    return candidates


def read_abb_data(ip, port, device_id, channel_count=6):
    """
    RVG200 reader using the confirmed sequential register map:
    Ch1=0, Ch2=2, Ch3=4, Ch4=6, Ch5=8, Ch6=10.

    ABB invalid/no-data sentinel values are returned as None. They must
    never be converted to zero or written into test data.
    """
    channel_count = max(1, min(int(channel_count), TOTAL_CHANNELS))
    client = ModbusTcpClient(host=ip, port=port, timeout=3)
    readings = {}
    errors = []

    try:
        if not client.connect():
            return None, "TCP connection failed."

        for channel in range(1, channel_count + 1):
            address = (channel - 1) * 2
            try:
                response = client.read_holding_registers(
                    address=address, count=2, device_id=device_id
                )
                if response.isError():
                    readings[f"Ch_{channel}"] = None
                    errors.append(f"Ch_{channel}: Modbus read error")
                    continue

                regs = getattr(response, "registers", None)
                if not regs or len(regs) < 2:
                    readings[f"Ch_{channel}"] = None
                    errors.append(f"Ch_{channel}: no register data")
                    continue

                value = struct.unpack(
                    ">f", struct.pack(">HH", regs[1], regs[0])
                )[0]

                if (
                    value != value
                    or value in (float("inf"), float("-inf"))
                    or value <= -99990
                    or value >= 99990
                ):
                    readings[f"Ch_{channel}"] = None
                    errors.append(f"Ch_{channel}: invalid value {value}")
                else:
                    readings[f"Ch_{channel}"] = float(value)

            except Exception as exc:
                readings[f"Ch_{channel}"] = None
                errors.append(f"Ch_{channel}: {type(exc).__name__}: {exc}")

        for channel in range(channel_count + 1, TOTAL_CHANNELS + 1):
            readings[f"Ch_{channel}"] = None

        return readings, " | ".join(errors) if errors else None

    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    finally:
        try:
            client.close()
        except Exception:
            pass


# ============================================================
# MAIN APPLICATION
# ============================================================
class HydrotestApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("ABB RVG200 Hydrotest Dashboard")
        self.geometry("1600x920")
        self.minsize(1200, 760)

        # Clean industrial dashboard styling.
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(8, 4))
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("TEntry", padding=3)
        style.configure("TCombobox", padding=2)

        self.running = False
        self.worker = None
        self.active_test = None

        # Required by START / STOP and the background logging thread.
        self.stop_event = threading.Event()

        # Hydrotest storage.
        self.test_data = {1: [], 2: []}
        self.test_results = {1: {}, 2: {}}

        # First valid pressure for each test. This is the graph zero reference.
        self.test_baseline = {1: None, 2: None}

        self.last_readings = {}
        # Cache only genuine Modbus readings. If the RVG200 temporarily
        # reports its invalid sentinels (-99999.9 / -999999), the live
        # display keeps the last genuine value, while the invalid sample is
        # NOT written to the test data, graph, CSV or report.
        self.last_valid_readings = {}

        # Auto-live monitoring starts after the first READ NOW.
        # While a hydrotest is running, the logging worker itself updates
        # the live cards, so the separate monitor pauses automatically.
        self.live_monitoring = False
        self.live_refresh_ms = 1000
        self.live_after_id = None

        self._create_variables()
        self._build_ui()
        self._test_channel_selection_changed()
        self._update_buttons()
        self._show_results()

    # ========================================================
    # VARIABLES
    # ========================================================
    def _create_variables(self):
        self.ip_var = tk.StringVar(value=DEFAULT_IP)
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        self.device_var = tk.StringVar(value=str(DEFAULT_DEVICE_ID))
        self.channel_var = tk.StringVar(value="1")

        self.interval_var = tk.StringVar(
            value=str(DEFAULT_SAMPLE_INTERVAL)
        )
        self.duration_var = tk.StringVar(
            value=str(DEFAULT_TEST_DURATION)
        )

        self.customer_var = tk.StringVar()
        self.work_order_var = tk.StringVar()
        self.tools_var = tk.StringVar(
            value="VALVE, RESERVOIR ISOLATION"
        )
        self.description_var = tk.StringVar()
        self.jde_var = tk.StringVar()
        self.documents_var = tk.StringVar()
        self.technician_var = tk.StringVar()
        self.recorded_var = tk.StringVar(
            value=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        self.input1_var = tk.StringVar(value="20K")
        self.input2_var = tk.StringVar(value="20K")
        self.applied1_var = tk.StringVar(value="")
        self.test_pressure_unit1_var = tk.StringVar(value="bar")
        self.test_pressure_unit2_var = tk.StringVar(value="bar")
        self.applied2_var = tk.StringVar(value="")
        self.max_dev1_var = tk.StringVar(value="0.20")
        self.max_dev2_var = tk.StringVar(value="0.20")

        self.status_var = tk.StringVar(
            value="Ready - click Read Now"
        )
        self.live_value_var = tk.StringVar(value="--")
        self.channel_values_var = tk.StringVar(
            value="Channels: --"
        )
        self.error_var = tk.StringVar(value="")

        # Live dashboard configuration
        self.channel_count_var = tk.StringVar(value="6")
        self.measurement_type_var = tk.StringVar(value="Pressure")
        self.unit_var = tk.StringVar(value="bar")
        self.live_channel_vars = [
            tk.StringVar(value=f"Ch_{i}\n--")
            for i in range(1, TOTAL_CHANNELS + 1)
        ]

        # Per-channel engineering configuration.
        # Raw RVG200 value + Offset = displayed/logged engineering value.
        self.channel_type_vars = [
            tk.StringVar(value="Pressure") for _ in range(TOTAL_CHANNELS)
        ]
        self.channel_unit_vars = [
            tk.StringVar(value="bar") for _ in range(TOTAL_CHANNELS)
        ]
        self.channel_offset_vars = [
            tk.StringVar(value="0.0") for _ in range(TOTAL_CHANNELS)
        ]

        # Channels to include in the hydrotest/logging/graph.
        # "No. of Channels" defines the available channels; these checkboxes
        # define which of those available channels are actually tested.
        self.test_channel_select_vars = [
            tk.BooleanVar(value=(i < 2)) for i in range(TOTAL_CHANNELS)
        ]
        self.test_channel_checkbuttons = []

    # ========================================================
    # UI
    # ========================================================
    def _build_ui(self):

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # ----------------------------------------------------
        # CONNECTION / LIVE DASHBOARD
        # ----------------------------------------------------
        frame = ttk.LabelFrame(
            self,
            text="ABB RVG200 Modbus TCP - Live Measurements"
        )
        frame.grid(
            row=0, column=0, sticky="ew",
            padx=8, pady=4
        )

        # Row 0: communications
        ttk.Label(frame, text="IP Address").grid(row=0, column=0, padx=4, pady=4)
        ttk.Entry(frame, textvariable=self.ip_var, width=14).grid(row=0, column=1, padx=4)

        ttk.Label(frame, text="Port").grid(row=0, column=2, padx=4)
        ttk.Entry(frame, textvariable=self.port_var, width=6).grid(row=0, column=3, padx=4)

        ttk.Label(frame, text="Device ID").grid(row=0, column=4, padx=4)
        ttk.Entry(frame, textvariable=self.device_var, width=6).grid(row=0, column=5, padx=4)

        ttk.Label(frame, text="No. of Channels").grid(row=0, column=6, padx=(12, 4))
        self.channel_count_combo = ttk.Combobox(
            frame,
            textvariable=self.channel_count_var,
            values=["1", "2", "3", "4", "5", "6"],
            state="readonly",
            width=5
        )
        self.channel_count_combo.grid(row=0, column=7, padx=4)
        self.channel_count_combo.bind("<<ComboboxSelected>>", self._channel_count_changed)

        # The former "Selected Channel" control was redundant because all
        # enabled channels are read and displayed simultaneously.
        ttk.Button(
            frame,
            text="READ NOW",
            command=self.read_now
        ).grid(row=0, column=8, padx=(18, 8))

        # Row 1: engineering display settings
        ttk.Label(frame, text="Measurement").grid(row=1, column=0, padx=4, pady=4)
        self.measurement_combo = ttk.Combobox(
            frame,
            textvariable=self.measurement_type_var,
            values=["Pressure", "Temperature"],
            state="readonly",
            width=12
        )
        self.measurement_combo.grid(row=1, column=1, padx=4)
        self.measurement_combo.bind("<<ComboboxSelected>>", self._measurement_changed)

        ttk.Label(frame, text="Unit").grid(row=1, column=2, padx=4)
        self.unit_combo = ttk.Combobox(
            frame,
            textvariable=self.unit_var,
            values=[
                "bar", "mbar", "Pa", "kPa", "MPa", "psi", "ksi",
                "kg/cm²", "kgf/cm²", "mmH2O", "cmH2O", "mH2O",
                "inH2O", "mmHg", "inHg", "atm", "Torr", "Custom..."
            ],
            state="normal",
            width=11
        )
        self.unit_combo.grid(row=1, column=3, padx=4)
        self.unit_combo.bind("<<ComboboxSelected>>", self._global_unit_selected)
        self.unit_combo.bind("<Return>", self._global_unit_changed)
        self.unit_combo.bind("<FocusOut>", self._global_unit_changed)

        # Individual channel cards below are the live display.  The former
        # "Selected Live" duplicate field has intentionally been removed.
        ttk.Label(
            frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=4, columnspan=7, sticky="w", padx=(14, 4))

        # Row 2: six individual live-value cards
        self.live_cards = []
        for i in range(TOTAL_CHANNELS):
            card = ttk.LabelFrame(frame, text=f"Channel {i + 1}")
            card.grid(
                row=2, column=i * 2, columnspan=2,
                sticky="nsew", padx=3, pady=(3, 2)
            )
            label = ttk.Label(
                card,
                textvariable=self.live_channel_vars[i],
                anchor="center",
                justify="center",
                font=("Segoe UI", 11, "bold"),
                width=12
            )
            # Compact horizontal card layout leaves substantially more
            # vertical room for the hydrotest graph.
            label.pack(side="left", fill="both", expand=True, padx=(5, 3), pady=3)

            cfg = ttk.Frame(card)
            cfg.pack(side="right", fill="y", padx=(2, 4), pady=2)

            ttk.Label(cfg, text="Type").grid(row=0, column=0, sticky="w")
            type_combo = ttk.Combobox(
                cfg,
                textvariable=self.channel_type_vars[i],
                values=["Pressure", "Temperature"],
                state="readonly",
                width=10
            )
            type_combo.grid(row=0, column=1, padx=2, pady=1)

            ttk.Label(cfg, text="Unit").grid(row=1, column=0, sticky="w")
            unit_combo = ttk.Combobox(
                cfg,
                textvariable=self.channel_unit_vars[i],
                values=["bar", "kPa", "MPa", "psi", "mbar", "kg/cm²",
                        "°C", "°F", "K"],
                state="readonly",
                width=10
            )
            unit_combo.grid(row=1, column=1, padx=2, pady=1)

            ttk.Label(cfg, text="Offset").grid(row=2, column=0, sticky="w")
            ttk.Entry(
                cfg,
                textvariable=self.channel_offset_vars[i],
                width=12
            ).grid(row=2, column=1, padx=2, pady=1)

            type_combo.bind(
                "<<ComboboxSelected>>",
                lambda e, idx=i, combo=unit_combo: self._channel_type_changed(idx, combo)
            )
            unit_combo.bind("<<ComboboxSelected>>", self._refresh_live_cards)
            self.channel_offset_vars[i].trace_add(
                "write", lambda *_args: self._refresh_live_cards()
            )

            self.live_cards.append(card)

        ttk.Label(
            frame,
            textvariable=self.error_var,
            foreground="red"
        ).grid(
            row=3, column=0, columnspan=12,
            sticky="w", padx=5, pady=(2, 4)
        )

        for c in range(12):
            frame.columnconfigure(c, weight=1)

        # ----------------------------------------------------
        # CERTIFICATE INFORMATION
        # ----------------------------------------------------
        info = ttk.LabelFrame(
            self,
            text="Hydrotest Certificate Information"
        )
        info.grid(
            row=1, column=0,
            sticky="ew",
            padx=8, pady=2
        )

        for c in range(8):
            info.columnconfigure(c, weight=1)

        fields = [
            ("Customer", self.customer_var),
            ("Work Order", self.work_order_var),
            ("Tools", self.tools_var),
            ("Description", self.description_var),
            ("JDE", self.jde_var),
            ("Documents", self.documents_var),
            ("Technician", self.technician_var),
            ("Recorded on", self.recorded_var),
        ]

        # Compact two-row certificate layout: label and entry share one row.
        # This saves vertical space and gives it to the live graph.
        for i, (label, var) in enumerate(fields):
            r = i // 4
            c = (i % 4) * 2
            ttk.Label(info, text=label).grid(
                row=r, column=c, sticky="e", padx=(5, 3), pady=3
            )
            ttk.Entry(info, textvariable=var).grid(
                row=r, column=c + 1, sticky="ew", padx=(0, 6), pady=3
            )

        # ----------------------------------------------------
        # REPORT / FILE ACTIONS - always visible
        # ----------------------------------------------------
        action_bar = ttk.Frame(self)
        action_bar.grid(
            row=2, column=0, sticky="ew",
            padx=8, pady=(0, 2)
        )

        ttk.Button(
            action_bar,
            text="EXPORT CSV",
            command=self.export_csv
        ).pack(side="left", padx=4)

        ttk.Button(
            action_bar,
            text="IMPORT CSV",
            command=self.import_csv
        ).pack(side="left", padx=4)

        ttk.Button(
            action_bar,
            text="PRINT / PDF REPORT",
            command=self.export_pdf
        ).pack(side="left", padx=4)

        ttk.Button(
            action_bar,
            text="CLEAR TESTS",
            command=self.clear_tests
        ).pack(side="left", padx=4)

        # ----------------------------------------------------
        # MAIN CONTENT
        # ----------------------------------------------------
        main = ttk.Frame(self)
        main.grid(
            row=3, column=0,
            sticky="nsew",
            padx=8, pady=2
        )

        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        left = ttk.Frame(main)
        left.grid(
            row=0, column=0,
            sticky="nsew"
        )

        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        # ----------------------------------------------------
        # TEST CONTROL
        # ----------------------------------------------------
        control = ttk.LabelFrame(
            left,
            text="Hydrotest Control"
        )
        control.grid(
            row=0, column=0,
            sticky="ew",
            pady=(0, 6)
        )

        # Row 0
        ttk.Label(control, text="Primary Channel").grid(row=0, column=0, padx=5, pady=5)

        self.test_combo = ttk.Combobox(
            control,
            values=["Channel 1", "Channel 2", "Channel 3", "Channel 4", "Channel 5", "Channel 6"],
            state="readonly",
            width=9
        )
        self.test_combo.current(0)
        self.test_combo.grid(row=0, column=1, padx=5)
        self.test_combo.bind("<<ComboboxSelected>>", self._test_changed)

        ttk.Label(control, text="Test Pressure / Rating").grid(
            row=0, column=2, padx=5
        )
        self.input_entry = ttk.Entry(
            control, textvariable=self.input1_var, width=10
        )
        self.input_entry.grid(row=0, column=3, padx=5)

        self.test_pressure_unit_combo = ttk.Combobox(
            control,
            textvariable=self.test_pressure_unit1_var,
            values=[
                "bar", "mbar", "Pa", "kPa", "MPa", "psi", "ksi",
                "kg/cm²", "kgf/cm²", "mmH2O", "cmH2O", "mH2O",
                "inH2O", "mmHg", "inHg", "atm", "Torr", "K", "Custom..."
            ],
            state="normal",
            width=10
        )
        self.test_pressure_unit_combo.grid(row=0, column=4, padx=5)
        self.test_pressure_unit_combo.bind("<<ComboboxSelected>>", self._rating_unit_selected)

        ttk.Label(control, text="Applied Pressure").grid(
            row=0, column=5, padx=5
        )
        self.applied_entry = ttk.Entry(
            control, textvariable=self.applied1_var, width=9
        )
        self.applied_entry.grid(row=0, column=6, padx=5)

        ttk.Label(
            control,
            textvariable=self.unit_var,
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=7, padx=(0, 8))

        ttk.Label(control, text="Max Dev. (±) - All Test Channels").grid(
            row=0, column=8, padx=5
        )
        self.max_dev_entry = ttk.Entry(
            control, textvariable=self.max_dev1_var, width=8
        )
        self.max_dev_entry.grid(row=0, column=9, padx=5)

        # Row 1 - choose exactly which enabled channels participate in test.
        ttk.Label(control, text="Test Channels").grid(
            row=1, column=0, padx=5, pady=5
        )

        test_channel_frame = ttk.Frame(control)
        test_channel_frame.grid(
            row=1, column=1, columnspan=5,
            padx=5, pady=5, sticky="w"
        )

        for ch in range(1, TOTAL_CHANNELS + 1):
            cb = ttk.Checkbutton(
                test_channel_frame,
                text=f"Ch_{ch}",
                variable=self.test_channel_select_vars[ch - 1],
                command=self._test_channel_selection_changed
            )
            cb.grid(row=0, column=ch - 1, padx=(0, 10))
            self.test_channel_checkbuttons.append(cb)

        ttk.Label(control, text="Sample (sec)").grid(
            row=1, column=6, padx=(12, 3), pady=4
        )
        ttk.Entry(
            control, textvariable=self.interval_var, width=7
        ).grid(row=1, column=7, padx=3)

        ttk.Label(control, text="Duration (min)").grid(
            row=1, column=8, padx=(8, 3)
        )
        ttk.Entry(
            control, textvariable=self.duration_var, width=7
        ).grid(row=1, column=9, padx=3)

        self.start_btn = ttk.Button(
            control, text="START TEST", command=self.start_test
        )
        self.start_btn.grid(row=0, column=10, padx=5, pady=4, sticky="ew")

        self.stop_btn = ttk.Button(
            control, text="STOP TEST", command=self.stop_test
        )
        self.stop_btn.grid(row=1, column=10, padx=5, pady=4, sticky="ew")
        self.stop_btn.configure(state="disabled")

        for col in range(11):
            control.columnconfigure(col, weight=1)

        # ----------------------------------------------------
        # GRAPH
        # ----------------------------------------------------
        if MATPLOTLIB_OK:
            self.figure = Figure(
                figsize=(14.5, 8.2),
                dpi=130
            )

            self.ax = self.figure.add_subplot(111)

            self.ax.set_title(
                "ABB RVG200 Hydrotest - Test 1 and Test 2"
            )
            self.ax.set_xlabel(
                "Elapsed Time (min)"
            )
            self.ax.set_ylabel(
                "RVG200 Reading"
            )
            self.ax.grid(True, alpha=0.3)

            self.canvas = FigureCanvasTkAgg(
                self.figure,
                master=left
            )

            self.canvas.get_tk_widget().grid(
                row=1, column=0,
                sticky="nsew"
            )
        else:
            ttk.Label(
                left,
                text=(
                    "matplotlib is not installed.\n"
                    "Run: python -m pip install matplotlib"
                )
            ).grid(
                row=1, column=0,
                sticky="nsew"
            )

        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------
        result_frame = ttk.LabelFrame(
            main,
            text="Test Results"
        )
        result_frame.grid(
            row=0, column=1,
            sticky="ns",
            padx=(8, 0)
        )

        self.result_text = tk.Text(
            result_frame,
            width=34,
            height=24,
            wrap="word"
        )
        self.result_text.grid(
            row=0, column=0,
            padx=5, pady=5
        )

        buttons = ttk.Frame(result_frame)
        buttons.grid(
            row=1, column=0,
            sticky="ew",
            padx=5, pady=5
        )

        ttk.Button(
            buttons,
            text="Export CSV",
            command=self.export_csv
        ).grid(row=0, column=0, padx=3, pady=3)

        ttk.Button(
            buttons,
            text="Import CSV",
            command=self.import_csv
        ).grid(row=0, column=1, padx=3, pady=3)

        ttk.Button(
            buttons,
            text="PRINT / PDF CERTIFICATE",
            command=self.export_pdf
        ).grid(row=1, column=0, columnspan=2,
               padx=3, pady=3, sticky="ew")

        ttk.Button(
            buttons,
            text="Clear Tests",
            command=self.clear_tests
        ).grid(row=2, column=0, columnspan=2,
               padx=3, pady=3, sticky="ew")

        self.protocol(
            "WM_DELETE_WINDOW",
            self._close
        )

        self._channel_count_changed()

    # ========================================================
    # TEST SELECTION
    # ========================================================
    def _test_changed(self, event=None):
        if self.test_combo.get() in ("Channel 1", "Test 1"):
            self.input_entry.configure(textvariable=self.input1_var)
            self.applied_entry.configure(textvariable=self.applied1_var)
            self.test_pressure_unit_combo.configure(
                textvariable=self.test_pressure_unit1_var
            )
            self.max_dev_entry.configure(textvariable=self.max_dev1_var)
        else:
            self.input_entry.configure(textvariable=self.input2_var)
            self.applied_entry.configure(textvariable=self.applied2_var)
            self.test_pressure_unit_combo.configure(
                textvariable=self.test_pressure_unit2_var
            )
            self.max_dev_entry.configure(textvariable=self.max_dev1_var)

        self._show_results()

    def _measurement_changed(self, event=None):
        if self.measurement_type_var.get() == "Temperature":
            self.unit_combo.configure(
                values=["°C", "°F", "K"]
            )
            if self.unit_var.get() not in ("°C", "°F", "K"):
                self.unit_var.set("°C")
        else:
            self.unit_combo.configure(values=[
                "bar", "mbar", "Pa", "kPa", "MPa", "psi", "ksi",
                "kg/cm²", "kgf/cm²", "mmH2O", "cmH2O", "mH2O",
                "inH2O", "mmHg", "inHg", "atm", "Torr", "Custom..."
            ])
            if not self.unit_var.get():
                self.unit_var.set("bar")
        self._global_unit_changed()

    def _ask_custom_unit(self, current_var, title):
        custom = simpledialog.askstring(
            title,
            "Enter the custom engineering unit:",
            parent=self
        )
        if custom is not None and custom.strip():
            current_var.set(custom.strip())
            return True
        return False

    def _global_unit_selected(self, event=None):
        if self.unit_var.get() == "Custom...":
            if not self._ask_custom_unit(self.unit_var, "Custom Process Unit"):
                self.unit_var.set(self.channel_unit_vars[0].get() or "bar")
        self._global_unit_changed()

    def _rating_unit_selected(self, event=None):
        var = self.test_pressure_unit1_var if self.test_combo.get() in ("Channel 1", "Test 1") else self.test_pressure_unit2_var
        if var.get() == "Custom...":
            if not self._ask_custom_unit(var, "Custom Test Pressure / Rating Unit"):
                var.set(self.unit_var.get() or "bar")

    def _global_unit_changed(self, event=None):
        """Apply the main Unit selection to all currently enabled channels.

        The RVG200 register value is already in the engineering unit configured
        for the recorder.  This synchronizes the dashboard/test/report unit
        label; it intentionally does not numerically convert the Modbus value.
        """
        unit = self.unit_var.get()
        try:
            count = max(1, min(int(self.channel_count_var.get()), TOTAL_CHANNELS))
        except Exception:
            count = TOTAL_CHANNELS

        for idx in range(count):
            self.channel_unit_vars[idx].set(unit)

        # Keep Test Pressure / Rating unit synchronized with the main
        # engineering unit. The rating value itself remains a free-entry field.
        if unit and unit != "Custom...":
            self.test_pressure_unit1_var.set(unit)
            self.test_pressure_unit2_var.set(unit)

        # If results already exist on screen (for example an imported CSV),
        # keep their displayed/report unit consistent with the selected unit.
        for ch, result in self.test_results.items():
            if 1 <= int(ch) <= count:
                result["unit"] = unit

        self._refresh_live_cards()
        self._show_results()
        self._update_graph()

    def _channel_type_changed(self, index, combo):
        if self.channel_type_vars[index].get() == "Temperature":
            combo.configure(values=["°C", "°F", "K"])
            if self.channel_unit_vars[index].get() not in ("°C", "°F", "K"):
                self.channel_unit_vars[index].set("°C")
        else:
            combo.configure(values=["bar", "mbar", "Pa", "kPa", "MPa", "psi", "ksi", "kg/cm²", "kgf/cm²", "mmH2O", "cmH2O", "mH2O", "inH2O", "mmHg", "inHg", "atm", "Torr"])
            if self.channel_unit_vars[index].get() not in (
                "bar", "mbar", "Pa", "kPa", "MPa", "psi", "ksi",
                "kg/cm²", "kgf/cm²", "mmH2O", "cmH2O", "mH2O",
                "inH2O", "mmHg", "inHg", "atm", "Torr"
            ):
                self.channel_unit_vars[index].set("bar")
        self._refresh_live_cards()

    def _channel_offset(self, channel):
        try:
            return float(self.channel_offset_vars[channel - 1].get().strip() or "0")
        except Exception:
            return 0.0

    def _engineering_value(self, channel, raw_value):
        if raw_value is None:
            return None
        return float(raw_value) + self._channel_offset(channel)

    def _channel_unit(self, channel):
        return self.channel_unit_vars[channel - 1].get()

    def _channel_type(self, channel):
        return self.channel_type_vars[channel - 1].get()

    def _selected_test_channels(self):
        try:
            count = int(self.channel_count_var.get())
        except Exception:
            count = TOTAL_CHANNELS

        return [
            ch for ch in range(1, count + 1)
            if self.test_channel_select_vars[ch - 1].get()
        ]

    def _test_channel_selection_changed(self):
        selected = self._selected_test_channels()
        if selected:
            selected_text = ", ".join(f"Ch_{ch}" for ch in selected)
            self.status_var.set("Test selection: " + selected_text)
            # Keep the certificate description synchronized with the actual
            # recording channels selected for the hydrotest.
            self.description_var.set("TEST CHANNELS: " + selected_text)
        else:
            self.status_var.set("Select at least one Test Channel.")
            self.description_var.set("")

    def _channel_count_changed(self, event=None):
        try:
            count = int(self.channel_count_var.get())
        except Exception:
            count = TOTAL_CHANNELS

        # Only channels inside "No. of Channels" can be selected for testing.
        for ch, cb in enumerate(self.test_channel_checkbuttons, start=1):
            if ch <= count:
                cb.configure(state="normal")
            else:
                self.test_channel_select_vars[ch - 1].set(False)
                cb.configure(state="disabled")

        # If the user reduced the channel count and nothing remains selected,
        # automatically select Ch_1 so START always has a sensible default.
        if count >= 1 and not self._selected_test_channels():
            self.test_channel_select_vars[0].set(True)

        self._refresh_live_cards()
        self._test_channel_selection_changed()

    def _merge_live_readings(self, readings):
        """Update live display cache without replacing good values by ABB invalid data."""
        if readings is None:
            return

        merged = {}
        for ch in range(1, TOTAL_CHANNELS + 1):
            key = f"Ch_{ch}"
            raw = readings.get(key)

            if raw is not None:
                # read_abb_data() has already rejected ABB sentinel values,
                # NaN and infinity. Therefore a non-None value is genuine.
                self.last_valid_readings[key] = raw
                merged[key] = raw
            else:
                # Hold the last genuine reading for DISPLAY ONLY.
                merged[key] = self.last_valid_readings.get(key)

        self.last_readings = merged

    def _refresh_live_cards(self, event=None):
        try:
            count = int(self.channel_count_var.get())
        except Exception:
            count = 6

        readings = getattr(self, "last_readings", {}) or {}
        shown = []

        for i in range(1, TOTAL_CHANNELS + 1):
            card = self.live_cards[i - 1]
            if i <= count:
                card.grid()
                raw = readings.get(f"Ch_{i}")
                value = self._engineering_value(i, raw)
                unit = self._channel_unit(i)

                if value is None:
                    self.live_channel_vars[i - 1].set(f"Ch_{i}\nN/A {unit}")
                    shown.append(f"Ch_{i}=N/A")
                else:
                    self.live_channel_vars[i - 1].set(
                        f"Ch_{i}\n{value:.3f} {unit}"
                    )
                    shown.append(f"Ch_{i}={value:.3f} {unit}")
            else:
                card.grid_remove()

        self.channel_values_var.set(" | ".join(shown))


    # ========================================================
    # SETTINGS
    # ========================================================
    def _get_settings(self):
        ip = self.ip_var.get().strip()
        port = int(self.port_var.get())
        device_id = int(self.device_var.get())
        channel = int(self.channel_var.get())
        interval = float(self.interval_var.get())
        duration = float(self.duration_var.get())

        if not ip:
            raise ValueError("IP address cannot be empty.")
        if not 1 <= port <= 65535:
            raise ValueError("Invalid TCP port.")
        if not 0 <= device_id <= 255:
            raise ValueError(
                "Device ID must be between 0 and 255."
            )
        if not 1 <= channel <= 6:
            raise ValueError("Channel must be 1 to 6.")
        if interval <= 0:
            raise ValueError(
                "Sample interval must be greater than zero."
            )
        if duration <= 0:
            raise ValueError(
                "Test duration must be greater than zero."
            )

        return (
            ip, port, device_id,
            channel, interval, duration
        )

    # ========================================================
    # AUTOMATIC LIVE REFRESH
    # ========================================================
    def _schedule_live_refresh(self):
        if self.live_after_id is not None:
            try:
                self.after_cancel(self.live_after_id)
            except Exception:
                pass
        self.live_after_id = self.after(
            self.live_refresh_ms, self._auto_live_refresh
        )

    def _auto_live_refresh(self):
        self.live_after_id = None
        if not self.live_monitoring:
            return

        # During a test, _multi_channel_worker already polls the RVG200 and
        # updates the live display at the selected sample interval.
        if self.running:
            self._schedule_live_refresh()
            return

        try:
            ip = self.ip_var.get().strip()
            port = int(self.port_var.get())
            device_id = int(self.device_var.get())
            channel_count = int(self.channel_count_var.get())
            selected_channel = int(self.channel_var.get())

            readings, error = read_abb_data(
                ip, port, device_id, channel_count
            )
            if readings is not None:
                self._merge_live_readings(readings)
                self._refresh_live_cards()

                raw = self.last_readings.get(f"Ch_{selected_channel}")
                value = self._engineering_value(selected_channel, raw)
                unit = self._channel_unit(selected_channel)
                if value is None:
                    self.live_value_var.set(
                        f"Ch_{selected_channel}: N/A {unit}"
                    )
                else:
                    self.live_value_var.set(
                        f"Ch_{selected_channel}: {value:.3f} {unit}"
                    )

                valid_count = sum(
                    readings.get(f"Ch_{ch}") is not None
                    for ch in range(1, channel_count + 1)
                )
                self.status_var.set(
                    f"LIVE - {valid_count}/{channel_count} channels valid"
                )
                self.error_var.set(error or "")
            else:
                self.status_var.set("LIVE - RVG200 read failed")
                self.error_var.set(error or "Unable to read RVG200.")
        except Exception as exc:
            self.error_var.set(f"Live refresh: {type(exc).__name__}: {exc}")
        finally:
            if self.live_monitoring:
                self._schedule_live_refresh()

    # ========================================================
    # READ NOW
    # ========================================================
    def read_now(self):
        """Read every enabled RVG200 channel and update all live cards."""
        try:
            ip = self.ip_var.get().strip()
            port = int(self.port_var.get())
            device_id = int(self.device_var.get())
            channel_count = int(self.channel_count_var.get())
            selected_channel = int(self.channel_var.get())
        except Exception as exc:
            messagebox.showerror("Invalid Communication Settings", str(exc))
            return

        self.status_var.set(f"Reading Ch_1 to Ch_{channel_count}...")
        self.error_var.set("")
        self.update_idletasks()

        readings, error = read_abb_data(
            ip, port, device_id, channel_count
        )

        if readings is None:
            self.status_var.set("RVG200 read failed")
            self.error_var.set(error or "Unable to read RVG200.")
            return

        self._merge_live_readings(readings)
        self._refresh_live_cards()

        raw = self.last_readings.get(f"Ch_{selected_channel}")
        value = self._engineering_value(selected_channel, raw)
        unit = self._channel_unit(selected_channel)

        if value is None:
            self.live_value_var.set(f"Ch_{selected_channel}: N/A {unit}")
        else:
            self.live_value_var.set(
                f"Ch_{selected_channel}: {value:.3f} {unit}"
            )

        valid_count = sum(
            readings.get(f"Ch_{ch}") is not None
            for ch in range(1, channel_count + 1)
        )
        self.status_var.set(
            f"READ NOW complete - {valid_count}/{channel_count} channels valid"
        )
        self.error_var.set(error or "")

        # READ NOW also enables continuous live monitoring. The values will
        # now refresh automatically every second as the RVG200 changes.
        self.live_monitoring = True
        self._schedule_live_refresh()


    def _read_now_worker(
        self, ip, port, device_id, channel
    ):
        data, error = read_abb_data(
            ip, port, device_id
        )

        self.after(
            0,
            self._read_now_complete,
            data, error, channel
        )

    def _read_now_complete(
        self, data, error, channel
    ):
        if data is None:
            self.live_value_var.set("--")
            self.status_var.set("Read failed")
            self.error_var.set(
                error or "Unknown error"
            )
            return

        self._merge_live_readings(data)

        value = self.last_readings.get(f"Ch_{channel}")

        if value is None:
            self.live_value_var.set("--")
        else:
            self.live_value_var.set(
                f"{value:.3f}"
            )

        channel_values = []

        for ch in range(1, 7):
            value = self.last_readings.get(f"Ch_{ch}")

            if value is None:
                channel_values.append(
                    f"Ch_{ch}=N/A"
                )
            else:
                channel_values.append(
                    f"Ch_{ch}={value:.3f}"
                )

        self.channel_values_var.set(
            " | ".join(channel_values)
        )

        if error:
            self.status_var.set(
                "Read completed with warning"
            )
            self.error_var.set(error)
        else:
            self.status_var.set(
                "RVG200 read successful"
            )
            self.error_var.set("")

    # ========================================================
    # PRESSURE VALUE PARSER
    # ========================================================
    @staticmethod
    def _parse_pressure(value):
        """
        Parse a numeric pressure/deviation value.

        IMPORTANT:
        Applied Pressure must be entered in the SAME engineering unit
        as the RVG200 recording channel. The separate Test Pressure /
        Rating field may contain descriptions such as 20K.
        """
        if value is None:
            return None

        value = str(value).strip().replace(",", "")
        if not value:
            return None

        try:
            return float(value)
        except ValueError:
            raise ValueError(
                "Applied Pressure and Max Deviation must be numeric "
                "and in the same unit as the RVG200 channel."
            )

    # ========================================================
    # START TEST
    # ========================================================
    def start_test(self):
        """
        Start ONE hydrotest session and log ALL channels selected by
        'No. of Channels' simultaneously.

        Channel 1 = Test 1, Channel 2 = Test 2, etc.
        """
        if self.running:
            messagebox.showwarning("Test Running", "A hydrotest is already running.")
            return

        try:
            ip = self.ip_var.get().strip()
            port = int(self.port_var.get())
            device_id = int(self.device_var.get())
            interval = float(self.interval_var.get())
            duration_min = float(self.duration_var.get())
            channel_count = int(self.channel_count_var.get())

            if interval <= 0:
                raise ValueError("Sample interval must be greater than zero.")
            if duration_min <= 0:
                raise ValueError("Test duration must be greater than zero.")
            if not 1 <= channel_count <= TOTAL_CHANNELS:
                raise ValueError("Number of channels must be 1 to 6.")

            selected_channels = self._selected_test_channels()
            if not selected_channels:
                raise ValueError(
                    "Select at least one channel under Test Channels."
                )

        except Exception as exc:
            messagebox.showerror("Invalid Test Settings", str(exc))
            return

        # The hydrotest control fields are common to every selected test channel.
        # In particular, one Max Dev. value is applied to ALL selected channels.
        common_rating = self.input1_var.get().strip()
        common_rating_unit = self.test_pressure_unit1_var.get().strip()
        common_applied_text = self.applied1_var.get().strip()
        common_maxdev_text = self.max_dev1_var.get().strip()

        try:
            common_applied = float(common_applied_text or "0")
        except Exception:
            common_applied = 0.0
        try:
            common_allowed = float(common_maxdev_text or "0")
        except Exception:
            common_allowed = 0.0

        now = datetime.now()

        # test_data/test_results now use channel number as the key.
        self.test_data = {
            ch: [] for ch in selected_channels
        }
        self.test_results = {}
        self.test_baseline = {
            ch: None for ch in selected_channels
        }

        for test_no, ch in enumerate(selected_channels, start=1):
            self.test_results[ch] = {
                "test_no": test_no,
                "channel": ch,
                "input": common_rating,
                "test_pressure_unit": common_rating_unit,
                "applied_pressure": common_applied,
                "max_deviation_allowed": common_allowed,
                "measurement_type": self._channel_type(ch),
                "unit": self._channel_unit(ch),
                "offset": self._channel_offset(ch),
                "start_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "start_dt": now,
                "end_time": "",
                "duration_min": duration_min,
                "sample_interval": interval,
                "start_value": None,
                "end_value": None,
                "minimum": None,
                "maximum": None,
                "max_deviation": 0.0,
                "peak_signed_deviation": 0.0,
                "relative_deviation": 0.0,
                "status": "RUNNING",
                "test_state": "RUNNING",
            }

        self.running = True
        self.active_test = "ALL"
        self.stop_event.clear()
        self._update_buttons()
        selected_text = ", ".join(f"Ch_{ch}" for ch in selected_channels)
        self.status_var.set(
            f"RUNNING - logging {selected_text}"
        )
        self.error_var.set("")

        # The chart begins visually at zero immediately.
        self._redraw_graph()
        self._show_results()
        self.update_idletasks()

        self.worker = threading.Thread(
            target=self._multi_channel_worker,
            args=(
                ip, port, device_id, interval, duration_min,
                channel_count, selected_channels
            ),
            daemon=True
        )
        self.worker.start()

    def _multi_channel_worker(
        self, ip, port, device_id, interval, duration_min,
        channel_count, selected_channels
    ):
        t0 = time.monotonic()
        duration_sec = duration_min * 60.0
        next_sample = 0.0

        try:
            while not self.stop_event.is_set():
                elapsed = time.monotonic() - t0
                if elapsed >= duration_sec:
                    break

                if elapsed < next_sample:
                    if self.stop_event.wait(min(next_sample - elapsed, 0.05)):
                        break
                    continue

                readings, error = read_abb_data(
                    ip, port, device_id, channel_count
                )

                if readings is None:
                    self.after(
                        0, self._test_error_update,
                        error or "RVG200 read failed"
                    )
                else:
                    sample_time = datetime.now()
                    sample_elapsed = time.monotonic() - t0

                    for ch in selected_channels:
                        raw = readings.get(f"Ch_{ch}")
                        value = self._engineering_value(ch, raw)
                        if value is None:
                            continue

                        if self.test_baseline[ch] is None:
                            self.test_baseline[ch] = value

                            # Visual zero point requested by user.
                            # This is ONLY for the graph shape. It is not used
                            # in deviation or PASS/FAIL calculations.
                            self.test_data[ch].append({
                                "timestamp": sample_time,
                                "elapsed_min": 0.0,
                                "value": 0.0,
                                "graph_zero": True
                            })

                            # Actual first pressure follows immediately after zero.
                            self.test_data[ch].append({
                                "timestamp": sample_time,
                                "elapsed_min": max(sample_elapsed / 60.0, 0.0005),
                                "value": value,
                                "graph_zero": False
                            })
                        else:
                            self.test_data[ch].append({
                                "timestamp": sample_time,
                                "elapsed_min": sample_elapsed / 60.0,
                                "value": value,
                                "graph_zero": False
                            })

                    self.after(
                        0, self._multi_channel_live_update,
                        readings, selected_channels
                    )

                next_sample += interval
                now_elapsed = time.monotonic() - t0
                if next_sample <= now_elapsed:
                    next_sample = now_elapsed + interval

        except Exception as exc:
            self.after(
                0, self._test_error_update,
                f"{type(exc).__name__}: {exc}"
            )
        finally:
            self.after(
                0, self._finish_multi_channel_test,
                selected_channels, self.stop_event.is_set()
            )

    def _multi_channel_live_update(self, readings, selected_channels):
        # Keep the last valid value on the live cards if this poll contains
        # an ABB invalid/no-data sentinel. The worker deliberately logs only
        # the current valid readings, so held values never become test data.
        self._merge_live_readings(readings)
        self._refresh_live_cards()

        total_samples = 0
        for ch in selected_channels:
            result = self.test_results.get(ch, {})
            actual_points = [
                p for p in self.test_data.get(ch, [])
                if not p.get("graph_zero")
            ]
            values = [p["value"] for p in actual_points]
            total_samples = max(total_samples, len(values))

            if not values:
                continue

            baseline = self.test_baseline.get(ch)
            if baseline is None:
                baseline = values[0]
                self.test_baseline[ch] = baseline

            deviations = [v - baseline for v in values]
            peak = max(deviations, key=abs, default=0.0)

            result.update({
                "sample_count": len(values),
                "start_value": values[0],
                "end_value": values[-1],
                "minimum": min(values),
                "maximum": max(values),
                "max_deviation": abs(peak),
                "peak_signed_deviation": peak,
                "relative_deviation": (
                    abs(peak) / abs(baseline) * 100.0
                    if baseline not in (None, 0) else None
                ),
            })

        selected_text = ", ".join(f"Ch_{ch}" for ch in selected_channels)
        self.status_var.set(
            f"RUNNING - {selected_text} - {total_samples} samples/channel"
        )
        self.error_var.set("")
        self._show_results()
        self._redraw_graph()

    def _finish_multi_channel_test(self, selected_channels, stopped=False):
        for ch in selected_channels:
            result = self.test_results.get(ch, {})
            actual_points = [
                p for p in self.test_data.get(ch, [])
                if not p.get("graph_zero")
            ]
            values = [p["value"] for p in actual_points]

            if values:
                baseline = self.test_baseline.get(ch)
                if baseline is None:
                    baseline = values[0]

                deviations = [v - baseline for v in values]
                peak = max(deviations, key=abs, default=0.0)
                allowed = result.get("max_deviation_allowed", 0.0)

                result.update({
                    "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sample_count": len(values),
                    "start_value": values[0],
                    "end_value": values[-1],
                    "minimum": min(values),
                    "maximum": max(values),
                    "max_deviation": abs(peak),
                    "peak_signed_deviation": peak,
                    "relative_deviation": (
                        abs(peak) / abs(baseline) * 100.0
                        if baseline not in (None, 0) else None
                    ),
                    "status": "PASS" if abs(peak) <= allowed else "FAIL",
                    "test_state": "STOPPED" if stopped else "COMPLETE",
                })
            else:
                result.update({
                    "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sample_count": 0,
                    "status": "NO DATA",
                    "test_state": "STOPPED" if stopped else "COMPLETE",
                })

        self.running = False
        self.active_test = None
        self._update_buttons()
        self.status_var.set(
            "Test stopped" if stopped else "Test complete"
        )
        self._show_results()
        self._redraw_graph()

    def _test_error_update(self, message):
        self.error_var.set(str(message))

    def stop_test(self):
        if self.running:
            self.status_var.set("Stopping test...")
            self.stop_event.set()
            self.stop_btn.configure(state="disabled")


    # ========================================================
    # BUTTONS
    # ========================================================
    def _update_buttons(self):
        self.start_btn.configure(
            state=(
                "disabled"
                if self.running
                else "normal"
            )
        )

        self.stop_btn.configure(
            state=(
                "normal"
                if self.running
                else "disabled"
            )
        )

    # ========================================================
    # COMBINED GRAPH
    # ========================================================
    def _redraw_graph(self):
        if not MATPLOTLIB_OK:
            return

        self.ax.clear()
        for old_legend in list(self.figure.legends):
            old_legend.remove()
        self.ax.set_title("ABB RVG200 Hydrotest - Selected Channels vs Time", fontsize=12, pad=8)
        self.ax.set_xlabel("Elapsed Time (min)", labelpad=8, fontsize=10)
        self.ax.set_ylabel("Process Value", fontsize=10)
        self.ax.grid(True, which="both", alpha=0.24)
        self.ax.set_facecolor("#fbfcfd")

        # Faded Weatherford watermark in the dashboard graph.  It is kept
        # deliberately light so measured traces and grid lines remain clear.
        try:
            watermark = mpimg.imread(
                io.BytesIO(base64.b64decode(WEATHERFORD_LOGO_BASE64)),
                format="png"
            )
            self.ax.imshow(
                watermark,
                extent=(0.27, 0.73, 0.30, 0.70),
                transform=self.ax.transAxes,
                alpha=0.055,
                aspect="auto",
                zorder=0
            )
        except Exception:
            pass

        plotted = False
        max_x = 0.0
        max_y = 0.0

        # Plot ONLY channels selected for this test.
        channels = sorted(self.test_data.keys())

        for plot_index, ch in enumerate(channels):
            points = self.test_data.get(ch, [])
            if not points:
                continue

            actual = [p for p in points if not p.get("graph_zero")]
            if not actual:
                continue

            unit = self.test_results.get(ch, {}).get(
                "unit", self._channel_unit(ch)
            )

            actual_x = [float(p["elapsed_min"]) for p in actual]
            actual_y = [float(p["value"]) for p in actual]

            # IMPORTANT:
            # Always construct the DISPLAY trace from an explicit origin
            # (0 sec, 0 process value), irrespective of the stored first
            # sample time. This point is visual only and is NOT used in any
            # deviation/min/max/PASS-FAIL calculation.
            #
            # Put the first actual reading a small visible distance to the
            # right of zero so the rise from zero can clearly be seen.
            first_visible_x = max(
                min(float(self.interval_var.get()) / 60.0, 0.02),
                0.002
            )

            display_x = [0.0]
            display_y = [0.0]

            for i, (xv, yv) in enumerate(zip(actual_x, actual_y)):
                if i == 0:
                    display_x.append(first_visible_x)
                else:
                    display_x.append(max(xv, first_visible_x))
                display_y.append(yv)

            line, = self.ax.plot(
                display_x,
                display_y,
                linewidth=0.65,
                antialiased=True,
                label=f"Ch_{ch} - {self._channel_type(ch)} ({unit})"
            )

            plotted = True
            max_x = max(max_x, max(display_x))
            max_y = max(max_y, max(display_y))

            baseline = self.test_baseline.get(ch)
            if baseline is None:
                baseline = actual_y[0]

            deviations = [v - baseline for v in actual_y]
            peak_i = max(
                range(len(deviations)),
                key=lambda i: abs(deviations[i])
            )
            peak_dev = deviations[peak_i]

            start_x = first_visible_x
            start_y = actual_y[0]
            end_x = display_x[-1]
            end_y = actual_y[-1]
            end_dev = end_y - baseline

            # Start/end markers.
            self.ax.scatter(
                [start_x], [start_y],
                s=18, color=line.get_color(), zorder=5
            )
            self.ax.scatter(
                [end_x], [end_y],
                s=18, color=line.get_color(), zorder=5
            )

            # Only start and end pressure values are labelled on the graph.
            # Alternate label lanes so channels with similar pressure do not
            # cover each other. Full channel/result details are shown below
            # the graph and in the report summary, not on top of the trace.
            lane = plot_index // 2
            direction = 1 if (plot_index % 2 == 0) else -1
            start_y_offset = direction * (15 + lane * 15)
            end_y_offset = direction * (17 + lane * 17)

            self.ax.annotate(
                f"Ch_{ch} Start {start_y:.3f} {unit}",
                (start_x, start_y),
                xytext=(8, start_y_offset),
                textcoords="offset points",
                fontsize=7,
                color=line.get_color(),
                bbox=dict(
                    boxstyle="round,pad=0.16",
                    fc="white",
                    ec=line.get_color(),
                    alpha=0.90
                )
            )

            self.ax.annotate(
                f"Ch_{ch} End {end_y:.3f} {unit}",
                (end_x, end_y),
                xytext=(-8, end_y_offset),
                textcoords="offset points",
                ha="right",
                fontsize=7,
                color=line.get_color(),
                bbox=dict(
                    boxstyle="round,pad=0.16",
                    fc="white",
                    ec=line.get_color(),
                    alpha=0.90
                )
            )

        if plotted:
            try:
                requested_duration = float(self.duration_var.get())
            except Exception:
                requested_duration = 0.0

            # During a live test, preserve the requested test duration.
            # For imported/completed CSV data, fit the X axis to the actual
            # elapsed duration stored in the file instead of the current UI
            # duration setting.
            if self.running:
                right_limit = max(max_x * 1.03, requested_duration, 0.1)
            else:
                right_limit = max(max_x * 1.03, 0.1)
            self.ax.set_xlim(0.0, right_limit)

            # Y axis MUST start at zero so the pressure rise from 0 to the
            # first actual process value is visible.
            self.ax.set_ylim(
                0.0,
                max(max_y * 1.18, 1.0)
            )

            # Recording-channel details use a dedicated figure-level band
            # below the X-axis title. This prevents overlap with Elapsed Time.
            handles, labels = self.ax.get_legend_handles_labels()
            for old_legend in list(self.figure.legends):
                old_legend.remove()
            if handles:
                self.figure.legend(
                    handles, labels,
                    loc="lower center",
                    bbox_to_anchor=(0.5, 0.010),
                    ncol=max(1, min(len(handles), 6)),
                    fontsize=7.5,
                    frameon=False
                )
        else:
            # Immediately after START, show a true zero-origin graph.
            try:
                requested_duration = float(self.duration_var.get())
            except Exception:
                requested_duration = 1.0
            self.ax.set_xlim(0.0, max(requested_duration, 0.1))
            self.ax.set_ylim(0.0, 1.0)

        # Reserve a bottom band for recording-channel details/legend.
        self.figure.tight_layout(rect=(0.010, 0.095, 0.995, 0.990))
        self.canvas.draw()


    # ========================================================
    # RESULTS
    # ========================================================
    def _show_results(self):
        self.result_text.delete("1.0", tk.END)

        if not self.test_results:
            selected = self._selected_test_channels() or [1]
            for test_no, ch in enumerate(selected, start=1):
                self.result_text.insert(
                    tk.END,
                    f"CHANNEL {ch} / TEST {test_no}\n{'=' * 34}\n"
                    "Selected for test - not conducted.\n\n"
                )
            return

        # Keep this panel intentionally compact, matching the supplied
        # Weatherford report: only the essential test-result fields.
        for ch in sorted(self.test_results.keys()):
            result = self.test_results[ch]
            test_no = result.get("test_no", ch)
            unit = result.get("unit", self._channel_unit(ch))
            rating = result.get("input", "")
            rating_unit = result.get("test_pressure_unit", "")

            self.result_text.insert(
                tk.END,
                f"CHANNEL {ch} / TEST {test_no}\n{'=' * 34}\n"
                f"Input: {rating} {rating_unit}\n"
                f"Start: {result.get('start_time', '')}\n"
                f"End: {result.get('end_time', '')}\n"
                f"Test duration: {self._format_number(result.get('duration_min'))} min\n"
                f"Start value: {self._format_number(result.get('start_value'))} {unit}\n"
                f"End value: {self._format_number(result.get('end_value'))} {unit}\n"
                f"Max. deviation: {self._format_signed_number(result.get('max_deviation'))} {unit}\n"
                f"Allowed deviation: {self._format_signed_number(result.get('max_deviation_allowed'))} {unit}\n"
                f"Relative deviation: {self._format_signed_percent(result.get('relative_deviation'))}\n"
                f"Result: {result.get('status', '')}\n\n"
            )


    @staticmethod
    def _format_number(value):
        if value is None:
            return "--"

        try:
            return f"{float(value):.3f}"
        except Exception:
            return str(value)

    @staticmethod
    def _format_signed_number(value):
        if value is None:
            return "--"

        try:
            return f"±{float(value):.3f}"
        except Exception:
            return str(value)

    @staticmethod
    def _format_signed_percent(value):
        if value is None:
            return "--"

        try:
            return f"±{float(value):.3f} %"
        except Exception:
            return str(value)

    # ========================================================
    # CERTIFICATE INFORMATION
    # ========================================================
    def _certificate_header(self):
        return {
            "Customer": self.customer_var.get(),
            "Work Order": self.work_order_var.get(),
            "Tools": self.tools_var.get(),
            "Description": self.description_var.get(),
            "JDE": self.jde_var.get(),
            "Documents": self.documents_var.get(),
            "Technician": self.technician_var.get(),
            "Recorded on": self.recorded_var.get()
        }

    # ========================================================
    # EXPORT CSV
    # ========================================================
    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export Complete Hydrotest CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        header = self._certificate_header()
        rows = []

        for test_no in sorted(self.test_results.keys()):
            result = self.test_results.get(test_no, {})
            points = self.test_data.get(test_no, [])

            if points:
                for point in points:
                    row = dict(header)

                    row.update({
                        "Test": result.get("test_no", test_no),
                        "Input_Test_Pressure":
                            result.get("input", ""),
                        "Channel":
                            result.get("channel", ""),
                        "Applied_Pressure_Numeric":
                            result.get("applied_pressure", ""),
                        "Max_Deviation_Allowed":
                            result.get("max_deviation_allowed", ""),
                        "Measurement_Type":
                            result.get("measurement_type", self.measurement_type_var.get()),
                        "Engineering_Unit":
                            result.get("unit", self.unit_var.get()),
                        "Test_Start":
                            result.get("start_time", ""),
                        "Test_End":
                            result.get("end_time", ""),
                        "Duration_min":
                            result.get("duration_min", ""),
                        "Sample_Count":
                            result.get("sample_count", ""),
                        "Start_Value":
                            result.get("start_value", ""),
                        "End_Value":
                            result.get("end_value", ""),
                        "Minimum":
                            result.get("minimum", ""),
                        "Maximum":
                            result.get("maximum", ""),
                        "Max_Deviation":
                            result.get("max_deviation", ""),
                        "Relative_Deviation_Percent":
                            result.get(
                                "relative_deviation", ""
                            ),
                        "Result":
                            result.get("status", ""),
                        "Sample_Timestamp":
                            point.get("timestamp", ""),
                        "Elapsed_min":
                            point.get("elapsed_min", ""),
                        "RVG200_Value":
                            point.get("value", ""),
                        "Graph_Zero":
                            bool(point.get("graph_zero", False))
                    })

                    rows.append(row)

            elif result:
                row = dict(header)

                row.update({
                    "Test": result.get("test_no", test_no),
                    "Input_Test_Pressure":
                        result.get("input", ""),
                    "Channel":
                        result.get("channel", ""),
                    "Applied_Pressure_Numeric":
                        result.get("applied_pressure", ""),
                    "Max_Deviation_Allowed":
                        result.get("max_deviation_allowed", ""),
                    "Measurement_Type":
                        result.get("measurement_type", self.measurement_type_var.get()),
                    "Engineering_Unit":
                        result.get("unit", self.unit_var.get()),
                    "Test_Start":
                        result.get("start_time", ""),
                    "Test_End":
                        result.get("end_time", ""),
                    "Duration_min":
                        result.get("duration_min", ""),
                    "Sample_Count":
                        result.get("sample_count", ""),
                    "Start_Value":
                        result.get("start_value", ""),
                    "End_Value":
                        result.get("end_value", ""),
                    "Minimum":
                        result.get("minimum", ""),
                    "Maximum":
                        result.get("maximum", ""),
                    "Max_Deviation":
                        result.get("max_deviation", ""),
                    "Relative_Deviation_Percent":
                        result.get(
                            "relative_deviation", ""
                        ),
                    "Result":
                        result.get("status", "")
                })

                rows.append(row)

        fields = [
            "Customer",
            "Work Order",
            "Tools",
            "Description",
            "JDE",
            "Documents",
            "Technician",
            "Recorded on",
            "Test",
            "Input_Test_Pressure",
            "Channel",
            "Applied_Pressure_Numeric",
            "Max_Deviation_Allowed",
            "Measurement_Type",
            "Engineering_Unit",
            "Test_Start",
            "Test_End",
            "Duration_min",
            "Sample_Count",
            "Start_Value",
            "End_Value",
            "Minimum",
            "Maximum",
            "Max_Deviation",
            "Relative_Deviation_Percent",
            "Result",
            "Sample_Timestamp",
            "Elapsed_min",
            "RVG200_Value",
            "Graph_Zero"
        ]

        try:
            with open(
                path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=fields
                )
                writer.writeheader()
                writer.writerows(rows)

            messagebox.showinfo(
                "CSV Export",
                (
                    "Complete hydrotest data exported "
                    "successfully.\n\n"
                    f"{path}"
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "CSV Export Error",
                str(exc)
            )

    # ========================================================
    # IMPORT CSV
    # ========================================================
    def import_csv(self):
        path = filedialog.askopenfilename(
            title="Import Previous Hydrotest CSV",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        try:
            with open(path, "r", newline="", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))
            if not rows:
                raise ValueError("The CSV file is empty.")

            first = rows[0]
            mapping = {
                "Customer": self.customer_var,
                "Work Order": self.work_order_var,
                "Tools": self.tools_var,
                "Description": self.description_var,
                "JDE": self.jde_var,
                "Documents": self.documents_var,
                "Technician": self.technician_var,
                "Recorded on": self.recorded_var,
            }
            for key, variable in mapping.items():
                if key in first:
                    variable.set(first.get(key, ""))

            # Discover every channel contained in the CSV (Ch1 ... Ch6).
            # Older versions incorrectly limited imports to Test 1 and Test 2.
            imported_channels = []
            for row in rows:
                try:
                    ch = int(float(row.get("Channel") or row.get("Test") or 0))
                except (ValueError, TypeError):
                    continue
                if 1 <= ch <= TOTAL_CHANNELS and ch not in imported_channels:
                    imported_channels.append(ch)
            imported_channels.sort()
            if not imported_channels:
                raise ValueError("No valid channel data (1 to 6) was found in the CSV file.")

            self.test_data = {ch: [] for ch in imported_channels}
            self.test_results = {ch: {} for ch in imported_channels}
            self.test_baseline = {ch: None for ch in imported_channels}

            for row in rows:
                try:
                    ch = int(float(row.get("Channel") or row.get("Test") or 0))
                    if ch not in self.test_data:
                        continue

                    result = self.test_results[ch]
                    if not result:
                        result.update({
                            "test_no": ch,
                            "channel": ch,
                            "input": row.get("Input_Test_Pressure", ""),
                            "test_pressure_unit": row.get("Test_Pressure_Unit", ""),
                            "applied_pressure": self._to_float(row.get("Applied_Pressure_Numeric")),
                            "max_deviation_allowed": self._to_float(row.get("Max_Deviation_Allowed")),
                            "measurement_type": row.get("Measurement_Type", "") or self._channel_type(ch),
                            "unit": row.get("Engineering_Unit", "") or self._channel_unit(ch),
                            "offset": self._to_float(row.get("Offset")) or 0.0,
                            "start_time": row.get("Test_Start", ""),
                            "end_time": row.get("Test_End", ""),
                            "duration_min": self._to_float(row.get("Duration_min")),
                            "sample_count": self._to_int(row.get("Sample_Count")),
                            "start_value": self._to_float(row.get("Start_Value")),
                            "end_value": self._to_float(row.get("End_Value")),
                            "minimum": self._to_float(row.get("Minimum")),
                            "maximum": self._to_float(row.get("Maximum")),
                            "max_deviation": self._to_float(row.get("Max_Deviation")),
                            "relative_deviation": self._to_float(row.get("Relative_Deviation_Percent")),
                            "status": row.get("Result", ""),
                            "test_state": "IMPORTED",
                        })
                        if result.get("max_deviation_allowed") is None:
                            result["max_deviation_allowed"] = 0.20

                    timestamp = row.get("Sample_Timestamp")
                    value = self._to_float(row.get("RVG200_Value"))
                    elapsed = self._to_float(row.get("Elapsed_min"))
                    if timestamp and value is not None:
                        # New CSVs explicitly identify the visual graph-zero point.
                        graph_zero_text = str(row.get("Graph_Zero", "")).strip().lower()
                        graph_zero = graph_zero_text in ("1", "true", "yes", "y")
                        self.test_data[ch].append({
                            "timestamp": timestamp,
                            "elapsed_min": elapsed if elapsed is not None else 0.0,
                            "value": value,
                            "graph_zero": graph_zero,
                        })
                except (ValueError, TypeError):
                    continue

            # Backward compatibility with CSVs exported before Graph_Zero existed:
            # the application used to export its visual (0,0) point as if it were
            # a measurement. Detect that leading visual point and exclude it from
            # calculations while retaining it for display.
            for ch in imported_channels:
                pts = self.test_data[ch]
                if len(pts) >= 2 and not any(p.get("graph_zero") for p in pts):
                    p0, p1 = pts[0], pts[1]
                    if (abs(float(p0.get("elapsed_min", 0.0))) < 1e-12
                            and abs(float(p0.get("value", 0.0))) < 1e-12
                            and abs(float(p1.get("value", 0.0))) > 1e-12):
                        p0["graph_zero"] = True

                actual = [p for p in pts if not p.get("graph_zero")]
                result = self.test_results[ch]
                if not actual:
                    continue

                values = [float(p["value"]) for p in actual]
                baseline = values[0]
                self.test_baseline[ch] = baseline
                deviations = [v - baseline for v in values]
                peak = max(deviations, key=abs, default=0.0)
                allowed = result.get("max_deviation_allowed")

                result.update({
                    "sample_count": len(values),
                    "start_value": values[0],
                    "end_value": values[-1],
                    "minimum": min(values),
                    "maximum": max(values),
                    "max_deviation": abs(peak),
                    "peak_signed_deviation": peak,
                    "relative_deviation": (abs(peak) / abs(baseline) * 100.0
                                           if baseline != 0 else None),
                })
                if allowed is not None:
                    result["status"] = "PASS" if abs(peak) <= allowed else "FAIL"

            # Number tests sequentially by selected/imported channel order.
            # Example: Ch_1 + Ch_3 => Ch_1/Test 1 and Ch_3/Test 2.
            for seq, ch in enumerate(imported_channels, start=1):
                self.test_results[ch]["test_no"] = seq

            # Restore imported channel availability and selections in the UI.
            highest_channel = max(imported_channels)
            self.channel_count_var.set(str(highest_channel))
            for ch in range(1, TOTAL_CHANNELS + 1):
                self.test_channel_select_vars[ch - 1].set(ch in imported_channels)
            self._channel_count_changed()

            # Restore per-channel type/unit/offset where possible.
            for ch in imported_channels:
                result = self.test_results[ch]
                if result.get("measurement_type"):
                    self.channel_type_vars[ch - 1].set(result["measurement_type"])
                if result.get("unit"):
                    self.channel_unit_vars[ch - 1].set(result["unit"])
                self.channel_offset_vars[ch - 1].set(str(result.get("offset", 0.0)))

            imported_elapsed = [
                float(p.get("elapsed_min", 0.0) or 0.0)
                for pts in self.test_data.values() for p in pts
            ]
            imported_result_durations = [
                float(r.get("duration_min") or 0.0)
                for r in self.test_results.values()
                if r and r.get("duration_min") is not None
            ]
            imported_duration = max(imported_elapsed + imported_result_durations + [0.0])
            if imported_duration > 0:
                self.duration_var.set(f"{imported_duration:.6g}")

            if 1 in self.test_results:
                r = self.test_results[1]
                self.input1_var.set(str(r.get("input", "")))
                if r.get("applied_pressure") is not None:
                    self.applied1_var.set(str(r["applied_pressure"]))
                if r.get("max_deviation_allowed") is not None:
                    self.max_dev1_var.set(str(r["max_deviation_allowed"]))
            if 2 in self.test_results:
                r = self.test_results[2]
                self.input2_var.set(str(r.get("input", "")))
                if r.get("applied_pressure") is not None:
                    self.applied2_var.set(str(r["applied_pressure"]))
                if r.get("max_deviation_allowed") is not None:
                    self.max_dev2_var.set(str(r["max_deviation_allowed"]))

            self._show_results()
            self._redraw_graph()
            self.status_var.set(
                "Previous hydrotest imported: " +
                ", ".join(f"Ch_{ch}" for ch in imported_channels)
            )
            messagebox.showinfo(
                "CSV Import",
                "Imported channels: " + ", ".join(f"Ch_{ch}" for ch in imported_channels)
            )

        except Exception as exc:
            messagebox.showerror("CSV Import Error", str(exc))

    @staticmethod
    def _to_float(value):
        if value in ("", None):
            return None
        try:
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _to_int(value):
        if value in ("", None):
            return 0
        try:
            return int(float(value))
        except Exception:
            return 0

    # ========================================================
    # PDF CERTIFICATE - ONE PAGE LANDSCAPE
    # ========================================================
    def export_pdf(self):
        if not REPORTLAB_OK:
            messagebox.showerror(
                "Missing Package",
                "ReportLab is not installed.\n\nRun:\npython -m pip install reportlab"
            )
            return

        if not any(self.test_data.get(n, []) for n in self.test_data):
            messagebox.showwarning(
                "No Test Data",
                "Conduct or import at least one selected test channel first."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save Hydrotest Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return

        graph_path = os.path.splitext(path)[0] + "_graph.png"

        try:
            # Save the current combined graph.
            self.figure.savefig(
                graph_path,
                dpi=300,
                bbox_inches="tight"
            )

            doc = SimpleDocTemplate(
                path,
                pagesize=landscape(A4),
                leftMargin=7 * mm,
                rightMargin=7 * mm,
                topMargin=6 * mm,
                bottomMargin=6 * mm
            )

            styles = getSampleStyleSheet()
            tiny = ParagraphStyle(
                "tiny",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=6.4,
                leading=7.2
            )
            tiny_bold = ParagraphStyle(
                "tinybold",
                parent=tiny,
                fontName="Helvetica-Bold"
            )
            title_style = ParagraphStyle(
                "reporttitle",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=11,
                alignment=TA_CENTER
            )

            # Weatherford logo is embedded directly in this Python file so the
            # report does not depend on a separate image file. If a local
            # Weatherford-Logo.png is present beside the script, it is used
            # first; otherwise the embedded logo is used automatically.
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_candidates = [
                os.path.join(script_dir, WEATHERFORD_LOGO_FILENAME),
                os.path.join(script_dir, "Weatherford-Logo(1).png"),
            ]
            logo_path = next(
                (p for p in logo_candidates if os.path.exists(p)), None
            )

            logo_source = None
            if logo_path:
                logo_source = logo_path
            else:
                try:
                    logo_source = io.BytesIO(base64.b64decode(WEATHERFORD_LOGO_BASE64))
                except Exception:
                    logo_source = None

            # Match the supplied Weatherford certificate layout: keep the
            # top focused on the graph/results and place the company logo in
            # the lower-left information block beneath the graph.
            story = [
                Paragraph("HYDROTEST REPORT", title_style),
                Spacer(1, 2 * mm)
            ]

            summary_cells = []
            selected_report_channels = sorted(
                ch for ch, r in self.test_results.items() if r
            )

            for ch in selected_report_channels:
                r = self.test_results.get(ch, {}) or {}
                display_test_no = r.get("test_no", ch)
                if not r:
                    html = f"<b>Test {display_test_no}</b><br/>Not conducted."
                else:
                    status = r.get("status", "")
                    rating = r.get("input", "")
                    rating_unit = r.get("test_pressure_unit", "")
                    unit = r.get("unit", self._channel_unit(ch))
                    def fv(key):
                        v = r.get(key)
                        return "" if v in (None, "") else f"{float(v):.3f}"

                    # Compact Weatherford-style result block: only required fields.
                    html = (
                        f"<b>Test {display_test_no} ... {status}</b><br/>"
                        f"Input: {rating} {rating_unit}<br/>"
                        f"Start: {r.get('start_time', '')}<br/>"
                        f"End: {r.get('end_time', '')}<br/>"
                        f"Test duration: {r.get('duration_min', '')} min<br/>"
                        f"Start value: {fv('start_value')} {unit}<br/>"
                        f"End value: {fv('end_value')} {unit}<br/>"
                        f"Max. deviation: ±{fv('max_deviation')} {unit}<br/>"
                        f"Allowed deviation: ±{fv('max_deviation_allowed')} {unit}<br/>"
                        f"Relative deviation: "
                        + (
                            ""
                            if r.get("relative_deviation") in (None, "")
                            else f"±{float(r.get('relative_deviation')):.2f}%"
                        )
                    )
                summary_cells.append(Paragraph(html, tiny))

            graph_img = Image(graph_path, width=184 * mm, height=96 * mm)
            if not summary_cells:
                summary_cells = [Paragraph("No test summary available.", tiny)]

            summary_rows = []
            for idx, cell in enumerate(summary_cells):
                if idx:
                    summary_rows.append([Spacer(1, 1.5 * mm)])
                summary_rows.append([cell])

            summary = Table(summary_rows, colWidths=[77 * mm])
            summary.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))

            top = Table(
                [[graph_img, summary]],
                colWidths=[188 * mm, 80 * mm]
            )
            top.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
                ("LINEBEFORE", (1, 0), (1, 0), 0.7, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(top)
            story.append(Spacer(1, 2 * mm))

            h = self._certificate_header()
            report_units = sorted({
                r.get("unit", "")
                for r in self.test_results.values()
                if r and r.get("unit", "")
            })
            unit = ", ".join(report_units) if report_units else self.unit_var.get()

            info = [
                [
                    Paragraph("<b>Customer :</b>", tiny), Paragraph(str(h.get("Customer", "")), tiny),
                    Paragraph("<b>JDE :</b>", tiny), Paragraph(str(h.get("JDE", "")), tiny),
                ],
                [
                    Paragraph("<b>Work Order :</b>", tiny), Paragraph(str(h.get("Work Order", "")), tiny),
                    Paragraph("<b>Documents :</b>", tiny), Paragraph(str(h.get("Documents", "")), tiny),
                ],
                [
                    Paragraph("<b>Tools :</b>", tiny), Paragraph(str(h.get("Tools", "")), tiny),
                    Paragraph("<b>Technician :</b>", tiny), Paragraph(str(h.get("Technician", "")), tiny),
                ],
                [
                    Paragraph("<b>Description :</b>", tiny), Paragraph(str(h.get("Description", "")), tiny),
                    Paragraph("<b>Recorded on :</b>", tiny), Paragraph(str(h.get("Recorded on", "")), tiny),
                ],
                [
                    Paragraph("<b>Measurement :</b>", tiny),
                    Paragraph(f"{self.measurement_type_var.get()} / {unit}", tiny),
                    Paragraph("<b>Signature :</b>", tiny),
                    Paragraph("____________________________", tiny),
                ],
            ]

            info_table = Table(
                info,
                colWidths=[22 * mm, 78 * mm, 22 * mm, 88 * mm]
            )
            info_table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            # Weatherford logo at the bottom-left, below the graph, matching
            # the supplied sample report arrangement.
            if logo_source:
                try:
                    if hasattr(logo_source, "seek"):
                        logo_source.seek(0)
                    bottom_logo = Image(
                        logo_source, width=46 * mm, height=24 * mm,
                        kind="proportional"
                    )
                    bottom = Table(
                        [[bottom_logo, info_table]],
                        colWidths=[50 * mm, 218 * mm]
                    )
                    bottom.setStyle(TableStyle([
                        ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (0, 0), "CENTER"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]))
                    story.append(bottom)
                except Exception:
                    story.append(info_table)
            else:
                story.append(info_table)

            doc.build(story)

            try:
                if os.path.exists(graph_path):
                    os.remove(graph_path)
            except Exception:
                pass

            messagebox.showinfo(
                "Report Created",
                f"PDF report created successfully.\n\n{path}"
            )

            try:
                if os.name == "nt":
                    os.startfile(path)
            except Exception:
                pass

        except Exception as exc:
            messagebox.showerror(
                "PDF Report Error",
                f"{type(exc).__name__}: {exc}"
            )

    def clear_tests(self):
        if self.running:
            messagebox.showwarning(
                "Test Running",
                "Stop the active test first."
            )
            return

        if not messagebox.askyesno(
            "Clear Tests",
            "Clear Test 1 and Test 2 data?"
        ):
            return

        self.test_data = {1: [], 2: []}
        self.test_results = {1: {}, 2: {}}
        self.test_baseline = {1: None, 2: None}
        self.active_test = None
        self.stop_event.clear()

        self._show_results()
        self._redraw_graph()

        self.status_var.set(
            "Ready - click Read Now"
        )
        self.error_var.set("")
        self.live_value_var.set("--")

    # ========================================================
    # CLOSE
    # ========================================================
    def _close(self):
        self.running = False
        self.stop_event.set()
        self.destroy()


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app = HydrotestApp()
    app.mainloop()
