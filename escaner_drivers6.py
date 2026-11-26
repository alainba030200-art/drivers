import csv
import ctypes
import html as html_lib
import json
import os
import re
import subprocess
import sys
import threading
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


CLASS_TRANSLATIONS = {
    "DISPLAY": "Pantalla / Tarjeta Gráfica",
    "NET": "Red / Wi-Fi / Ethernet",
    "MEDIA": "Audio / Video / Multimedia",
    "SOUND": "Audio / Sonido",
    "USB": "Controlador USB",
    "HIDCLASS": "Dispositivo de Entrada (Teclado/Mouse)",
    "KEYBOARD": "Teclado",
    "MOUSE": "Mouse / Panel Táctil",
    "DISKDRIVE": "Almacenamiento / Disco",
    "SCSIADAPTER": "Controladora de Almacenamiento (SATA/NVMe)",
    "HDC": "Controladora IDE / ATA",
    "BLUETOOTH": "Bluetooth",
    "SYSTEM": "Chipset / Dispositivo del Sistema",
    "PROCESSOR": "Procesador (CPU)",
    "MONITOR": "Monitor",
    "CAMERA": "Cámara / Webcam",
    "IMAGE": "Cámara / Escáner",
    "PRINTER": "Impresora",
    "PORTS": "Puertos (COM / LPT)",
    "BATTERY": "Batería / Energía",
    "BIOMETRIC": "Biometría / Huella",
    "SENSOR": "Sensor",
    "MTD": "Memoria Flash / Lector SD",
    "WPD": "Dispositivo Portátil (MTP/USB)",
    "SOFTWAREDEVICE": "Dispositivo de Software",
    "EXTENSION": "Extensión de Controlador",
    "FIRMWARE": "Firmware / UEFI",
    "VOLUME": "Volumen de Almacenamiento",
    "CDROM": "Unidad Óptica (CD/DVD)",
}

PNP_ERROR_DESCRIPTIONS = {
    1: "Dispositivo no configurado correctamente (Código 1)",
    10: "El dispositivo no puede iniciarse (Código 10)",
    18: "Reinstalar controladores de este dispositivo (Código 18)",
    22: "Dispositivo deshabilitado (Código 22)",
    28: "Controladores no instalados (Código 28)",
    31: "El dispositivo no funciona correctamente (Código 31)",
    43: "Windows detuvo este dispositivo por problemas (Código 43)",
}

VENDOR_ID_MAP = {
    "10DE": ("NVIDIA", "https://www.nvidia.com/es-la/drivers/"),
    "1002": ("AMD", "https://www.amd.com/es/support/download/drivers.html"),
    "1022": ("AMD", "https://www.amd.com/es/support/download/drivers.html"),
    "8086": ("Intel", "https://www.intel.la/content/www/xl/es/download-center/home.html"),
    "10EC": ("Realtek", "https://www.realtek.com/Download/Index?cate_id=193"),
    "0BDA": ("Realtek", "https://www.realtek.com/Download/Index?cate_id=193"),
    "14E4": ("Broadcom", "https://www.broadcom.com/support/download-search"),
    "168C": ("Qualcomm Atheros", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "17CB": ("Qualcomm", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "14C3": ("MediaTek", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "0E8D": ("MediaTek", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "1969": ("Qualcomm Atheros", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "1B21": ("ASMedia", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "1043": ("ASUS", "https://www.asus.com/support/download-center/"),
    "1028": ("Dell", "https://www.dell.com/support/home/es-mx?app=drivers"),
    "103C": ("HP", "https://support.hp.com/mx-es/drivers"),
    "17AA": ("Lenovo", "https://pcsupport.lenovo.com/mx/es"),
    "1462": ("MSI", "https://www.msi.com/support/download"),
    "1458": ("Gigabyte", "https://www.gigabyte.com/Support"),
    "1849": ("ASRock", "https://www.asrock.com/support/index.asp"),
    "046D": ("Logitech", "https://support.logi.com/hc/es"),
    "1532": ("Razer", "https://mysupport.razer.com/"),
    "045E": ("Microsoft", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "0A12": ("Cambridge Silicon Radio (CSR Bluetooth)", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "0CF3": ("Qualcomm Atheros", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
    "13D3": ("IMC Networks / AzureWave", "https://www.catalog.update.microsoft.com/Search.aspx?q="),
}

VENDOR_NAME_URLS = {
    "nvidia": "https://www.nvidia.com/es-la/drivers/",
    "amd": "https://www.amd.com/es/support/download/drivers.html",
    "advanced micro devices": "https://www.amd.com/es/support/download/drivers.html",
    "intel": "https://www.intel.la/content/www/xl/es/download-center/home.html",
    "realtek": "https://www.realtek.com/Download/Index?cate_id=193",
    "broadcom": "https://www.broadcom.com/support/download-search",
    "qualcomm": "https://www.catalog.update.microsoft.com/Search.aspx?q=",
    "mediatek": "https://www.catalog.update.microsoft.com/Search.aspx?q=",
    "asus": "https://www.asus.com/support/download-center/",
    "dell": "https://www.dell.com/support/home/es-mx?app=drivers",
    "hp": "https://support.hp.com/mx-es/drivers",
    "hewlett": "https://support.hp.com/mx-es/drivers",
    "lenovo": "https://pcsupport.lenovo.com/mx/es",
    "msi": "https://www.msi.com/support/download",
    "gigabyte": "https://www.gigabyte.com/Support",
    "asrock": "https://www.asrock.com/support/index.asp",
    "logitech": "https://support.logi.com/hc/es",
}


def parse_version_tuple(ver_str: str) -> tuple[int, ...]:
    """Convierte una versión tipo '10.0.19041.1' en tupla numérica comparable."""
    nums = re.findall(r"\d+", ver_str or "")
    return tuple(int(n) for n in nums) if nums else (0,)


def parse_any_date(date_str: str) -> datetime | None:
    """Acepta YYYY-MM-DD, MM/DD/YYYY o DD/MM/YYYY."""
    s = (date_str or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:10], fmt)
        except ValueError:
            continue
    return None


def is_newer_candidate(
    inst_ver: str, inst_date: str, cand_ver: str, cand_date: str
) -> tuple[bool, str]:
    """Determina si un paquete candidato supera al instalado por fecha o versión."""
    v_inst = parse_version_tuple(inst_ver)
    v_cand = parse_version_tuple(cand_ver)
    d_inst = parse_any_date(inst_date)
    d_cand = parse_any_date(cand_date)

    ver_newer = bool(cand_ver) and v_cand > v_inst and v_inst != (0,)
    date_newer = bool(d_cand and d_inst and d_cand.date() > d_inst.date())

    if ver_newer and date_newer:
        return True, "Versión y fecha superiores"
    if ver_newer:
        return True, "Versión superior"
    if date_newer:
        return True, "Fecha más reciente"
    if v_inst == (0,) and (cand_ver or d_cand):
        return True, "Disponible para instalar"
    return False, "Igual o anterior"


def identify_vendor_from_hwid(hwid: str, current_provider: str) -> tuple[str, str]:
    upper = (hwid or "").upper()
    match = re.search(r"(?:VEN_|VID_)([0-9A-F]{4})", upper)
    if match:
        ven_code = match.group(1)
        if ven_code in VENDOR_ID_MAP:
            return VENDOR_ID_MAP[ven_code]

    prov_lower = (current_provider or "").lower()
    for key, url in VENDOR_NAME_URLS.items():
        if key in prov_lower:
            return (current_provider, url)

    return (current_provider or "Desconocido", "")


def extract_clean_hwid(raw_hwid: str) -> str:
    if not raw_hwid:
        return ""
    upper = raw_hwid.upper()
    m_pci = re.search(r"(PCI\\VEN_[0-9A-F]{4}&DEV_[0-9A-F]{4})", upper)
    if m_pci:
        return m_pci.group(1)
    m_usb = re.search(r"(USB\\VID_[0-9A-F]{4}&PID_[0-9A-F]{4})", upper)
    if m_usb:
        return m_usb.group(1)
    m_bth = re.search(r"(VID_[0-9A-F]{4}&PID_[0-9A-F]{4})", upper)
    if m_bth:
        return m_bth.group(1)
    parts = raw_hwid.split("&")
    if len(parts) >= 2:
        return f"{parts[0]}&{parts[1]}"
    return raw_hwid


def detect_hardware_type(dev_class: str, device_name: str, hardware_id: str) -> str:
    cls_key = (dev_class or "").strip().upper()
    if cls_key in CLASS_TRANSLATIONS:
        return CLASS_TRANSLATIONS[cls_key]

    text = f"{device_name} {hardware_id}".lower()
    if any(k in text for k in ("graphics", "radeon", "geforce", "nvidia", "uhd", "display", "vga")):
        return "Pantalla / Tarjeta Gráfica"
    if any(k in text for k in ("wi-fi", "wifi", "wireless", "ethernet", "lan", "network", "802.11")):
        return "Red / Wi-Fi / Ethernet"
    if any(k in text for k in ("audio", "realtek", "sound", "speaker", "microphone", "hdaudio")):
        return "Audio / Sonido"
    if "bluetooth" in text or "bth" in text:
        return "Bluetooth"
    if any(k in text for k in ("nvme", "sata", "ahci", "disk", "ssd", "hdd", "storage")):
        return "Almacenamiento / Disco"
    if "usb" in text or "xhci" in text:
        return "Controlador USB"
    if any(k in text for k in ("pci", "acpi", "chipset", "smbus", "bridge", "system")):
        return "Chipset / Dispositivo del Sistema"
    if dev_class:
        return f"Otro ({dev_class})"
    return "Hardware General / Sin clasificar"


def is_virtual_device(hardware_id: str, dev_id_hint: str = "") -> bool:
    """True si el ID corresponde a un dispositivo virtual (ROOT\\, SWD\\, etc.)."""
    up = (hardware_id or "").strip().upper()
    return up.startswith(("ROOT\\", "SWD\\", "UMB\\", "STORAGE\\VOLUME", "HTREE\\ROOT"))


def evaluate_driver_classification(
    device_name: str,
    provider: str,
    detected_vendor: str,
    version: str,
    date_str: str,
    inf: str,
    dev_class: str,
    error_code: int,
    hardware_id: str = "",
    min_years_threshold: float = 3.0,
) -> tuple[str, str, str, str]:
    if error_code == 28 or (not version and not inf):
        msg = PNP_ERROR_DESCRIPTIONS.get(error_code, "Controlador no instalado — Necesita instalar/actualizar.")
        return ("Necesita actualizarse", "missing", "missing", msg)

    if error_code and error_code != 0:
        msg = PNP_ERROR_DESCRIPTIONS.get(error_code, f"Error de dispositivo (Código {error_code}) — Necesita reinstalarse.")
        return ("Necesita actualizarse", "missing", "missing", msg)

    prov_low = (provider or "").lower()
    ven_low = (detected_vendor or "").lower()
    inf_low = (inf or "").lower()
    cls_up = (dev_class or "").upper()
    ver_clean = (version or "").strip()

    is_win_core_date = date_str.startswith("2006-06-")
    is_win_build_ver = ver_clean.startswith(("10.0.19041.", "10.0.22000.", "10.0.22621.", "10.0.26100."))
    core_infs = {
        "machine.inf", "hal.inf", "acpi.inf", "disk.inf", "volume.inf",
        "cpu.inf", "pci.inf", "usb.inf", "usbport.inf", "usbhub3.inf",
        "usbxhci.inf", "msmouse.inf", "keyboard.inf", "monitor.inf",
        "bth.inf", "tdibth.inf", "bthleenum.inf", "microsoft_bluetooth_a2dp.inf",
        "audioendpoint.inf", "hdaudbus.inf", "softwaredevice.inf", "c_swdevice.inf",
    }

    structural_infs = {
        "machine.inf", "hal.inf", "acpi.inf", "disk.inf", "volume.inf", "cpu.inf", "pci.inf",
        "usb.inf", "usbport.inf", "usbhub3.inf", "usbxhci.inf", "msmouse.inf", "keyboard.inf",
        "monitor.inf", "softwaredevice.inf", "c_swdevice.inf", "audioendpoint.inf", "hdaudbus.inf",
    }
    is_inbox_driver = is_win_core_date or is_win_build_ver or inf_low in core_infs

    third_party_hw = (
        ven_low not in ("", "microsoft", "desconocido")
        and inf_low not in structural_infs
        and not is_virtual_device(hardware_id)
        and cls_up not in ("PROCESSOR", "VOLUME", "SOFTWAREDEVICE", "FIRMWARE", "BATTERY")
    )

    if "microsoft" in prov_low and third_party_hw and is_inbox_driver:
        return (
            "Puede actualizar (Genérico Win)",
            "updatable",
            "updatable",
            f"Hardware de {detected_vendor} usando driver genérico de Windows (v{ver_clean}, {date_str}). "
            "Habilita actualizaciones opcionales o descárgalo desde el Catálogo.",
        )

    if "microsoft" in prov_low and (is_win_core_date or is_win_build_ver or inf_low in core_infs):
        return (
            "NO ACTUALIZAR (Base OS)",
            "do_not_update",
            "do_not_update",
            f"Controlador nativo del núcleo de Windows (v{ver_clean}, {date_str}). No se debe actualizar manualmente.",
        )

    if cls_up in ("PROCESSOR", "VOLUME", "SOFTWAREDEVICE", "FIRMWARE", "BATTERY"):
        return (
            "NO ACTUALIZAR (Sistema)",
            "do_not_update",
            "do_not_update",
            f"Componente crítico/base de clase {cls_up} (v{ver_clean}). No se debe actualizar manualmente.",
        )

    if is_virtual_device(hardware_id, dev_id_hint=device_name):
        return (
            "VIRTUAL (su programa)",
            "virtual",
            "virtual",
            f"Dispositivo virtual de {detected_vendor} (v{ver_clean}, {date_str}). "
            "Lo gestiona el programa que lo instaló.",
        )

    years_old = 0.0
    drv_year = ""
    if date_str:
        drv_date = parse_any_date(date_str)
        if drv_date:
            years_old = (datetime.now() - drv_date).days / 365.25
            drv_year = str(drv_date.year)

    if "microsoft" not in prov_low or ven_low not in ("microsoft", "desconocido"):
        if years_old >= min_years_threshold:
            return (
                f"Puede actualizar ({drv_year})" if drv_year else "Puede actualizar",
                "updatable",
                "updatable",
                f"Controlador de {detected_vendor} (v{ver_clean}, {date_str}). "
                f"Tiene {years_old:.1f} año(s) (umbral: {min_years_threshold:g} años); admite actualización opcional.",
            )
        else:
            return (
                "AL DÍA (Reciente)",
                "ok",
                "ok",
                f"Controlador reciente de {detected_vendor} (v{ver_clean}, {date_str}).",
            )

    if years_old >= max(min_years_threshold, 4.0):
        return (
            f"Puede actualizar ({drv_year})",
            "updatable",
            "updatable",
            f"Controlador genérico de {date_str} (+{int(years_old)} años). Puedes buscar paquete del fabricante.",
        )

    return ("OK / Instalado", "ok", "ok", "Controlador instalado y al día.")


# ---------------------------------------------------------------------------
# Descarga de drivers y gestión de Windows Update (Actualizaciones Opcionales)
# ---------------------------------------------------------------------------
CATALOG_URL = "https://www.catalog.update.microsoft.com"
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
}


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def safe_name(text: str, maxlen: int = 60) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\s]+', "_", text or "").strip("._")
    return cleaned[:maxlen] or "driver"


def _strip_tags(raw: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", raw or ""))).strip()


def _http_request(url: str, data: bytes | None = None, timeout: int = 30) -> str:
    headers = dict(HTTP_HEADERS)
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def catalog_search(query: str) -> list[dict]:
    page = _http_request(f"{CATALOG_URL}/Search.aspx?q={urllib.parse.quote(query)}")
    results = []
    for m in re.finditer(r'<tr id="([0-9a-fA-F-]{36})_R\d+"[^>]*>(.*?)</tr>', page, re.S):
        uid, row = m.groups()
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 6:
            continue

        size_txt = ""
        if len(cells) > 6:
            size_m = re.search(r"<span[^>]*_size[^>]*>(.*?)</span>", cells[6], re.S)
            size_txt = _strip_tags(size_m.group(1)) if size_m else _strip_tags(cells[6])

        date_txt = _strip_tags(cells[4])
        sort_date = parse_any_date(date_txt) or datetime.min

        results.append(
            {
                "id": uid,
                "title": _strip_tags(cells[1]),
                "products": _strip_tags(cells[2]),
                "classification": _strip_tags(cells[3]),
                "date": date_txt,
                "version": _strip_tags(cells[5]),
                "size": size_txt,
                "_sort": sort_date,
            }
        )
    results.sort(key=lambda r: (r["_sort"], parse_version_tuple(r["version"])), reverse=True)
    return results


def catalog_download_urls(update_id: str) -> list[str]:
    payload = json.dumps([{"size": 0, "languages": "", "uidInfo": update_id, "updateID": update_id}])
    body = urllib.parse.urlencode({"updateIDs": payload}).encode("utf-8")
    page = _http_request(f"{CATALOG_URL}/DownloadDialog.aspx", data=body)
    urls = re.findall(r"downloadInformation\[\d+\]\.files\[\d+\]\.url\s*=\s*'([^']+)'", page)
    return list(dict.fromkeys(urls))


def download_file(url: str, dest: Path, progress_cb=None, cancel_event: threading.Event | None = None) -> Path:
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Descarga cancelada.")
            chunk = resp.read(64 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if progress_cb:
                progress_cb(done, total)
    return dest


def run_hidden(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=timeout,
    )


def get_wu_driver_policy_status() -> tuple[bool, str]:
    """Verifica en el Registro si Windows Update tiene bloqueada la búsqueda de drivers."""
    if os.name != "nt":
        return True, "Solo disponible en Windows"
    ps = (
        "$p1 = (Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate' "
        "-Name 'ExcludeWUDriversInQualityUpdate' -ErrorAction SilentlyContinue).ExcludeWUDriversInQualityUpdate; "
        "$p2 = (Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching' "
        "-Name 'SearchOrderConfig' -ErrorAction SilentlyContinue).SearchOrderConfig; "
        "Write-Output \"$p1|$p2\""
    )
    proc = run_hidden(["powershell", "-NoProfile", "-Command", ps], timeout=15)
    out = proc.stdout.strip()
    parts = out.split("|")
    excl = parts[0].strip() if len(parts) > 0 else ""
    search_cfg = parts[1].strip() if len(parts) > 1 else ""
    if excl == "1" or search_cfg == "0":
        return False, "Desactivado por política/registro (ExcludeWUDrivers=1 o SearchOrderConfig=0)"
    return True, "Habilitado en Windows Update"


def set_wu_driver_policy(enable: bool) -> tuple[bool, str]:
    """Reactiva o desactiva la descarga de drivers opcionales en Windows Update."""
    if not is_admin():
        return False, "Se requieren permisos de Administrador para modificar la política de Windows Update."
    excl_val = 0 if enable else 1
    search_val = 1 if enable else 0
    ps = (
        "New-Item -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate' -Force | Out-Null; "
        f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate' -Name 'ExcludeWUDriversInQualityUpdate' -Type DWord -Value {excl_val}; "
        "New-Item -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching' -Force | Out-Null; "
        f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching' -Name 'SearchOrderConfig' -Type DWord -Value {search_val}; "
        "Write-Output 'OK'"
    )
    proc = run_hidden(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], timeout=20)
    if proc.returncode == 0 and "OK" in proc.stdout:
        return True, (
            "Actualizaciones de drivers reactivadas en Windows Update."
            if enable
            else "Descarga automática de drivers desactivada."
        )
    return False, (proc.stderr or proc.stdout).strip()


class WindowsOptionalUpdatesDialog(tk.Toplevel):
    """Gestiona la reactivación de actualizaciones opcionales en WU y busca drivers pendientes por fecha/versión."""

    def __init__(self, parent: tk.Tk, installed_drivers: list[dict], on_installed_callback=None):
        super().__init__(parent)
        self.installed_drivers = installed_drivers
        self.on_installed_callback = on_installed_callback
        self.title("Actualizaciones Opcionales de Windows Update (Por Fecha / Versión)")
        self.geometry("980x560")
        self.minsize(820, 480)
        self.transient(parent)

        self.wu_updates: list[dict] = []
        self.busy = False
        self.policy_status_var = tk.StringVar(value="Verificando configuración de Windows Update...")
        self.status_var = tk.StringVar(value="Listo para consultar actualizaciones opcionales.")
        self.only_newer_var = tk.BooleanVar(value=True)

        self._build()
        self._refresh_policy_label()

    def _build(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        pol_box = ttk.LabelFrame(frm, text="Control de Actualizaciones Opcionales en Windows Update", padding=8)
        pol_box.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(pol_box, textvariable=self.policy_status_var, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 6))

        pol_btns = ttk.Frame(pol_box)
        pol_btns.pack(fill=tk.X)
        ttk.Button(
            pol_btns,
            text="✔ Reactivar Drivers Opcionales en Windows Update",
            command=lambda: self._toggle_policy(True),
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            pol_btns,
            text="✖ Desactivar Drivers en Windows Update",
            command=lambda: self._toggle_policy(False),
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            pol_btns,
            text="Abrir Actualizaciones Opcionales (Configuración)",
            command=self._open_wu_optional_settings,
        ).pack(side=tk.RIGHT)

        scan_bar = ttk.Frame(frm)
        scan_bar.pack(fill=tk.X, pady=(0, 6))
        self.btn_scan_wu = ttk.Button(
            scan_bar,
            text="🔍 Buscar Drivers Opcionales en Windows Update (Online)",
            command=self._scan_wu_optional,
        )
        self.btn_scan_wu.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Checkbutton(
            scan_bar,
            text="Mostrar solo si supera fecha o versión instalada",
            variable=self.only_newer_var,
            command=self._render_table,
        ).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(scan_bar, mode="indeterminate", length=140)
        self.progress.pack(side=tk.RIGHT)

        cols = ("title", "driver_ver", "driver_date", "installed_info", "comparison", "size")
        table = ttk.Frame(frm)
        table.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(table, columns=cols, show="headings", selectmode="extended")
        self.tree.tag_configure("newer", background="#D5F5E3", foreground="#145A32")
        self.tree.tag_configure("same", background="#FFFFFF", foreground="#2C3E50")

        for col, (title, width) in {
            "title": ("Actualización Opcional (Windows Update)", 310),
            "driver_ver": ("Versión WU", 105),
            "driver_date": ("Fecha WU", 90),
            "installed_info": ("Instalado en PC", 175),
            "comparison": ("Evaluación Fecha/Versión", 160),
            "size": ("Tamaño", 75),
        }.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, minwidth=60, anchor=tk.W)

        ysb = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)

        bottom = ttk.Frame(frm)
        bottom.pack(fill=tk.X, pady=(8, 0))
        self.btn_install_wu = ttk.Button(
            bottom,
            text="⬇ Instalar Seleccionados desde Windows Update",
            command=self._install_selected_wu,
            state=tk.DISABLED,
        )
        self.btn_install_wu.pack(side=tk.LEFT)
        ttk.Button(bottom, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT)

        ttk.Label(frm, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(6, 3)).pack(
            fill=tk.X, pady=(6, 0)
        )

    def _refresh_policy_label(self):
        enabled, desc = get_wu_driver_policy_status()
        prefix = "Estado actual: ✅ " if enabled else "Estado actual: ⛔ "
        self.policy_status_var.set(prefix + desc)

    def _toggle_policy(self, enable: bool):
        ok, msg = set_wu_driver_policy(enable)
        self._refresh_policy_label()
        if ok:
            messagebox.showinfo("Windows Update", msg, parent=self)
        else:
            messagebox.showwarning("Permisos requeridos", msg, parent=self)

    def _open_wu_optional_settings(self):
        try:
            os.startfile("ms-settings:windowsupdate-optionalupdates")
        except Exception:
            webbrowser.open("ms-settings:windowsupdate")

    def _match_installed(self, hwid: str, title: str) -> dict | None:
        clean_target = extract_clean_hwid(hwid).upper()
        if clean_target:
            for d in self.installed_drivers:
                if clean_target in (d.get("hardware_id") or "").upper():
                    return d
        title_low = (title or "").lower()
        for d in self.installed_drivers:
            dev_low = (d.get("device") or "").lower()
            if len(dev_low) > 6 and dev_low in title_low:
                return d
        return None

    def _scan_wu_optional(self):
        if self.busy:
            return
        self.busy = True
        self.btn_scan_wu.configure(state=tk.DISABLED)
        self.btn_install_wu.configure(state=tk.DISABLED)
        self.progress.start(10)
        self.status_var.set("Consultando servidor de Windows Update (puede tardar 15-40 segundos)...")

        def worker():
            ps = (
                "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                "$session = New-Object -ComObject Microsoft.Update.Session; "
                "$searcher = $session.CreateUpdateSearcher(); "
                "$res = $searcher.Search(\"IsInstalled=0 and Type='Driver'\"); "
                "$list = @(); "
                "for ($i=0; $i -lt $res.Updates.Count; $i++) { "
                "  $u = $res.Updates.Item($i); "
                "  $dStr = if ($u.DriverVerDate) { $u.DriverVerDate.ToString('yyyy-MM-dd') } else { '' }; "
                "  $list += [PSCustomObject]@{ "
                "    Index=$i; Title=$u.Title; DriverModel=$u.DriverModel; "
                "    DriverManufacturer=$u.DriverManufacturer; DriverHardwareID=$u.DriverHardwareID; "
                "    DriverVerDate=$dStr; MaxSize=$u.MaxDownloadSize "
                "  } "
                "} "
                "$list | ConvertTo-Json -Depth 3 -Compress"
            )
            try:
                proc = run_hidden(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], timeout=120)
                if proc.returncode != 0:
                    raise RuntimeError(proc.stderr.strip() or "Error al consultar Windows Update.")
                raw = proc.stdout.strip()
                items = json.loads(raw) if raw else []
                if isinstance(items, dict):
                    items = [items]
                self.after(0, lambda: self._on_wu_scan_done(items, None))
            except Exception as exc:
                err = str(exc)
                self.after(0, lambda: self._on_wu_scan_done([], err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_wu_scan_done(self, items: list[dict], error: str | None):
        self.progress.stop()
        self.busy = False
        self.btn_scan_wu.configure(state=tk.NORMAL)
        if error:
            self.status_var.set("Error al consultar Windows Update.")
            messagebox.showerror("Error Windows Update", error, parent=self)
            return

        enriched = []
        for it in items:
            title = it.get("Title") or ""
            hwid = it.get("DriverHardwareID") or ""
            wu_date = it.get("DriverVerDate") or ""
            ver_match = re.search(r"(\d+\.\d+\.\d+(?:\.\d+)?)", title)
            wu_ver = ver_match.group(1) if ver_match else ""
            size_mb = f"{(it.get('MaxSize') or 0) / 1048576:.1f} MB"

            inst = self._match_installed(hwid, title)
            if inst:
                inst_str = f"v{inst['version'] or '?'} ({inst['date'] or '?'})"
                is_new, reason = is_newer_candidate(inst["version"], inst["date"], wu_ver, wu_date)
            else:
                inst_str = "No instalado / Nuevo"
                is_new, reason = True, "Driver faltante o nuevo"

            enriched.append(
                {
                    "index": it.get("Index", 0),
                    "title": title,
                    "wu_ver": wu_ver or "N/A",
                    "wu_date": wu_date or "N/A",
                    "inst_str": inst_str,
                    "is_newer": is_new,
                    "reason": reason,
                    "size": size_mb,
                }
            )

        self.wu_updates = enriched
        self._render_table()

    def _render_table(self):
        self.tree.delete(*self.tree.get_children())
        shown = 0
        for u in self.wu_updates:
            if self.only_newer_var.get() and not u["is_newer"]:
                continue
            tag = "newer" if u["is_newer"] else "same"
            self.tree.insert(
                "",
                tk.END,
                iid=str(u["index"]),
                values=(u["title"], u["wu_ver"], u["wu_date"], u["inst_str"], u["reason"], u["size"]),
                tags=(tag,),
            )
            shown += 1

        self.btn_install_wu.configure(state=tk.NORMAL if shown > 0 else tk.DISABLED)
        self.status_var.set(f"Actualizaciones opcionales encontradas: {len(self.wu_updates)}  |  Mostrando: {shown}")

    def _install_selected_wu(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Selecciona al menos una actualización de la lista.", parent=self)
            return
        if not is_admin():
            messagebox.showwarning(
                "Administrador requerido",
                "Reinicia la aplicación como Administrador para descargar e instalar desde Windows Update.",
                parent=self,
            )
            return
        indices = ",".join(sel)
        self.busy = True
        self.btn_install_wu.configure(state=tk.DISABLED)
        self.progress.start(10)
        self.status_var.set("Descargando e instalando actualizaciones opcionales seleccionadas...")

        def worker():
            ps = (
                "$session = New-Object -ComObject Microsoft.Update.Session; "
                "$searcher = $session.CreateUpdateSearcher(); "
                "$res = $searcher.Search(\"IsInstalled=0 and Type='Driver'\"); "
                "$toInstall = New-Object -ComObject Microsoft.Update.UpdateColl; "
                f"foreach ($idx in @({indices})) {{ if ($idx -lt $res.Updates.Count) {{ $toInstall.Add($res.Updates.Item($idx)) | Out-Null }} }}; "
                "$dl = $session.CreateUpdateDownloader(); $dl.Updates = $toInstall; $dl.Download() | Out-Null; "
                "$inst = $session.CreateUpdateInstaller(); $inst.Updates = $toInstall; $ir = $inst.Install(); "
                "Write-Output \"$($ir.ResultCode)|$($ir.RebootRequired)\""
            )
            try:
                proc = run_hidden(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], timeout=600)
                if proc.returncode != 0:
                    raise RuntimeError(proc.stderr.strip() or "Falló la instalación de Windows Update.")
                self.after(0, lambda: self._on_wu_install_done(proc.stdout.strip(), None))
            except Exception as exc:
                err = str(exc)
                self.after(0, lambda: self._on_wu_install_done("", err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_wu_install_done(self, result: str, error: str | None):
        self.progress.stop()
        self.busy = False
        self.btn_install_wu.configure(state=tk.NORMAL)
        if error:
            self.status_var.set("Error al instalar desde Windows Update.")
            messagebox.showerror("Error", error, parent=self)
            return

        code_map = {
            "2": "Instalación exitosa",
            "3": "Completado con advertencias",
            "4": "Error en la instalación",
            "5": "Instalación cancelada",
        }
        parts = result.split("|")
        status_txt = code_map.get(parts[0].strip(), f"Código {parts[0]}")
        reboot_txt = "Sí (reinicia el equipo)" if len(parts) > 1 and parts[1].strip().lower() == "true" else "No"

        self.status_var.set(f"{status_txt} | Requiere reinicio: {reboot_txt}")
        messagebox.showinfo(
            "Windows Update",
            f"Estado: {status_txt}\n¿Requiere reinicio?: {reboot_txt}",
            parent=self,
        )
        if self.on_installed_callback:
            self.on_installed_callback()
        self._scan_wu_optional()


class DriverDownloadDialog(tk.Toplevel):
    """Ventana para buscar, descargar, extraer e instalar un driver desde el Catálogo de Microsoft."""

    def __init__(self, parent: tk.Tk, drv: dict):
        super().__init__(parent)
        self.drv = drv
        self.title(f"Descargar driver — {drv['device']}")
        self.geometry("1040x580")
        self.minsize(840, 480)
        self.transient(parent)

        self.results: list[dict] = []
        self.busy = False
        self.cancel_event = threading.Event()

        clean_id = extract_clean_hwid(drv["hardware_id"])
        self.query_var = tk.StringVar(value=clean_id or drv["device"])
        default_dir = Path.home() / "Downloads" / "Drivers" / safe_name(f"{drv['detected_vendor']}_{drv['device']}")
        self.dest_var = tk.StringVar(value=str(default_dir))
        self.only_newer_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Presiona 'Buscar' para consultar el Catálogo de Microsoft Update.")

        self._build()
        self._search()

    def _build(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text=self.drv["device"], font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(
            frm,
            text=(
                f"Fabricante: {self.drv['detected_vendor']}   |   "
                f"Instalado: v{self.drv['version'] or 'N/A'} ({self.drv['date'] or 'N/A'})   |   "
                f"ID: {self.drv['hardware_id'] or 'No reportado'}"
            ),
        ).pack(anchor=tk.W, pady=(0, 8))

        search_row = ttk.Frame(frm)
        search_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(search_row, text="Buscar en catálogo:").pack(side=tk.LEFT, padx=(0, 4))
        entry = ttk.Entry(search_row, textvariable=self.query_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        entry.bind("<Return>", lambda _e: self._search())
        self.btn_search = ttk.Button(search_row, text="Buscar", command=self._search)
        self.btn_search.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Checkbutton(
            search_row,
            text="Solo más nuevos (fecha/versión)",
            variable=self.only_newer_var,
            command=self._populate_tree,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(search_row, text="Abrir en navegador", command=self._open_in_browser).pack(side=tk.LEFT)

        cols = ("title", "products", "date", "version", "compare", "size")
        table = ttk.Frame(frm)
        table.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(table, columns=cols, show="headings", selectmode="browse")
        self.tree.tag_configure("newer", background="#D5F5E3", foreground="#145A32")
        self.tree.tag_configure("older", background="#FFFFFF", foreground="#2C3E50")

        for col, (title, width) in {
            "title": ("Título", 340),
            "products": ("Sistemas compatibles", 190),
            "date": ("Fecha", 80),
            "version": ("Versión", 105),
            "compare": ("Vs. Instalado", 150),
            "size": ("Tamaño", 75),
        }.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, minwidth=60, anchor=tk.W)
        ysb = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)

        dest_row = ttk.Frame(frm)
        dest_row.pack(fill=tk.X, pady=(8, 4))
        ttk.Label(dest_row, text="Guardar en:").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Entry(dest_row, textvariable=self.dest_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(dest_row, text="Cambiar...", command=self._choose_dir).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(frm, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X, pady=(4, 2))
        ttk.Label(frm, textvariable=self.status_var, anchor=tk.W).pack(fill=tk.X)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=(8, 0))
        self.btn_dl = ttk.Button(btns, text="⬇ Descargar (.cab)", command=lambda: self._start("download"))
        self.btn_dl.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_ext = ttk.Button(btns, text="⬇ Descargar y extraer", command=lambda: self._start("extract"))
        self.btn_ext.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_inst = ttk.Button(btns, text="⬇ Descargar e instalar (admin)", command=lambda: self._start("install"))
        self.btn_inst.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="Cerrar", command=self._close).pack(side=tk.RIGHT)
        self.btn_cancel = ttk.Button(btns, text="Cancelar descarga", command=self.cancel_event.set, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.RIGHT, padx=(0, 6))

        self.tree.bind("<Double-1>", lambda _e: self._start("download"))
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _ui(self, fn, *args):
        try:
            self.after(0, lambda: fn(*args))
        except (tk.TclError, RuntimeError):
            pass

    def _set_status(self, text: str):
        self.status_var.set(text)

    def _set_busy(self, busy: bool):
        self.busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for b in (self.btn_dl, self.btn_ext, self.btn_inst, self.btn_search):
            b.configure(state=state)
        self.btn_cancel.configure(state=tk.NORMAL if busy else tk.DISABLED)

    def _set_progress(self, done: int, total: int):
        if total:
            self.progress.configure(mode="determinate")
            self.progress["value"] = done * 100 / total
            self.status_var.set(f"Descargando... {done / 1048576:.1f} / {total / 1048576:.1f} MB")
        else:
            self.status_var.set(f"Descargando... {done / 1048576:.1f} MB")

    def _choose_dir(self):
        folder = filedialog.askdirectory(title="Carpeta de destino", parent=self)
        if folder:
            self.dest_var.set(folder)

    def _open_in_browser(self):
        webbrowser.open(f"{CATALOG_URL}/Search.aspx?q={urllib.parse.quote(self.query_var.get().strip())}")

    def _close(self):
        self.cancel_event.set()
        self.destroy()

    def _search(self):
        if self.busy:
            return
        query = self.query_var.get().strip()
        if not query:
            return
        self._set_busy(True)
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)
        self.status_var.set(f"Buscando '{query}' en el Catálogo de Microsoft Update...")
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query: str):
        try:
            results = catalog_search(query)
            if not results and query == extract_clean_hwid(self.drv["hardware_id"]):
                for alt in self.drv.get("hardware_ids", [])[:4]:
                    results = catalog_search(alt)
                    if results:
                        break
            self._ui(self._on_search_done, results, None)
        except Exception as exc:
            self._ui(self._on_search_done, [], str(exc))

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        first_id = None
        shown = 0
        for r in self.results:
            is_new, reason = is_newer_candidate(
                self.drv.get("version", ""), self.drv.get("date", ""), r["version"], r["date"]
            )
            if self.only_newer_var.get() and not is_new:
                continue
            tag = "newer" if is_new else "older"
            self.tree.insert(
                "",
                tk.END,
                iid=r["id"],
                values=(r["title"], r["products"], r["date"], r["version"], reason, r["size"]),
                tags=(tag,),
            )
            if first_id is None:
                first_id = r["id"]
            shown += 1
        if first_id:
            self.tree.selection_set(first_id)
        return shown

    def _on_search_done(self, results: list[dict], error: str | None):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = 0
        self._set_busy(False)
        self.results = results
        shown = self._populate_tree()
        if error:
            self.status_var.set(f"No se pudo consultar el catálogo: {error}. Prueba 'Abrir en navegador'.")
        elif results:
            self.status_var.set(f"{len(results)} resultado(s) ({shown} mostrados). En verde los más recientes.")
        else:
            self.status_var.set("Sin resultados. Edita la búsqueda o usa 'Abrir en navegador'.")

    def _start(self, mode: str):
        if self.busy:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecciona un driver", "Elige primero un resultado de la lista.", parent=self)
            return
        if mode == "install":
            if not is_admin():
                messagebox.showwarning(
                    "Se requieren permisos de administrador",
                    "Para instalar drivers, ejecuta la app como administrador "
                    "(botón 'Admin' de la ventana principal).",
                    parent=self,
                )
                return
            if not messagebox.askyesno(
                "Confirmar instalación",
                "Se instalará el driver descargado en el sistema.\n\n"
                "Recomendado: crear un punto de restauración antes.\n¿Continuar?",
                parent=self,
            ):
                return
        update_id = sel[0]
        dest = Path(self.dest_var.get().strip() or ".")
        self.cancel_event.clear()
        self._set_busy(True)
        self.progress["value"] = 0
        self.status_var.set("Obteniendo enlace de descarga...")
        threading.Thread(target=self._download_worker, args=(update_id, dest, mode), daemon=True).start()

    def _download_worker(self, update_id: str, dest: Path, mode: str):
        try:
            dest.mkdir(parents=True, exist_ok=True)
            urls = catalog_download_urls(update_id)
            if not urls:
                raise RuntimeError("El catálogo no devolvió enlaces de descarga para este paquete.")

            files: list[Path] = []
            for url in urls:
                name = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name or f"{update_id}.cab"
                files.append(download_file(url, dest / name, lambda d, t: self._ui(self._set_progress, d, t), self.cancel_event))

            extracted: list[Path] = []
            if mode in ("extract", "install"):
                for f in files:
                    if f.suffix.lower() != ".cab":
                        continue
                    out_dir = dest / f.stem
                    out_dir.mkdir(exist_ok=True)
                    self._ui(self._set_status, f"Extrayendo {f.name}...")
                    proc = run_hidden(["expand", "-F:*", str(f), str(out_dir)])
                    if proc.returncode != 0:
                        raise RuntimeError(f"Error al extraer {f.name}: {(proc.stdout + proc.stderr).strip()}")
                    extracted.append(out_dir)

            install_msg = ""
            if mode == "install":
                if not extracted:
                    raise RuntimeError("No hay archivos .cab para instalar (el paquete no es un CAB de drivers).")
                for out_dir in extracted:
                    self._ui(self._set_status, f"Instalando drivers de {out_dir.name}...")
                    proc = run_hidden(["pnputil", "/add-driver", str(out_dir / "*.inf"), "/subdirs", "/install"])
                    out = (proc.stdout + proc.stderr).strip()
                    if proc.returncode not in (0, 3010):
                        raise RuntimeError(f"pnputil devolvió código {proc.returncode}:\n{out[-800:]}")
                    install_msg += f"\n{out[-500:]}"
                    if proc.returncode == 3010:
                        install_msg += "\n(Se requiere reiniciar el equipo.)"

            self._ui(self._on_download_done, dest, mode, len(files), install_msg, None)
        except Exception as exc:
            self._ui(self._on_download_done, dest, mode, 0, "", str(exc))

    def _on_download_done(self, dest: Path, mode: str, n_files: int, install_msg: str, error: str | None):
        self._set_busy(False)
        if error:
            self.progress["value"] = 0
            self.status_var.set(f"Error: {error}")
            messagebox.showerror("Error", error, parent=self)
            return
        self.progress["value"] = 100
        self.status_var.set(f"Listo: {n_files} archivo(s) en {dest}")
        if mode == "install":
            messagebox.showinfo("Instalación completada", f"Driver instalado.{install_msg}", parent=self)
        else:
            msg = f"Se descargaron {n_files} archivo(s) en:\n{dest}"
            if mode == "extract":
                msg += "\n\nLos .inf quedaron extraídos; puedes instalarlos desde el Administrador de dispositivos."
            messagebox.showinfo("Descarga completada", msg, parent=self)
        try:
            os.startfile(str(dest))
        except Exception:
            pass


class DriverScannerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Escáner de Hardware y Buscador de Drivers (Windows)" + (" — Administrador" if is_admin() else ""))
        self.root.geometry("1280x750")
        self.root.minsize(1040, 620)

        self.all_drivers: list[dict] = []
        self.filtered_drivers: list[dict] = []
        self.item_map: dict[str, dict] = {}
        self.selected_driver: dict | None = None

        self.is_scanning = False
        self._filter_after_id = None

        self.search_var = tk.StringVar()
        self.category_filter = tk.StringVar(value="ALL")
        self.filter_third_party = tk.BooleanVar(value=False)
        self.age_threshold_var = tk.StringVar(value="3 años")
        self.status_var = tk.StringVar(
            value="Listo. Presiona '1. Escanear Hardware y Drivers' para analizar todos los controladores."
        )

        self.detail_status = tk.StringVar(value="-")
        self.detail_hw_type = tk.StringVar(value="-")
        self.detail_device = tk.StringVar(value="Haz clic en cualquier fila de la tabla para activar la búsqueda")
        self.detail_vendor = tk.StringVar(value="-")
        self.detail_hwid = tk.StringVar(value="-")
        self.detail_meta = tk.StringVar(value="-")

        self.search_var.trace_add("write", lambda *_: self._schedule_filter())

        self._build_ui()

    def _get_min_years(self) -> float:
        mapping = {"1 año": 1.0, "2 años": 2.0, "3 años": 3.0, "5 años": 5.0}
        return mapping.get(self.age_threshold_var.get(), 3.0)

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Barra superior de acciones y leyenda de colores ---
        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 8))

        self.btn_scan = ttk.Button(
            top_bar, text="1. Escanear Hardware y Drivers", command=self._start_scan
        )
        self.btn_scan.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_wu_optional = ttk.Button(
            top_bar, text="Actualizaciones Opcionales (WU)", command=self._open_wu_optional_dialog
        )
        self.btn_wu_optional.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_export_csv = ttk.Button(
            top_bar, text="Exportar CSV", command=self._export_csv, state=tk.DISABLED
        )
        self.btn_export_csv.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_export_txt = ttk.Button(
            top_bar, text="Exportar TXT", command=self._export_txt, state=tk.DISABLED
        )
        self.btn_export_txt.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_backup = ttk.Button(top_bar, text="Respaldar", command=self._backup_drivers)
        self.btn_backup.pack(side=tk.LEFT, padx=(0, 4))

        if not is_admin():
            ttk.Button(top_bar, text="Admin", command=self._relaunch_as_admin).pack(side=tk.LEFT, padx=(0, 8))

        # Leyenda actualizada
        legend_frame = ttk.Frame(top_bar)
        legend_frame.pack(side=tk.RIGHT)

        tk.Label(
            legend_frame, text=" ■ Necesita actualizarse ", bg="#82E0AA", fg="#0B5345", font=("Segoe UI", 8, "bold"), padx=4
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(
            legend_frame, text=" ■ Puede actualizar ", bg="#D5F5E3", fg="#145A32", font=("Segoe UI", 8, "bold"), padx=4
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(
            legend_frame, text=" ■ No Actualizar ", bg="#FADBD8", fg="#922B21", font=("Segoe UI", 8, "bold"), padx=4
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(
            legend_frame, text=" ■ Virtual ", bg="#D6EAF8", fg="#1B4F72", font=("Segoe UI", 8, "bold"), padx=4
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(
            legend_frame, text=" ■ Al Día ", bg="#F2F4F4", fg="#2C3E50", font=("Segoe UI", 8, "bold"), padx=4
        ).pack(side=tk.LEFT, padx=2)

        # --- Segunda barra: Filtros y búsqueda ---
        filter_bar = ttk.Frame(main_frame)
        filter_bar.pack(fill=tk.X, pady=(0, 8))

        ttk.Radiobutton(
            filter_bar, text="Todos", value="ALL", variable=self.category_filter, command=self._apply_filters
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(
            filter_bar, text="Necesita actualizarse", value="missing", variable=self.category_filter, command=self._apply_filters
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(
            filter_bar, text="Puede actualizar", value="updatable", variable=self.category_filter, command=self._apply_filters
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(
            filter_bar, text="No Actualizar", value="do_not_update", variable=self.category_filter, command=self._apply_filters
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(
            filter_bar, text="Virtual", value="virtual", variable=self.category_filter, command=self._apply_filters
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Checkbutton(
            filter_bar,
            text="Solo terceros",
            variable=self.filter_third_party,
            command=self._apply_filters,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(filter_bar, text="Opcional si >").pack(side=tk.LEFT, padx=(0, 3))
        age_combo = ttk.Combobox(
            filter_bar,
            textvariable=self.age_threshold_var,
            values=("1 año", "2 años", "3 años", "5 años"),
            state="readonly",
            width=7,
        )
        age_combo.pack(side=tk.LEFT, padx=(0, 8))
        age_combo.bind("<<ComboboxSelected>>", lambda _e: self._reclassify_drivers())

        ttk.Label(filter_bar, text="Buscar:").pack(side=tk.LEFT, padx=(0, 4))
        search_entry = ttk.Entry(filter_bar, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.progress = ttk.Progressbar(filter_bar, mode="indeterminate", length=110)
        self.progress.pack(side=tk.RIGHT)

        # --- Tabla de resultados (Treeview) ---
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("status", "hw_type", "device", "provider", "version", "date", "inf")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            takefocus=True,
        )

        self.tree.tag_configure("missing", background="#82E0AA", foreground="#0B5345")
        self.tree.tag_configure("updatable", background="#D5F5E3", foreground="#145A32")
        self.tree.tag_configure("do_not_update", background="#FADBD8", foreground="#922B21")
        self.tree.tag_configure("virtual", background="#D6EAF8", foreground="#1B4F72")
        self.tree.tag_configure("ok", background="#FFFFFF", foreground="#1C2833")

        headers = {
            "status": ("Estado / Acción", 185),
            "hw_type": ("Tipo de Hardware", 195),
            "device": ("Dispositivo / Controlador", 260),
            "provider": ("Fabricante Detectado", 165),
            "version": ("Versión", 110),
            "date": ("Fecha", 85),
            "inf": ("Archivo INF", 100),
        }

        for col, (title, width) in headers.items():
            self.tree.heading(
                col, text=title, command=lambda c=col: self._sort_by_column(c, False)
            )
            self.tree.column(col, width=width, minwidth=70, anchor=tk.W, stretch=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self.tree.bind("<Double-1>", lambda _e: self._open_download_dialog())

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # --- Panel inferior ---
        detail_box = ttk.LabelFrame(
            main_frame, text="Diagnóstico del Controlador y Búsqueda en Internet / Fabricantes", padding=8
        )
        detail_box.pack(fill=tk.X, pady=(8, 0))
        detail_box.columnconfigure(0, weight=1)
        detail_box.columnconfigure(1, weight=0)

        info_container = ttk.Frame(detail_box)
        info_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        row0 = ttk.Frame(info_container)
        row0.pack(fill=tk.X, pady=1)
        ttk.Label(row0, text="Diagnóstico:", width=16, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(row0, textvariable=self.detail_status).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row1 = ttk.Frame(info_container)
        row1.pack(fill=tk.X, pady=1)
        ttk.Label(row1, text="Tipo de Hardware:", width=16, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(row1, textvariable=self.detail_hw_type).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row2 = ttk.Frame(info_container)
        row2.pack(fill=tk.X, pady=1)
        ttk.Label(row2, text="Dispositivo:", width=16, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(row2, textvariable=self.detail_device).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row_ven = ttk.Frame(info_container)
        row_ven.pack(fill=tk.X, pady=1)
        ttk.Label(row_ven, text="Fabricante Real:", width=16, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(row_ven, textvariable=self.detail_vendor).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row3 = ttk.Frame(info_container)
        row3.pack(fill=tk.X, pady=1)
        ttk.Label(row3, text="ID de Hardware:", width=16, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(row3, textvariable=self.detail_hwid).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row4 = ttk.Frame(info_container)
        row4.pack(fill=tk.X, pady=1)
        ttk.Label(row4, text="Datos Técnicos:", width=16, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(row4, textvariable=self.detail_meta).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Columna derecha de botones ---
        action_col = ttk.Frame(detail_box)
        action_col.grid(row=0, column=1, sticky="ns")

        self.btn_download = ttk.Button(
            action_col,
            text="⬇ DESCARGAR DRIVER (Catálogo Microsoft)",
            command=self._open_download_dialog,
            state=tk.DISABLED,
            width=38,
        )
        self.btn_download.pack(pady=(0, 8))

        self.btn_vendor_site = ttk.Button(
            action_col,
            text="1. Ir a Soporte del Fabricante",
            command=self._open_vendor_support,
            state=tk.DISABLED,
            width=38,
        )
        self.btn_vendor_site.pack(pady=(0, 4))

        self.btn_search_pkg = ttk.Button(
            action_col,
            text="2. Buscar Descarga del Driver en Web",
            command=self._search_driver_download,
            state=tk.DISABLED,
            width=38,
        )
        self.btn_search_pkg.pack(pady=(0, 4))

        self.btn_lookup_pci = ttk.Button(
            action_col,
            text="3. Identificar Chip en Base PCI/USB",
            command=self._lookup_chip_online,
            state=tk.DISABLED,
            width=38,
        )
        self.btn_lookup_pci.pack(pady=(0, 4))

        self.btn_copy_hwid = ttk.Button(
            action_col,
            text="4. Copiar ID Limpio al Portapapeles",
            command=self._copy_hwid,
            state=tk.DISABLED,
            width=38,
        )
        self.btn_copy_hwid.pack()

        # --- Barra de estado inferior ---
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(6, 3)
        )
        status_bar.pack(fill=tk.X, pady=(8, 0))

    def _reclassify_drivers(self):
        if not self.all_drivers:
            return
        min_years = self._get_min_years()
        for drv in self.all_drivers:
            status_lbl, tag, category, status_detail = evaluate_driver_classification(
                drv["device"],
                drv["provider"],
                drv["detected_vendor"],
                drv["version"],
                drv["date"],
                drv["inf"],
                drv["class"],
                drv.get("error_code", 0),
                drv["hardware_id"],
                min_years_threshold=min_years,
            )
            drv["status"] = status_lbl
            drv["tag"] = tag
            drv["category"] = category
            drv["status_detail"] = status_detail
        self._apply_filters()

    def _open_wu_optional_dialog(self):
        if os.name != "nt":
            messagebox.showinfo("Solo Windows", "Windows Update solo está disponible en Windows.")
            return
        WindowsOptionalUpdatesDialog(self.root, self.all_drivers, on_installed_callback=self._start_scan)

    def _on_row_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        drv = self.item_map.get(selection[0])
        if not drv:
            return

        self.selected_driver = drv
        clean_id = extract_clean_hwid(drv["hardware_id"])

        self.detail_status.set(f"{drv['status']} — {drv['status_detail']}")
        self.detail_hw_type.set(drv["hw_type"])
        self.detail_device.set(drv["device"])
        self.detail_vendor.set(drv["detected_vendor"])
        self.detail_hwid.set(
            f"{clean_id}   (Completo: {drv['hardware_id']})"
            if clean_id and clean_id != drv["hardware_id"]
            else (drv["hardware_id"] or "No reportado")
        )
        self.detail_meta.set(
            f"Clase: {drv['class'] or 'N/A'}  |  Versión: {drv['version'] or 'N/A'}  |  "
            f"Fecha: {drv['date'] or 'N/A'}  |  INF: {drv['inf'] or 'N/A'}"
        )

        self.btn_download.configure(state=tk.NORMAL)
        self.btn_vendor_site.configure(state=tk.NORMAL)
        self.btn_search_pkg.configure(state=tk.NORMAL)
        self.btn_lookup_pci.configure(state=tk.NORMAL)
        self.btn_copy_hwid.configure(state=tk.NORMAL)

    def _warn_if_do_not_update(self) -> bool:
        if self.selected_driver and self.selected_driver["category"] == "virtual":
            return messagebox.askyesno(
                "Dispositivo virtual",
                "Este NO es hardware físico: lo creó un programa instalado en tu PC, y su driver viene "
                "con ese programa. Windows Update y el Catálogo de Microsoft no lo tienen.\n\n"
                "Para actualizarlo, actualiza el programa que lo instaló.\n\n"
                "¿Aún así deseas buscarlo en internet?",
            )
        if self.selected_driver and self.selected_driver["category"] == "do_not_update":
            return messagebox.askyesno(
                "Controlador Base del Sistema",
                "Este controlador está marcado en ROJO como 'NO ACTUALIZAR' porque pertenece "
                "al núcleo base de Windows.\n\n¿Aún así deseas abrir la búsqueda en internet?",
            )
        return True

    def _open_download_dialog(self):
        if not self.selected_driver or not self._warn_if_do_not_update():
            return
        if os.name != "nt":
            messagebox.showinfo("Solo Windows", "La descarga/instalación de drivers solo funciona en Windows.")
            return
        DriverDownloadDialog(self.root, self.selected_driver)

    def _relaunch_as_admin(self):
        try:
            script = os.path.abspath(sys.argv[0])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
            if ret > 32:
                self.root.destroy()
            else:
                messagebox.showwarning("Permisos", "No se pudo reiniciar como administrador.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _backup_drivers(self):
        if os.name != "nt":
            messagebox.showinfo("Solo Windows", "El respaldo de drivers solo funciona en Windows.")
            return
        if not is_admin():
            messagebox.showwarning(
                "Se requieren permisos de administrador",
                "pnputil necesita permisos de administrador para exportar drivers.\n"
                "Usa el botón 'Admin'.",
            )
            return

        target = "*"
        sel = self.selected_driver
        if sel and sel["inf"].lower().startswith("oem"):
            ans = messagebox.askyesnocancel(
                "Respaldar drivers",
                f"¿Respaldar solo el driver seleccionado ({sel['device']})?\n\n"
                "Sí = solo el seleccionado\nNo = todos los drivers de terceros",
            )
            if ans is None:
                return
            target = sel["inf"] if ans else "*"
        elif not messagebox.askyesno("Respaldar drivers", "¿Respaldar TODOS los drivers de terceros instalados?"):
            return

        folder = filedialog.askdirectory(title="Carpeta donde guardar el respaldo")
        if not folder:
            return
        dest = Path(folder) / f"respaldo_drivers_{datetime.now().strftime('%Y%m%d_%H%M')}"
        dest.mkdir(parents=True, exist_ok=True)

        self.btn_backup.configure(state=tk.DISABLED)
        self.progress.start(10)
        self.status_var.set("Respaldando drivers (puede tardar varios minutos)...")

        def worker():
            try:
                proc = run_hidden(["pnputil", "/export-driver", target, str(dest)], timeout=1800)
                err = None if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-600:]
            except Exception as exc:
                err = str(exc)
            self.root.after(0, lambda: done(err))

        def done(err):
            self.progress.stop()
            self.btn_backup.configure(state=tk.NORMAL)
            if err:
                self.status_var.set("Error al respaldar drivers.")
                messagebox.showerror("Error al respaldar", err)
            else:
                self.status_var.set(f"Respaldo completado en: {dest}")
                messagebox.showinfo("Respaldo completado", f"Drivers guardados en:\n{dest}")
                try:
                    os.startfile(str(dest))
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _open_vendor_support(self):
        if not self.selected_driver or not self._warn_if_do_not_update():
            return
        vendor = self.selected_driver["detected_vendor"]
        vendor_url = self.selected_driver["vendor_url"]
        clean_id = extract_clean_hwid(self.selected_driver["hardware_id"])
        dev_name = self.selected_driver["device"]

        if vendor_url:
            if vendor_url.endswith("?q="):
                target = vendor_url + urllib.parse.quote(clean_id or dev_name)
            else:
                target = vendor_url
            webbrowser.open(target)
            self.status_var.set(f"Abriendo portal oficial de {vendor}...")
        else:
            query = f"{clean_id} {dev_name} official driver download".strip()
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            self.status_var.set(f"Buscando soporte oficial para: {query}")

    def _search_driver_download(self):
        if not self.selected_driver or not self._warn_if_do_not_update():
            return
        clean_id = extract_clean_hwid(self.selected_driver["hardware_id"])
        vendor = self.selected_driver["detected_vendor"]
        dev_name = self.selected_driver["device"]
        inf_name = self.selected_driver["inf"]

        useful_inf = inf_name if (inf_name and not inf_name.lower().startswith("oem")) else ""

        parts = []
        if vendor and vendor != "Desconocido":
            parts.append(vendor)
        if clean_id:
            parts.append(f'"{clean_id}"')
        parts.append(dev_name)
        if useful_inf:
            parts.append(useful_inf)
        parts.append("driver download Windows")

        query = " ".join(parts).strip()
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        self.status_var.set(f"Buscando paquete de driver: {query}")

    def _lookup_chip_online(self):
        if not self.selected_driver:
            return
        raw_id = self.selected_driver["hardware_id"].upper()
        m_pci = re.search(r"PCI\\VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})", raw_id)
        if m_pci:
            ven, dev = m_pci.group(1), m_pci.group(2)
            url = f"https://devicehunt.com/view/type/pci/vendor/{ven}/device/{dev}"
            webbrowser.open(url)
            self.status_var.set(f"Consultando chip PCI VEN_{ven} & DEV_{dev} en DeviceHunt...")
            return

        m_usb = re.search(r"USB\\VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", raw_id)
        if m_usb:
            vid, pid = m_usb.group(1), m_usb.group(2)
            url = f"https://devicehunt.com/view/type/usb/vendor/{vid}/device/{pid}"
            webbrowser.open(url)
            self.status_var.set(f"Consultando dispositivo USB VID_{vid} & PID_{pid} en DeviceHunt...")
            return

        clean_id = extract_clean_hwid(raw_id) or self.selected_driver["device"]
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(clean_id + ' hardware id driver')}")
        self.status_var.set(f"Buscando identificador en base web: {clean_id}")

    def _copy_hwid(self):
        if not self.selected_driver:
            return
        clean_id = extract_clean_hwid(self.selected_driver["hardware_id"]) or self.selected_driver["device"]
        self.root.clipboard_clear()
        self.root.clipboard_append(clean_id)
        self.status_var.set(f"ID limpio copiado al portapapeles: {clean_id}")

    def _schedule_filter(self):
        if self._filter_after_id is not None:
            self.root.after_cancel(self._filter_after_id)
        self._filter_after_id = self.root.after(180, self._apply_filters)

    def _start_scan(self):
        if self.is_scanning:
            return

        self.is_scanning = True
        self.btn_scan.configure(state=tk.DISABLED)
        self.btn_export_csv.configure(state=tk.DISABLED)
        self.btn_export_txt.configure(state=tk.DISABLED)
        self.status_var.set("Escaneando hardware, identificando fabricantes y clasificando versiones...")
        self.progress.start(10)

        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            drivers = self._query_windows_drivers()
            self.root.after(0, lambda: self._on_scan_success(drivers))
        except Exception as exc:
            err = str(exc)
            self.root.after(0, lambda: self._on_scan_error(err))

    def _query_windows_drivers(self) -> list[dict]:
        ps_script = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "$signed = Get-CimInstance Win32_PnPSignedDriver | Where-Object { $_.DeviceName -ne $null } | "
            "Select-Object DeviceName, DeviceID, DriverProviderName, DriverVersion, "
            "@{Name='DriverDateStr';Expression={if($_.DriverDate){$_.DriverDate.ToString('yyyy-MM-dd')}else{''}}}, "
            "InfName, DeviceClass, HardwareID; "
            "$errors = Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 } | "
            "Select-Object Name, DeviceID, Manufacturer, PNPClass, ConfigManagerErrorCode, HardwareID; "
            "@{signed=$signed; errors=$errors} | ConvertTo-Json -Depth 3 -Compress"
        )

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
            timeout=60,
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "No se pudo consultar el inventario PnP.")

        raw_json = proc.stdout.strip()
        if not raw_json:
            return []

        payload = json.loads(raw_json)
        signed_list = payload.get("signed") or []
        error_list = payload.get("errors") or []

        if isinstance(signed_list, dict):
            signed_list = [signed_list]
        if isinstance(error_list, dict):
            error_list = [error_list]

        error_by_dev_id = {}
        for err_item in error_list:
            dev_id = (err_item.get("DeviceID") or "").strip()
            if dev_id:
                error_by_dev_id[dev_id] = int(err_item.get("ConfigManagerErrorCode") or 0)

        results = []
        seen_keys = set()
        seen_dev_ids = set()
        min_years = self._get_min_years()

        for item in signed_list:
            device = (item.get("DeviceName") or "").strip()
            dev_id = (item.get("DeviceID") or "").strip()
            provider = (item.get("DriverProviderName") or "Desconocido").strip()
            version = (item.get("DriverVersion") or "").strip()
            date_str = (item.get("DriverDateStr") or "").strip()
            inf = (item.get("InfName") or "").strip()
            dev_class = (item.get("DeviceClass") or "").strip()
            hw_raw = item.get("HardwareID") or ""
            hw_list = [str(x).strip() for x in hw_raw] if isinstance(hw_raw, list) else ([str(hw_raw).strip()] if hw_raw else [])
            hw_id = hw_list[0] if hw_list else ""

            err_code = error_by_dev_id.get(dev_id, 0)
            key = (device, inf, version, err_code)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if dev_id:
                seen_dev_ids.add(dev_id)

            hw_type = detect_hardware_type(dev_class, device, hw_id)
            detected_vendor, vendor_url = identify_vendor_from_hwid(hw_id, provider)
            status_lbl, tag, category, status_detail = evaluate_driver_classification(
                device, provider, detected_vendor, version, date_str, inf, dev_class, err_code, hw_id, min_years
            )

            results.append(
                {
                    "status": status_lbl,
                    "tag": tag,
                    "category": category,
                    "status_detail": status_detail,
                    "hw_type": hw_type,
                    "device": device,
                    "provider": provider,
                    "detected_vendor": detected_vendor,
                    "vendor_url": vendor_url,
                    "version": version,
                    "date": date_str,
                    "inf": inf,
                    "class": dev_class,
                    "hardware_id": hw_id,
                    "hardware_ids": hw_list,
                    "device_id": dev_id,
                    "error_code": err_code,
                }
            )

        for err_item in error_list:
            dev_id = (err_item.get("DeviceID") or "").strip()
            if dev_id and dev_id in seen_dev_ids:
                continue
            device = (err_item.get("Name") or "Dispositivo desconocido").strip()
            provider = (err_item.get("Manufacturer") or "Desconocido").strip()
            dev_class = (err_item.get("PNPClass") or "").strip()
            err_code = int(err_item.get("ConfigManagerErrorCode") or 28)
            hw_raw = err_item.get("HardwareID") or ""
            hw_list = [str(x).strip() for x in hw_raw] if isinstance(hw_raw, list) else ([str(hw_raw).strip()] if hw_raw else [])
            hw_id = hw_list[0] if hw_list else ""

            hw_type = detect_hardware_type(dev_class, device, hw_id)
            detected_vendor, vendor_url = identify_vendor_from_hwid(hw_id, provider)
            status_lbl, tag, category, status_detail = evaluate_driver_classification(
                device, provider, detected_vendor, "", "", "", dev_class, err_code, hw_id, min_years
            )

            results.append(
                {
                    "status": status_lbl,
                    "tag": tag,
                    "category": category,
                    "status_detail": status_detail,
                    "hw_type": hw_type,
                    "device": device,
                    "provider": provider,
                    "detected_vendor": detected_vendor,
                    "vendor_url": vendor_url,
                    "version": "",
                    "date": "",
                    "inf": "",
                    "class": dev_class,
                    "hardware_id": hw_id,
                    "hardware_ids": hw_list,
                    "device_id": dev_id,
                    "error_code": err_code,
                }
            )

        priority = {"missing": 0, "updatable": 1, "virtual": 2, "do_not_update": 3, "ok": 4}
        results.sort(key=lambda x: (priority.get(x["category"], 9), x["hw_type"].lower(), x["device"].lower()))
        return results

    def _on_scan_success(self, drivers: list[dict]):
        self.progress.stop()
        self.is_scanning = False
        self.btn_scan.configure(state=tk.NORMAL)

        self.all_drivers = drivers
        self._apply_filters()

        if drivers:
            self.btn_export_csv.configure(state=tk.NORMAL)
            self.btn_export_txt.configure(state=tk.NORMAL)

    def _on_scan_error(self, error_msg: str):
        self.progress.stop()
        self.is_scanning = False
        self.btn_scan.configure(state=tk.NORMAL)
        self.status_var.set("Error durante el escaneo.")
        messagebox.showerror("Error de escaneo", f"No se pudieron obtener los drivers:\n{error_msg}")

    def _apply_filters(self):
        self._filter_after_id = None
        query = self.search_var.get().strip().lower()
        cat = self.category_filter.get()
        only_third_party = self.filter_third_party.get()

        filtered = []
        for drv in self.all_drivers:
            if cat != "ALL" and drv["category"] != cat:
                continue
            if only_third_party and "microsoft" in drv["detected_vendor"].lower():
                continue

            if query:
                haystack = (
                    f"{drv['status']} {drv['hw_type']} {drv['device']} {drv['detected_vendor']} "
                    f"{drv['version']} {drv['inf']} {drv['hardware_id']}"
                ).lower()
                if query not in haystack:
                    continue

            filtered.append(drv)

        self.filtered_drivers = filtered
        self._refresh_table()

        c_miss = sum(1 for d in self.all_drivers if d["category"] == "missing")
        c_upd = sum(1 for d in self.all_drivers if d["category"] == "updatable")
        c_no = sum(1 for d in self.all_drivers if d["category"] == "do_not_update")
        c_ok = sum(1 for d in self.all_drivers if d["category"] == "ok")
        c_virt = sum(1 for d in self.all_drivers if d["category"] == "virtual")

        self.status_var.set(
            f"Total: {len(self.all_drivers)}  |  Necesita actualizarse: {c_miss}  |  "
            f"Puede actualizar: {c_upd}  |  Virtual: {c_virt}  |  No Actualizar: {c_no}  |  "
            f"Al Día: {c_ok}  |  Mostrando: {len(self.filtered_drivers)}"
        )

    def _refresh_table(self):
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        self.item_map.clear()

        for drv in self.filtered_drivers:
            iid = self.tree.insert(
                "",
                tk.END,
                values=(
                    drv["status"],
                    drv["hw_type"],
                    drv["device"],
                    drv["detected_vendor"],
                    drv["version"],
                    drv["date"],
                    drv["inf"],
                ),
                tags=(drv["tag"],),
            )
            self.item_map[iid] = drv

    def _sort_by_column(self, col: str, reverse: bool):
        key_name = "detected_vendor" if col == "provider" else col
        self.filtered_drivers.sort(key=lambda x: str(x.get(key_name, "")).lower(), reverse=reverse)
        self._refresh_table()
        self.tree.heading(col, command=lambda: self._sort_by_column(col, not reverse))

    def _export_csv(self):
        if not self.filtered_drivers:
            return

        default_name = f"diagnostico_drivers_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        file_path = filedialog.asksaveasfilename(
            title="Exportar diagnóstico de drivers a CSV",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("Archivo CSV (Excel)", "*.csv")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Estado",
                        "Detalle Diagnóstico",
                        "Tipo de Hardware",
                        "Dispositivo",
                        "Fabricante Detectado",
                        "Versión",
                        "Fecha",
                        "Archivo INF",
                        "Clase PnP",
                        "Hardware ID",
                    ]
                )
                for drv in self.filtered_drivers:
                    writer.writerow(
                        [
                            drv["status"],
                            drv["status_detail"],
                            drv["hw_type"],
                            drv["device"],
                            drv["detected_vendor"],
                            drv["version"],
                            drv["date"],
                            drv["inf"],
                            drv["class"],
                            drv["hardware_id"],
                        ]
                    )
            self.status_var.set(f"Exportado correctamente: {file_path}")
            messagebox.showinfo(
                "Exportación completada",
                f"Se guardaron {len(self.filtered_drivers)} registros en:\n{file_path}",
            )
        except Exception as exc:
            messagebox.showerror("Error al exportar", str(exc))

    def _export_txt(self):
        if not self.filtered_drivers:
            return

        default_name = f"reporte_drivers_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        file_path = filedialog.asksaveasfilename(
            title="Exportar reporte de drivers a TXT",
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
        )
        if not file_path:
            return

        try:
            lines = [
                f"REPORTE DE DIAGNÓSTICO DE CONTROLADORES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total incluidos en este reporte: {len(self.filtered_drivers)}",
                "=" * 84,
                "",
            ]
            for idx, drv in enumerate(self.filtered_drivers, start=1):
                lines.extend(
                    [
                        f"{idx:03d}. [{drv['status']}] [{drv['hw_type']}] {drv['device']}",
                        f"     Diagnóstico : {drv['status_detail']}",
                        f"     Fabricante  : {drv['detected_vendor']}",
                        f"     Versión     : {drv['version']}  |  Fecha: {drv['date']}",
                        f"     Archivo INF : {drv['inf']}  |  Clase PnP: {drv['class']}",
                        f"     Hardware ID : {drv['hardware_id']}",
                        "-" * 84,
                    ]
                )

            Path(file_path).write_text("\n".join(lines), encoding="utf-8")
            self.status_var.set(f"Exportado correctamente: {file_path}")
            messagebox.showinfo("Exportación completada", f"Reporte guardado en:\n{file_path}")
        except Exception as exc:
            messagebox.showerror("Error al exportar", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    app = DriverScannerApp(root)
    root.mainloop()