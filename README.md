# Cyber-Range-Ransomware-Attack-vs-File-Recovery-Defense-Simulator
A full-featured GUI-based Python simulation of a **Ransomware Attack vs File Recovery Defense** scenario built on Cyber Range as a Service (CRaaS) principles.

 What This Simulates

### Red Team — Attack Engine
- **5-stage Kill Chain**: Initial Access → Key Generation → File Enumeration → Encryption Loop → Ransom Note
- Real **AES-128 symmetric encryption** via Python's `cryptography` (Fernet)
- Encrypts 15 realistic target files (`.txt`, `.csv`, `.json`, `.log`, `.ini`, `.db`)
- Drops a `RANSOM_NOTE.txt` with simulated demand and C2 details
- Encryption key captured in memory (models the key escrow problem)

### Blue Team — Defense Engine
- **Strategy A** — Restore from Backup: pre-attack backup copy restored
- **Strategy B** — Decrypt with Key: uses the captured AES key to decrypt `.locked` files
- **Strategy C** — Network Isolation: simulates firewall rules, C2 traffic blocking, SMB disabling
- Real-time **Defense Score** (0–100) that decrements per file encrypted and rewards smart response

### Threat Intelligence Module
- Live **Indicators of Compromise (IoC)** panel with severity levels (HIGH / MEDIUM / LOW)
- **Incident Timeline** logging all events with timestamps
- **Time to Detect (TTD)** metric
- **Incident Report** exported as structured JSON (incident ID, IoCs, timeline, score)

### File System State Panel
- Visual grid showing all 15 files transitioning: `Normal → Encrypting → Locked → Recovering → Safe`

---

## Architecture

```
ransomware_sim.py
├── AttackEngine        — Key gen, file encryption, kill-chain execution
├── DefenseEngine       — Backup restore, AES decryption, network isolation
├── ThreatIntelligence  — IoC tracker, timeline, scoring, JSON report export
├── FileManager         — Sandboxed test environment (15 realistic files)
└── CRaaSSimApp         — Full tkinter GUI (Red Team | File Grid | Blue Team)
```

---

## Requirements

- Python 3.8+
- `cryptography
-
-
## How to Use the App

| Step | Action | Panel |
|------|--------|-------|
| 1 | Click **Launch Ransomware Attack** | Red Team |
| 2 | Watch kill-chain stages progress, files turn locked | Stage bar + File Grid |
| 3 | Monitor IoC panel and Attack Log | Red Team |
| 4 | Click **Strategy C: Network Isolation** (optional, earns score) | Blue Team |
| 5 | Click **Strategy A** (Restore Backup) or **Strategy B** (Decrypt) | Blue Team |
| 6 | Watch files recover in real time | File Grid |
| 7 | Click **Export Incident Report** to save JSON | Blue Team |
| 8 | Click **Reset** to run again | Red Team |


Output Files Generated at Runtime

| File | Description |
|------|-------------|
| `craas_test_files/` | Auto-generated target files (15 realistic documents) |
| `craas_test_files_backup/` | Pre-attack backup (used by Strategy A) |
| `RANSOM_NOTE.txt` | Simulated demand note dropped after attack |
| `incident_report.json` | Structured IR report with IoCs, timeline, score |
| `craas_sim.log` | Full activity log for every run |

---

## Security Note

This application operates **exclusively on auto-generated files** in an isolated directory. It contains no real network activity and no actual malware behavior. Designed purely for academic learning within the CRaaS framework.` library

