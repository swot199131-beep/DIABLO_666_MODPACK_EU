import json
import io
import hashlib
import re
import subprocess
import zipfile
import urllib.error
import urllib.request
import os
import shutil
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from datetime import datetime

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
    APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DIABLO_666_MODPACK_EU"
else:
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR
    APP_DATA_DIR = APP_DIR
CATALOG_PATH = RESOURCE_DIR / "catalog.json"

def expected_mod_compatibility_version():
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        return str(catalog.get("game_client", {}).get("mod_compatibility_version", "2.4.1.1"))
    except Exception:
        return "2.4.1.1"

def normalize_profile_name(name):
    cleaned = re.sub(r"[^0-9A-Za-zА-Яа-яЁё _-]+", "", str(name)).strip(" ._-")
    if not cleaned or len(cleaned) > 64:
        raise ValueError("Название профиля должно содержать от 1 до 64 допустимых символов.")
    return cleaned


def validate_profile_payload(profile, known_module_ids):
    if not isinstance(profile, dict) or profile.get("schema_version") != 1:
        raise ValueError("Неизвестный формат профиля.")
    ids = profile.get("selected_module_ids")
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
        raise ValueError("В профиле должен быть непустой список ID модификаций.")
    if len(ids) != len(set(ids)):
        raise ValueError("В профиле обнаружены повторяющиеся ID модификаций.")
    unknown = sorted(set(ids) - set(known_module_ids))
    if unknown:
        raise ValueError("Неизвестные ID модов: " + ", ".join(unknown))
    return set(ids)


GAME_CANDIDATES = [
    Path(r"C:\Games\World_of_Tanks_EU"),
    Path(r"C:\Games\World_of_Tanks"),
    Path(r"C:\Games\Wargaming.net\World_of_Tanks_EU"),
    Path(r"C:\Games\World_of_Tanks_EU"),
]

BG = "#111216"
PANEL = "#1b1d24"
PANEL2 = "#242731"
RED = "#d62935"
TEXT = "#f2f2f4"
MUTED = "#a4a8b3"
GREEN = "#64c98a"

class DiabloInstaller:
    def __init__(self, root):
        self.root = root
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.root.title("DIABLO_666 MODPACK EU 0.6.0")
        self.root.geometry("1120x720")
        self.root.minsize(980, 640)
        self.root.configure(bg=BG)
        self.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.modules = self.catalog["modules"]
        self.selected_id = self.modules[0]["id"] if self.modules else None
        self.checked = {m["id"]: bool(m.get("default")) for m in self.modules}
        self.game_path = self.detect_game_path()
        self.preview_image = None
        self.build_ui()
        self.refresh_module_list()
        if self.modules:
            self.select_module(self.modules[0]["id"])

    def detect_game_path(self):
        for p in GAME_CANDIDATES:
            if p.exists() and (p / "WorldOfTanks.exe").exists():
                return p
        # Common Wargaming Game Center locations are intentionally treated as hints only.
        return None

    def build_ui(self):
        header = tk.Frame(self.root, bg="#090a0d", height=88)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="DIABLO_666", fg=TEXT, bg="#090a0d",
                 font=("Segoe UI", 25, "bold")).pack(side="left", padx=(24, 8), pady=16)
        tk.Label(header, text="MODPACK EU", fg=RED, bg="#090a0d",
                 font=("Segoe UI", 19, "bold")).pack(side="left", pady=20)
        tk.Label(header, text="COMMUNITY EDITION  •  BUILD 0.6.0  •  LIVE 2.4.1_4 / MODS 2.4.1.1",
                 fg=MUTED, bg="#090a0d", font=("Segoe UI", 9, "bold")).pack(side="right", padx=24)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=16)

        left = tk.Frame(body, bg=PANEL, width=245)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)
        tk.Label(left, text="КАТЕГОРИИ", fg=MUTED, bg=PANEL,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(16, 8))
        self.category_var = tk.StringVar(value="Все моды")
        categories = ["Все моды"] + list(dict.fromkeys(m["category"] for m in self.modules))
        self.category_box = ttk.Combobox(left, textvariable=self.category_var,
                                         values=categories, state="readonly")
        self.category_box.pack(fill="x", padx=14, pady=(0, 12))
        self.category_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_module_list())
        tk.Label(left, text="ПОИСК", fg=MUTED, bg=PANEL,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(8, 5))
        self.search_var = tk.StringVar()
        search = tk.Entry(left, textvariable=self.search_var, bg=PANEL2, fg=TEXT,
                          insertbackground=TEXT, relief="flat")
        search.pack(fill="x", padx=14, ipady=8)
        self.search_var.trace_add("write", lambda *_: self.refresh_module_list())
        self.module_list = tk.Listbox(left, bg=PANEL, fg=TEXT, selectbackground=RED,
                                      selectforeground="white", relief="flat",
                                      highlightthickness=0, font=("Segoe UI", 10),
                                      activestyle="none")
        self.module_list.pack(fill="both", expand=True, padx=10, pady=12)
        self.module_list.bind("<<ListboxSelect>>", self.on_list_select)

        center = tk.Frame(body, bg=PANEL, width=310)
        center.pack(side="left", fill="y", padx=(0, 12))
        center.pack_propagate(False)
        tk.Label(center, text="СПИСОК МОДОВ", fg=TEXT, bg=PANEL,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=16)
        check_shell = tk.Frame(center, bg=PANEL)
        check_shell.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.check_canvas = tk.Canvas(check_shell, bg=PANEL, highlightthickness=0, borderwidth=0)
        check_scroll = ttk.Scrollbar(check_shell, orient="vertical", command=self.check_canvas.yview)
        self.check_canvas.configure(yscrollcommand=check_scroll.set)
        check_scroll.pack(side="right", fill="y")
        self.check_canvas.pack(side="left", fill="both", expand=True)
        self.check_area = tk.Frame(self.check_canvas, bg=PANEL)
        self.check_canvas_window = self.check_canvas.create_window((0, 0), window=self.check_area, anchor="nw")
        self.check_area.bind(
            "<Configure>",
            lambda _event: self.check_canvas.configure(scrollregion=self.check_canvas.bbox("all"))
        )
        self.check_canvas.bind(
            "<Configure>",
            lambda event: self.check_canvas.itemconfigure(self.check_canvas_window, width=event.width)
        )
        self.module_vars = {}
        self.module_check_widgets = {}
        for m in self.modules:
            var = tk.BooleanVar(value=self.checked[m["id"]])
            self.module_vars[m["id"]] = var
            row = tk.Frame(self.check_area, bg=PANEL2)
            row.pack(fill="x", pady=3)
            cb = tk.Checkbutton(row, text=m["name"], variable=var,
                                command=lambda mid=m["id"]: self.toggle_module(mid),
                                bg=PANEL2, fg=TEXT, selectcolor="#303440",
                                activebackground=PANEL2, activeforeground=TEXT,
                                anchor="w", wraplength=245, justify="left")
            cb.pack(fill="x", padx=8, pady=7)
            self.module_check_widgets[m["id"]] = row

        right = tk.Frame(body, bg=PANEL)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="ПРЕДПРОСМОТР", fg=TEXT, bg=PANEL,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 8))
        self.preview = tk.Label(right, text="Выберите мод, чтобы увидеть превью",
                                bg="#0b0c10", fg=MUTED, font=("Segoe UI", 12),
                                compound="center")
        self.preview.pack(fill="both", expand=False, padx=16, pady=4, ipady=100)
        self.detail_name = tk.Label(right, text="", fg=TEXT, bg=PANEL,
                                    font=("Segoe UI", 15, "bold"), anchor="w")
        self.detail_name.pack(fill="x", padx=16, pady=(14, 4))
        self.description = tk.Label(right, text="", fg=MUTED, bg=PANEL,
                                    font=("Segoe UI", 10), justify="left",
                                    anchor="nw", wraplength=450)
        self.description.pack(fill="x", padx=16, pady=4)
        self.meta = tk.Label(right, text="", fg=RED, bg=PANEL,
                             font=("Segoe UI", 9, "bold"), anchor="w")
        self.meta.pack(fill="x", padx=16, pady=8)
        self.source_button = tk.Button(
            right, text="ОТКРЫТЬ СТРАНИЦУ МОДА / ИСТОЧНИК",
            command=self.open_selected_source, bg=PANEL2, fg=TEXT,
            activebackground=RED, activeforeground="white",
            relief="flat", font=("Segoe UI", 9, "bold"), padx=12, pady=8,
            state="disabled"
        )
        self.source_button.pack(anchor="w", padx=16, pady=(2, 12))

        footer = tk.Frame(self.root, bg="#090a0d")
        footer.pack(fill="x", side="bottom")
        pathrow = tk.Frame(footer, bg="#090a0d")
        pathrow.pack(fill="x", padx=18, pady=(10, 4))
        tk.Label(pathrow, text="ПАПКА ИГРЫ:", bg="#090a0d", fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self.path_var = tk.StringVar(value=str(self.game_path) if self.game_path else "Не определена — укажите вручную")
        tk.Label(pathrow, textvariable=self.path_var, bg="#090a0d", fg=TEXT,
                 font=("Segoe UI", 9)).pack(side="left", padx=10)
        tk.Button(pathrow, text="Обзор…", command=self.browse_game,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=12).pack(side="right")
        bottom = tk.Frame(footer, bg="#090a0d")
        bottom.pack(fill="x", padx=18, pady=(4, 12))
        self.status = tk.Label(bottom, text="DIABLO 0.6.0 • WoT EU LIVE 2.4.1_4 • mods/2.4.1.1 • Official-source local imports.",
                               bg="#090a0d", fg=MUTED, anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        tk.Button(bottom, text="ЗАГРУЗИТЬ ПРОФИЛЬ", command=self.load_profile,
                  bg=PANEL2, fg=TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=11).pack(side="right", padx=(8, 0))
        tk.Button(bottom, text="СОХРАНИТЬ ПРОФИЛЬ", command=self.save_profile,
                  bg=PANEL2, fg=TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=11).pack(side="right", padx=(8, 0))
        tk.Button(bottom, text="УДАЛИТЬ МОДЫ DIABLO", command=self.uninstall,
                  bg=PANEL2, fg=TEXT, activebackground=RED,
                  activeforeground="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=14, pady=11).pack(side="right", padx=(8, 0))
        tk.Button(bottom, text="ИМПОРТ ОФИЦИАЛЬНОГО АРХИВА", command=self.import_official_archive,
                  bg=PANEL2, fg=TEXT, activebackground=RED,
                  activeforeground="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=14, pady=11).pack(side="right", padx=(8, 0))
        tk.Button(bottom, text="УСТАНОВИТЬ ВЫБРАННОЕ", command=self.install,
                  bg=RED, fg="white", activebackground="#a91f29",
                  activeforeground="white", relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=18, pady=11).pack(side="right")

    def refresh_module_list(self):
        if not hasattr(self, "module_list"):
            return
        self.module_list.delete(0, tk.END)
        self.visible_modules = []
        category = self.category_var.get()
        query = self.search_var.get().strip().lower()
        for m in self.modules:
            if category != "Все моды" and m["category"] != category:
                continue
            if query and query not in (m["name"] + " " + m["description"]).lower():
                continue
            self.visible_modules.append(m)
            mark = "✓ " if self.checked.get(m["id"]) else "□ "
            if m.get("blocked_reason"):
                suffix = "  [ЗАБЛОКИРОВАНО]"
            elif m.get("status") == "placeholder":
                suffix = "  [КОНЦЕПТ — НЕ УСТАНАВЛИВАЕТСЯ]"
            elif m.get("status") == "external_link_only":
                suffix = "  [НУЖЕН ИМПОРТ ИЗ ИСТОЧНИКА]"
            elif m.get("status") == "upstream_release":
                suffix = "  [ЗАГРУЗКА ИЗ РЕЛИЗА]"
            else:
                suffix = ""
            self.module_list.insert(tk.END, mark + m["name"] + suffix)

    def on_list_select(self, _event=None):
        sel = self.module_list.curselection()
        if sel and sel[0] < len(self.visible_modules):
            self.select_module(self.visible_modules[sel[0]]["id"])

    def _display_module_preview(self, module):
        self.preview_image = None
        preview_url = module.get("preview_url", "")
        if preview_url.startswith("https://wotmodsplanet.com/"):
            try:
                from PIL import Image, ImageTk
                cache_dir = APP_DATA_DIR / "preview_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path = cache_dir / (module["id"] + ".jpg")
                if not cache_path.is_file():
                    request = urllib.request.Request(
                        preview_url,
                        headers={"User-Agent": "DIABLO-666-MODPACK-EU/0.6.0"}
                    )
                    with urllib.request.urlopen(request, timeout=4) as response:
                        image_data = response.read(5 * 1024 * 1024 + 1)
                    if len(image_data) > 5 * 1024 * 1024:
                        raise ValueError("Превью превышает лимит 5 МБ.")
                    with Image.open(io.BytesIO(image_data)) as check:
                        check.verify()
                    cache_path.write_bytes(image_data)
                with Image.open(cache_path) as image:
                    image.thumbnail((560, 240))
                    self.preview_image = ImageTk.PhotoImage(image.copy())
                self.preview.config(image=self.preview_image, text="")
                return "source"
            except Exception:
                pass

        preview_path = RESOURCE_DIR / "assets" / module.get("preview", "")
        if preview_path.exists():
            try:
                self.preview_image = tk.PhotoImage(file=str(preview_path))
                self.preview.config(image=self.preview_image, text="")
                return "concept" if str(module.get("preview", "")).startswith("previews/concept_") else "local"
            except tk.TclError:
                self.preview.config(image="", text="Не удалось загрузить превью")
                return "none"
        else:
            self.preview.config(image="", text="ПРЕВЬЮ НЕДОСТУПНО")
            return "none"

    def select_module(self, module_id):
        self.selected_id = module_id
        m = next(x for x in self.modules if x["id"] == module_id)
        self.detail_name.config(text=m["name"])
        self.description.config(text=m["description"])
        preview_kind = self._display_module_preview(m)
        preview_note = {
            "source": "   •   ПРЕВЬЮ: СКРИНШОТ ИЗ ИСТОЧНИКА",
            "concept": "   •   ПРЕВЬЮ: КОНЦЕПТ",
            "local": "   •   ПРЕВЬЮ: ЛОКАЛЬНОЕ ИЗОБРАЖЕНИЕ"
        }.get(preview_kind, "   •   ПРЕВЬЮ НЕДОСТУПНО")
        self.meta.config(text=f'Версия: {m["version"]}   •   Лицензия: {m["license"]}   •   Статус: {m["status"].upper()}{preview_note}')
        source_url = m.get("source_url") or m.get("mod_hub") or ""
        self.source_button.config(state=("normal" if source_url.startswith("https://") else "disabled"))
        self.refresh_module_list()

    def open_selected_source(self):
        if not self.selected_id:
            return
        m = next((x for x in self.modules if x["id"] == self.selected_id), None)
        if not m:
            return
        url = m.get("source_url") or m.get("mod_hub") or ""
        if url.startswith("https://"):
            webbrowser.open(url)
        else:
            messagebox.showinfo("Источник не указан", "Для этого мода ещё не добавлена проверенная ссылка на первоисточник.")

    def get_selection_conflicts(self, selected_modules=None):
        selected_modules = selected_modules if selected_modules is not None else [
            m for m in self.modules if self.checked.get(m["id"])
        ]
        groups = {}
        conflicts = []
        for module in selected_modules:
            for group in module.get("conflict_groups", []):
                groups.setdefault(group, []).append(module["name"])
        for group, names in groups.items():
            if len(names) > 1:
                conflicts.append(
                    f"Группа «{group}»: одновременно выбраны " + ", ".join(names)
                )
        selected_ids = {m["id"] for m in selected_modules}
        for module in selected_modules:
            for other_id in module.get("conflicts_with", []):
                if other_id in selected_ids:
                    other = next((m for m in self.modules if m["id"] == other_id), None)
                    conflicts.append(f"{module['name']} несовместим с {other['name'] if other else other_id}")
        return conflicts

    def selection_warnings(self):
        selected = [m for m in self.modules if self.checked.get(m["id"])]
        warnings = self.get_selection_conflicts(selected)
        for module in selected:
            if module.get("blocked_reason"):
                warnings.append(f"{module['name']}: {module['blocked_reason']}")
        return warnings

    def toggle_module(self, module_id):
        self.checked[module_id] = self.module_vars[module_id].get()
        self.refresh_module_list()
        conflicts = self.get_selection_conflicts()
        if conflicts:
            messagebox.showwarning(
                "Конфликт модификаций",
                "Выбраны несовместимые компоненты. Снимите одну из галочек перед установкой:\n\n• "
                + "\n• ".join(conflicts)
            )

    def browse_game(self):
        chosen = filedialog.askdirectory(title="Выберите папку World of Tanks EU")
        if chosen:
            p = Path(chosen)
            if not (p / "WorldOfTanks.exe").exists():
                messagebox.showwarning("Папка не подтверждена",
                    "В выбранной папке не найден WorldOfTanks.exe. Проверьте, что выбрана корневая папка игры.")
                return
            self.game_path = p
            self.path_var.set(str(p))



    def _matches_any_pattern(self, filename, patterns):
        import fnmatch
        base = Path(filename).name.lower()
        return any(fnmatch.fnmatch(base, pattern.lower()) for pattern in patterns)

    def _prepare_local_official_import(self, module, archive_path, game_version):
        """Prepare a local-only package from an archive the user downloaded from WGMods."""
        from urllib.parse import urlparse
        source_host=urlparse(str(module.get("source_url",""))).hostname or ""
        allowed_hosts=module.get("manual_import_domains",[])
        if not module.get("manual_import_enabled") or not any(
            source_host==host or source_host.endswith("."+host) for host in allowed_hosts
        ):
            raise ValueError("Импорт не разрешён для этого источника или карточки.")
        expected_version = expected_mod_compatibility_version()
        if game_version != expected_version:
            raise ValueError(
                f"Этот импорт настроен для каталога модов {expected_version}; "
                f"обнаружена версия {game_version}."
            )
        package_dir = APP_DATA_DIR / "packages" / module["package_dir"]
        packages_root = package_dir.parent
        packages_root.mkdir(parents=True, exist_ok=True)
        staging_dir = packages_root / (module["package_dir"] + ".staging")
        files_dir = staging_dir / "files"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        files_dir.mkdir(parents=True, exist_ok=True)

        selected_payloads = []
        patterns = module.get("manual_import_patterns", [])
        dependency_patterns = module.get("manual_import_dependency_patterns", [])
        required_dependency_patterns = module.get("required_dependency_patterns", [])

        def validate_wotmod(data, label):
            if not data or len(data) > 250 * 1024 * 1024:
                raise ValueError(f"Некорректный размер файла: {label}")
            with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
                infos = zf.infolist()
                if not infos or len(infos) > 5000:
                    raise ValueError(f"Некорректное число записей в .wotmod: {label}")
                total_size = sum(info.file_size for info in infos)
                if total_size > 500 * 1024 * 1024:
                    raise ValueError(f"Слишком большой распакованный .wotmod: {label}")
                for info in infos:
                    member = info.filename
                    p = Path(member.replace("\\", "/"))
                    if p.is_absolute() or ".." in p.parts:
                        raise ValueError(f"Небезопасный путь внутри .wotmod: {member}")
                if zf.testzip():
                    raise ValueError(f"Повреждённый .wotmod: {label}")

        try:
            archive_path = Path(archive_path)
            if archive_path.suffix.lower() == ".wotmod":
                if archive_path.stat().st_size > 250 * 1024 * 1024:
                    raise ValueError("Архив превышает лимит 250 МБ.")
                raw = archive_path.read_bytes()
                if not self._matches_any_pattern(archive_path.name, patterns):
                    raise ValueError("Имя .wotmod не соответствует выбранной карточке.")
                validate_wotmod(raw, archive_path.name)
                selected_payloads.append((archive_path.name, raw))
            elif zipfile.is_zipfile(archive_path):
                with zipfile.ZipFile(archive_path, "r") as zf:
                    infos = zf.infolist()
                    if len(infos) > 2000:
                        raise ValueError("В архиве слишком много файлов.")
                    total_uncompressed = sum(info.file_size for info in infos)
                    if total_uncompressed > 750 * 1024 * 1024:
                        raise ValueError("Распакованный размер архива превышает лимит 750 МБ.")
                    if any(info.file_size > 250 * 1024 * 1024 for info in infos):
                        raise ValueError("Один из файлов архива превышает лимит 250 МБ.")
                    bad = zf.testzip()
                    if bad:
                        raise ValueError(f"Повреждён внешний архив: {bad}")
                    seen_names = set()
                    for info in infos:
                        if info.is_dir():
                            continue
                        base = Path(info.filename.replace("\\", "/")).name
                        if self._matches_any_pattern(base, patterns):
                            if base.lower() in seen_names:
                                raise ValueError(f"Дублируется имя основного файла: {base}")
                            seen_names.add(base.lower())
                            raw = zf.read(info)
                            validate_wotmod(raw, base)
                            selected_payloads.append((base, raw))
                        elif dependency_patterns and self._matches_any_pattern(base, dependency_patterns):
                            if not self._has_installed_pattern(game_version, [base]):
                                if base.lower() in seen_names:
                                    continue
                                seen_names.add(base.lower())
                                raw = zf.read(info)
                                validate_wotmod(raw, base)
                                selected_payloads.append((base, raw))
            else:
                raise ValueError("Выберите ZIP-архив или .wotmod, скачанный со страницы источника этой карточки.")

            expected_primary = [n for n, _ in selected_payloads if self._matches_any_pattern(n, patterns)]
            if len(expected_primary) != 1:
                raise ValueError("В выбранном архиве не найден ровно один файл нужного мода. Проверьте, что скачали правильный архив.")
            for required_pattern in required_dependency_patterns:
                bundled = any(self._matches_any_pattern(name, [required_pattern]) for name, _ in selected_payloads)
                installed = self._has_installed_pattern(game_version, [required_pattern])
                if not bundled and not installed:
                    raise ValueError(
                        f"Не найдена обязательная зависимость {required_pattern}. "
                        "Установите её из официального источника или выберите полный архив."
                    )

            manifest_files = []
            for filename, payload in selected_payloads:
                target = files_dir / filename
                target.write_bytes(payload)
                manifest_files.append({
                    "source": "files/" + filename,
                    "destination": f"mods/{game_version}/{filename}",
                    "sha256": hashlib.sha256(payload).hexdigest()
                })

            manifest = {
                "module_id": module["id"],
                "game_version": game_version,
                "author": module.get("author", ""),
                "source_url": module["source_url"],
                "license": "User-supplied download from the module source; installed locally only, not redistributed by DIABLO.",
                "redistribution_permission": "user_supplied_official_download",
                "local_import": True,
                "files": manifest_files
            }
            (staging_dir / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            # Atomic-ish replacement: retain the previous valid package until the new one is fully verified.
            old_dir = packages_root / (module["package_dir"] + ".previous")
            if old_dir.exists():
                shutil.rmtree(old_dir)
            if package_dir.exists():
                package_dir.replace(old_dir)
            try:
                staging_dir.replace(package_dir)
            except Exception:
                if old_dir.exists() and not package_dir.exists():
                    old_dir.replace(package_dir)
                raise
            if old_dir.exists():
                shutil.rmtree(old_dir)
            return manifest
        except Exception:
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)
            raise

    def import_official_archive(self):
        if not self.selected_id:
            messagebox.showinfo("Выберите мод","Сначала выберите мод с пометкой «Импорт доступен» в каталоге.")
            return
        module=next((m for m in self.modules if m["id"]==self.selected_id),None)
        if not module or not module.get("manual_import_enabled"):
            messagebox.showinfo("Импорт модов","Для выбранной карточки пока не настроен локальный импорт. Выберите мод с пометкой «Импорт доступен».")
            return
        if not self.game_path or not (self.game_path/"WorldOfTanks.exe").exists():
            messagebox.showwarning("Папка игры","Сначала укажите корневую папку World of Tanks EU.")
            return
        try:
            version=self._game_version()
        except Exception as exc:
            messagebox.showerror("Версия игры",str(exc))
            return
        if version!="2.4.1.1":
            messagebox.showwarning("Несовместимая версия","Этот пакет проверен по карточке для WoT 2.4.1.1. Импорт на другой версии заблокирован.")
            return
        if not messagebox.askyesno(
            "Источник мода",
            "Сначала скачайте архив самостоятельно со страницы источника.\n"
            "DIABLO не перепубликует чужой бинарник.\n\nОткрыть страницу мода?"
        ):
            return
        webbrowser.open(module["source_url"])
        chosen=filedialog.askopenfilename(
            title="Выберите архив, скачанный со страницы источника",
            filetypes=[("Архивы модов","*.zip *.wotmod"),("Все файлы","*.*")]
        )
        if not chosen:
            return
        try:
            manifest=self._prepare_local_official_import(module,chosen,version)
            messagebox.showinfo(
                "Импорт подготовлен",
                f"{module['name']} импортирован локально.\n"
                f"Файлов: {len(manifest['files'])}\n"
                "Теперь отметьте мод галочкой и нажмите «УСТАНОВИТЬ ВЫБРАННОЕ»."
            )
            self.status.config(text=f"Локальный пакет подготовлен: {module['name']} • WoT {version}")
        except Exception as exc:
            messagebox.showerror("Импорт не выполнен",str(exc))

    def _game_version(self):
        version_file = self.game_path / "version.xml"
        if not version_file.is_file():
            raise RuntimeError("В корне игры не найден version.xml. Нельзя безопасно определить версию клиента.")
        text = version_file.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"<version>\s*v?(\d+\.\d+\.\d+\.\d+)", text)
        if not match:
            raise RuntimeError("Не удалось прочитать номер версии из version.xml.")
        return match.group(1)

    def _game_running(self):
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq WorldOfTanks.exe", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=8
            )
            return "WorldOfTanks.exe" in result.stdout
        except Exception:
            # If process state cannot be checked, fail closed for file mutation.
            return True

    def _safe_relative(self, value):
        rel = Path(value)
        if rel.is_absolute() or not rel.parts or any(part in ("..", ".") for part in rel.parts):
            raise ValueError(f"Небезопасный относительный путь: {value}")
        if rel.parts[0].lower() not in ("mods", "res_mods"):
            raise ValueError(f"Разрешены только папки mods и res_mods: {value}")
        return rel

    def _state_path(self):
        key = __import__("hashlib").sha256(str(self.game_path.resolve()).encode("utf-8")).hexdigest()[:16]
        return APP_DATA_DIR / "installed_state" / f"{key}.json"


    def _has_openwg_gameface(self, game_version):
        version_dir = self.game_path / "mods" / game_version
        if not version_dir.is_dir():
            return False
        return any(version_dir.rglob("net.openwg.gameface_*.wotmod"))

    def _has_installed_pattern(self, game_version, patterns):
        version_dir = self.game_path / "mods" / game_version
        if not version_dir.is_dir():
            return False
        return any(
            self._matches_any_pattern(path.name, patterns)
            for path in version_dir.rglob("*.wotmod")
        )

    def _download_pinned_github_wotmod(self, module, game_version):
        """Fetch one pinned .wotmod release asset from the author's GitHub release."""
        if module.get("release_tag") != "v9.0.0":
            raise RuntimeError("Для этого компонента не задана одобренная закреплённая версия.")
        api_url = module.get("release_api", "")
        if not api_url.startswith("https://api.github.com/repos/"):
            raise RuntimeError("Недопустимый GitHub API URL.")

        request = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "DIABLO-666-MODPACK-EU/0.4.1"
            }
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.loads(response.read().decode("utf-8"))

        if release.get("tag_name") != module["release_tag"]:
            raise RuntimeError("GitHub вернул не ту версию релиза.")
        if release.get("draft") or release.get("prerelease"):
            raise RuntimeError("Релиз помечен как draft/prerelease и не допускается.")

        release_text = (release.get("body") or "").lower()
        if "2.4.1.1" not in release_text:
            raise RuntimeError("В описании релиза не подтверждена совместимость с WoT 2.4.1.1.")
        if game_version != "2.4.1.1":
            raise RuntimeError(f"Этот пакет закреплён для WoT 2.4.1.1, обнаружена версия {game_version}.")

        assets = release.get("assets", [])
        candidates = [
            a for a in assets
            if a.get("name", "").lower().endswith(".wotmod")
            and "moe_calculator" in a.get("name", "").lower()
            and a.get("browser_download_url", "").startswith("https://github.com/")
        ]
        if len(candidates) != 1:
            raise RuntimeError("В релизе не найден единственный ожидаемый .wotmod-файл MoE Calculator.")

        asset = candidates[0]
        package_dir = APP_DATA_DIR / "packages" / module["package_dir"]
        files_dir = package_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        target_file = files_dir / asset["name"]

        download_request = urllib.request.Request(
            asset["browser_download_url"],
            headers={"User-Agent": "DIABLO-666-MODPACK-EU/0.4.1", "Accept": "application/octet-stream"}
        )
        with urllib.request.urlopen(download_request, timeout=90) as response:
            payload = response.read()

        if not payload or len(payload) > 100 * 1024 * 1024:
            raise RuntimeError("Размер скачанного пакета пустой или превышает допустимые 100 МБ.")
        actual_hash = hashlib.sha256(payload).hexdigest()

        # GitHub's release API may expose a publisher-side SHA-256 digest.
        expected_digest = asset.get("digest") or ""
        if expected_digest.startswith("sha256:"):
            if actual_hash.lower() != expected_digest.split(":", 1)[1].lower():
                raise RuntimeError("SHA-256 скачанного файла не совпадает с digest GitHub Release.")

        temp_file = target_file.with_suffix(target_file.suffix + ".download")
        temp_file.write_bytes(payload)
        if not zipfile.is_zipfile(temp_file):
            temp_file.unlink(missing_ok=True)
            raise RuntimeError("Скачанный .wotmod не является корректным ZIP-контейнером.")

        # Reject archives containing absolute or parent-traversal paths before installing.
        with zipfile.ZipFile(temp_file, "r") as archive:
            names = archive.namelist()
            if not names:
                raise RuntimeError("Архив .wotmod пуст.")
            for name in names:
                path = Path(name.replace("\\", "/"))
                if path.is_absolute() or ".." in path.parts:
                    raise RuntimeError(f"В архиве обнаружен небезопасный путь: {name}")
            bad_member = archive.testzip()
            if bad_member:
                raise RuntimeError(f"Повреждённый элемент архива: {bad_member}")

        temp_file.replace(target_file)
        manifest = {
            "module_id": module["id"],
            "game_version": game_version,
            "author": module["author"],
            "source_url": module["source_url"],
            "release_tag": module["release_tag"],
            "license": module["license"],
            "redistribution_permission": "confirmed",
            "credits": module["credits"],
            "files": [{
                "source": "files/" + asset["name"],
                "destination": f"mods/{game_version}/{asset['name']}",
                "sha256": actual_hash
            }]
        }
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return package_dir

    def _reconcile_obsolete_files(self, state, desired_modules_by_path):
        """Remove only DIABLO-managed files absent from the new selection.

        Files changed by another tool/user are left untouched. Shared files are
        retained while at least one currently selected DIABLO module still uses them.
        """
        old_files = state.get("files", {})
        new_files = {}
        removed = 0
        skipped = []
        game_root = self.game_path.resolve()
        app_root = APP_DATA_DIR.resolve()

        for rel_text, record in old_files.items():
            rel = self._safe_relative(rel_text)
            target = self.game_path / rel
            if not target.resolve().is_relative_to(game_root):
                raise ValueError(f"Небезопасный путь в состоянии DIABLO: {rel_text}")

            desired_modules = desired_modules_by_path.get(rel.as_posix())
            if desired_modules:
                if target.is_file():
                    current_hash = hashlib.sha256(target.read_bytes()).hexdigest()
                    if current_hash != record.get("installed_sha256"):
                        raise RuntimeError(
                            f"Файл {rel_text} изменён после установки DIABLO. "
                            "Чтобы не перезаписать чужой мод, установка остановлена. "
                            "Сначала восстановите/удалите этот файл вручную либо удалите мод через DIABLO."
                        )
                updated = dict(record)
                updated["modules"] = sorted(set(desired_modules))
                new_files[rel.as_posix()] = updated
                continue

            if not target.is_file():
                # The managed file was already removed manually.
                continue

            current_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if current_hash != record.get("installed_sha256"):
                skipped.append(rel_text + " (изменён другим модом/пользователем; оставлен)")
                continue

            backup_rel = record.get("backup")
            if backup_rel:
                backup_path = Path(backup_rel)
                if backup_path.is_absolute() or ".." in backup_path.parts:
                    skipped.append(rel_text + " (небезопасный путь резервной копии)")
                    continue
                backup = (APP_DATA_DIR / backup_path).resolve()
                if not backup.is_relative_to(app_root):
                    skipped.append(rel_text + " (резервная копия вне каталога DIABLO)")
                    continue
                if not backup.is_file():
                    skipped.append(rel_text + " (резервная копия не найдена; файл оставлен)")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
            else:
                target.unlink()
            removed += 1

        state["files"] = new_files
        return removed, skipped

    def install(self):
        selected = [m for m in self.modules if self.checked.get(m["id"])]
        if not selected:
            messagebox.showinfo("Ничего не выбрано", "Отметьте хотя бы один мод.")
            return
        conflicts = self.get_selection_conflicts(selected)
        blocked = [m for m in selected if m.get("blocked_reason")]
        if conflicts or blocked:
            details = conflicts + [
                f"{m['name']}: {m['blocked_reason']}" for m in blocked
            ]
            messagebox.showerror(
                "Нельзя установить выбранный набор",
                "Исправьте конфликты/версии перед установкой:\n\n• " + "\n• ".join(details)
            )
            return
        if not self.game_path or not (self.game_path / "WorldOfTanks.exe").exists():
            messagebox.showwarning("Папка игры", "Сначала укажите корневую папку World of Tanks EU.")
            return
        if self._game_running():
            messagebox.showwarning("Игра запущена", "Закройте WorldOfTanks.exe перед установкой модификаций.")
            return

        try:
            game_version = self._game_version()
        except Exception as exc:
            messagebox.showerror("Версия игры", str(exc))
            return

        ready, missing, external = [], [], []
        for m in selected:
            local_manifest = APP_DATA_DIR / "packages" / m.get("package_dir", "") / "manifest.json"
            local_import = False
            if m.get("status") == "external_link_only" and local_manifest.is_file():
                try:
                    local_data=json.loads(local_manifest.read_text(encoding="utf-8"))
                    local_import=(local_data.get("module_id")==m["id"] and local_data.get("local_import") is True
                                  and local_data.get("redistribution_permission")=="user_supplied_official_download"
                                  and local_data.get("source_url")==m.get("source_url"))
                except Exception:
                    local_import=False
            if m.get("status") == "external_link_only" and not local_import:
                external.append(m)
                continue
            if m.get("status") == "upstream_release":
                dependency = (m.get("dependencies") or [{}])[0]
                if dependency.get("required") and not self._has_openwg_gameface(game_version):
                    missing.append(
                        m["name"] + " (нужен OpenWG GameFace " +
                        dependency.get("minimum_version", "1.2.2") + "+)"
                    )
                    if messagebox.askyesno(
                        "Нужна зависимость",
                        "Для MoE Calculator требуется OpenWG GameFace 1.2.2+ .\n"
                        "Открою официальный источник зависимости. Установите её отдельно, "
                        "затем повторите установку DIABLO?"
                    ):
                        webbrowser.open(dependency.get("source_url", "https://gitlab.com/openwg/wot.gameface/-/releases"))
                    continue
                try:
                    package = self._download_pinned_github_wotmod(m, game_version)
                except Exception as exc:
                    missing.append(m["name"] + " (загрузка/проверка не прошла: " + str(exc) + ")")
                    continue
            else:
                package = APP_DATA_DIR / "packages" / m.get("package_dir", "")
            manifest_path = package / "manifest.json"
            if m.get("status") not in ("ready", "upstream_release", "external_link_only") or not manifest_path.is_file():
                missing.append(m["name"])
                continue
            if m.get("redistribution_permission") not in ("confirmed", "license_allows_redistribution") and not local_import:
                missing.append(m["name"] + " (нет подтверждённого разрешения на распространение)")
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("module_id") != m["id"]:
                    raise ValueError("module_id в manifest не совпадает с каталогом")
                supported = manifest.get("game_version")
                if supported != game_version:
                    raise ValueError(f"пакет рассчитан на {supported}, клиент установлен {game_version}")
                if not manifest.get("source_url", "").startswith("https://"):
                    raise ValueError("нет HTTPS-источника")
                if not manifest.get("license") or not manifest.get("redistribution_permission"):
                    raise ValueError("не заполнены лицензия/разрешение")
                if local_import and not (
                    manifest.get("local_import") is True
                    and manifest.get("redistribution_permission") == "user_supplied_official_download"
                    and manifest.get("source_url") == m.get("source_url")
                ):
                    raise ValueError("локальный импорт не подтверждён источником/манифестом")
                entries = manifest.get("files", [])
                if not entries:
                    raise ValueError("в manifest нет файлов")
                checked_entries = []
                for entry in entries:
                    rel_source = Path(entry["source"])
                    if rel_source.is_absolute() or ".." in rel_source.parts:
                        raise ValueError("небезопасный путь исходного файла")
                    source_file = package / rel_source
                    if not source_file.is_file():
                        raise ValueError(f"файл пакета отсутствует: {entry['source']}")
                    rel_dest = self._safe_relative(entry["destination"])
                    expected_hash = entry.get("sha256", "").lower()
                    actual_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
                    if not expected_hash or actual_hash != expected_hash:
                        raise ValueError(f"SHA-256 не совпадает: {entry['source']}")
                    checked_entries.append((source_file, rel_dest, actual_hash))
                ready.append((m, package, manifest, checked_entries))
            except Exception as exc:
                missing.append(f'{m["name"]} (ошибка проверки: {exc})')

        if external:
            names="\n• ".join(m["name"] for m in external)
            if messagebox.askyesno(
                "Нужна загрузка с сайта автора",
                "Эти моды пока не импортированы. Скачайте их с официальной страницы автора и используйте кнопку «ИМПОРТ ОФИЦИАЛЬНОГО АРХИВА»:\n\n• "
                + names + "\n\nОткрыть официальные страницы сейчас?"
            ):
                from urllib.parse import urlparse
                for item in external:
                    url=item.get("source_url","")
                    host=urlparse(url).hostname or ""
                    allowed=item.get("manual_import_domains",[])
                    if url.startswith("https://") and any(
                        host==domain or host.endswith("."+domain) for domain in allowed
                    ):
                        webbrowser.open(url)
        if missing:
            messagebox.showwarning(
                "Не допущены к установке",
                "Пропущены компоненты без проверенного пакета/совместимости/разрешения:\n\n• " +
                "\n• ".join(missing)
            )
        if not ready:
            self.status.config(text="Нет выбранных модов, допущенных к установке.")
            return

        if not messagebox.askyesno(
            "Подтверждение",
            f"Будет установлено компонентов: {len(ready)} для WoT {game_version}.\n"
            "Перед заменой файлов будут сохранены резервные копии. "
            "Моды DIABLO, которых нет в новом выбранном наборе, будут удалены или восстановлены. "
            "Чужие моды и изменённые сторонние файлы DIABLO не тронет. Продолжить?"
        ):
            return

        state_path = self._state_path()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {"game_path": str(self.game_path.resolve()), "game_version": game_version, "files": {}}
        old_state_text = state_path.read_text(encoding="utf-8") if state_path.is_file() else None
        if state_path.is_file():
            state = json.loads(old_state_text)
            if Path(state.get("game_path", "")).resolve() != self.game_path.resolve():
                raise RuntimeError("Файл состояния относится к другой папке игры.")

        # Build the exact set of files required by the newly selected modules.
        desired_modules_by_path = {}
        for module, _package, _manifest, entries in ready:
            for _source_file, rel_dest, _file_hash in entries:
                desired_modules_by_path.setdefault(rel_dest.as_posix(), []).append(module["id"])

        backup_root = APP_DATA_DIR / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        transaction_root = APP_DATA_DIR / "transactions" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        newly_written, created_dirs = [], []
        rollback_snapshots = {}
        obsolete_removed = 0
        obsolete_skipped = []
        try:
            # Snapshot every destination before reconciliation or replacement.
            paths_to_touch = set(state.get("files", {})) | set(desired_modules_by_path)
            for rel_text in paths_to_touch:
                rel = self._safe_relative(rel_text)
                target = self.game_path / rel
                if not target.resolve().is_relative_to(self.game_path.resolve()):
                    raise ValueError(f"Небезопасный путь назначения: {rel_text}")
                if target.is_file():
                    snap = transaction_root / rel
                    snap.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, snap)
                    rollback_snapshots[rel.as_posix()] = (snap, True)
                else:
                    rollback_snapshots[rel.as_posix()] = (None, False)

            obsolete_removed, obsolete_skipped = self._reconcile_obsolete_files(
                state, desired_modules_by_path
            )

            for m, package, manifest, entries in ready:
                for source_file, rel_dest, file_hash in entries:
                    dest = self.game_path / rel_dest
                    if not dest.resolve().is_relative_to(self.game_path.resolve()):
                        raise ValueError(f"Путь назначения выходит за пределы папки игры: {rel_dest}")
                    key = rel_dest.as_posix()
                    existing_record = state["files"].get(key)
                    if existing_record is None:
                        backup_rel = None
                        if dest.exists():
                            backup_rel = (backup_root / rel_dest).relative_to(APP_DATA_DIR).as_posix()
                            backup = APP_DATA_DIR / backup_rel
                            backup.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(dest, backup)
                        state["files"][key] = {
                            "backup": backup_rel,
                            "installed_sha256": file_hash,
                            "modules": list(desired_modules_by_path.get(key, [m["id"]]))
                        }
                    else:
                        # Preserve the original pre-DIABLO backup, but refresh ownership
                        # to exactly the selected modules that use this destination.
                        state["files"][key]["installed_sha256"] = file_hash
                        state["files"][key]["modules"] = sorted(
                            set(desired_modules_by_path.get(key, [m["id"]]))
                        )
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, dest)

            state["game_path"] = str(self.game_path.resolve())
            state["game_version"] = game_version
            tmp_state = state_path.with_suffix(".json.tmp")
            tmp_state.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_state.replace(state_path)
        except Exception as exc:
            # Restore all files touched by this transaction to their exact pre-install state.
            for rel_text, (snapshot, existed) in rollback_snapshots.items():
                target = self.game_path / self._safe_relative(rel_text)
                try:
                    if existed and snapshot and snapshot.is_file():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(snapshot, target)
                    elif not existed and target.exists():
                        target.unlink()
                except Exception:
                    pass
            try:
                state_path.unlink(missing_ok=True)
                if "old_state_text" in locals() and old_state_text is not None:
                    state_path.write_text(old_state_text, encoding="utf-8")
            except Exception:
                pass
            shutil.rmtree(transaction_root, ignore_errors=True)
            messagebox.showerror("Ошибка установки", f"Установка отменена. Изменения откатаны.\\n\\n{exc}")
            return
        finally:
            shutil.rmtree(transaction_root, ignore_errors=True)

        messagebox.showinfo(
            "Установка завершена",
            f"Установлено компонентов: {len(ready)}.\nВерсия клиента: {game_version}.\n"
            + (f"Резервная копия: {backup_root}" if backup_root.exists() else "Перезаписанных файлов не было.")
        )
        self.status.config(text=f"Установлено компонентов: {len(ready)} • WoT {game_version}")

    def uninstall(self):
        if not self.game_path or not (self.game_path / "WorldOfTanks.exe").exists():
            messagebox.showwarning("Папка игры", "Сначала укажите корневую папку WoT EU.")
            return
        if self._game_running():
            messagebox.showwarning("Игра запущена", "Закройте WorldOfTanks.exe перед удалением модификаций.")
            return
        state_path = self._state_path()
        if not state_path.is_file():
            messagebox.showinfo("Нечего удалять", "Для этой папки игры DIABLO не зарегистрировал установленные файлы.")
            return
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if Path(state.get("game_path", "")).resolve() != self.game_path.resolve():
                raise RuntimeError("Файл состояния относится к другой папке игры.")
            if not messagebox.askyesno(
                "Удалить моды DIABLO",
                f"Будут обработаны файлы: {len(state.get('files', {}))}.\n"
                "Оригиналы, сохранённые при установке, будут восстановлены. Продолжить?"
            ):
                return
            removed, skipped = 0, []
            for rel_text, record in state.get("files", {}).items():
                rel = self._safe_relative(rel_text)
                target = self.game_path / rel
                if not target.resolve().is_relative_to(self.game_path.resolve()):
                    raise ValueError(f"Небезопасный путь: {rel_text}")
                # Do not overwrite a file changed by the user or another mod after DIABLO installed it.
                if target.is_file():
                    current_hash = hashlib.sha256(target.read_bytes()).hexdigest()
                    if current_hash != record.get("installed_sha256"):
                        skipped.append(rel_text)
                        continue
                backup_rel = record.get("backup")
                if backup_rel:
                    backup = APP_DATA_DIR / backup_rel
                    if backup.is_file():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, target)
                    else:
                        skipped.append(rel_text + " (резервная копия не найдена)")
                        continue
                elif target.exists():
                    target.unlink()
                removed += 1
            if skipped:
                messagebox.showwarning(
                    "Частичное удаление",
                    f"Восстановлено/удалено файлов: {removed}.\nПропущено изменённых или не найденных: {len(skipped)}.\n\n" +
                    "\n".join(skipped[:20])
                )
            else:
                state_path.unlink(missing_ok=True)
                messagebox.showinfo("Готово", f"Восстановлено/удалено файлов: {removed}.")
            self.status.config(text=f"Удаление завершено • файлов обработано: {removed}")
        except Exception as exc:
            messagebox.showerror("Ошибка удаления", str(exc))

if __name__ == "__main__":
    root = tk.Tk()
    app = DiabloInstaller(root)
    root.mainloop()
