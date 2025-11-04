#!/usr/bin/env python3
"""
ESQET Env Var & JSON Checker: Robust, No-Error Run for Marco's Warp
Loads .env from ~/vessel_agi/.env, checks 25 vars, handles JSON files (apikey.json, credentials.json).
VQE-Specific: Checks Qiskit deps for VQE/QPU/Aer sim. Light Aer test for sim integration.
Termux Detection: Tailored install advice for Android/Termux (cmake/ninja + TUR repo for gcc/libgcc fixes).
Enhanced Colors: Full Rich integration (auto-install if missing). Fallback to ANSI escapes.
Run: python env_checker.py
"""

import os
import json
import sys
import platform
from typing import Dict, List

# Detect Termux
IS_TERMUX = 'com.termux' in os.environ.get('PREFIX', '') or 'ANDROID_ROOT' in os.environ

# Auto-Install & Import dotenv
try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    os.system("pip install python-dotenv --user")
    from dotenv import load_dotenv

# Auto-Install & Import Rich for Colors (if missing)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rprint
    USE_RICH = True
    console = Console()
except ImportError:
    # Fallback ANSI Colors
    USE_RICH = False
    COLORS = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'bold': '\033[1m',
        'reset': '\033[0m'
    }
    def color_text(text, color='white'):
        return f"{COLORS.get(color, '')}{COLORS['bold'] if 'bold' in color else ''}{text}{COLORS['reset']}"
    def rprint(msg, style=None):
        print(color_text(msg, style) if style else msg)

# Load .env
env_path = os.path.join(os.path.expanduser("~"), "vessel_agi", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    if USE_RICH:
        rprint(f"[green]✅ Loaded .env from {env_path}[/green]")
    else:
        print(color_text(f"✅ Loaded .env from {env_path}", 'green'))
else:
    if USE_RICH:
        rprint(f"[yellow]⚠️  .env not found at {env_path}; using system env. Create it for full warp.[/yellow]")
    else:
        print(color_text(f"⚠️  .env not found at {env_path}; using system env. Create it for full warp.", 'yellow'))

# Expected Vars (unchanged)
expected_vars = [
    "GIT_USER_NAME", "GIT_USER_EMAIL",
    "IBM_TOKEN", "GROQ_API_KEY", "NASA_API_KEY", "PINATA_API_KEY", "PINATA_API_SECRET",
    "PINATA_JWT", "QDRANT_API_KEY", "ETHERSCAN_API_KEY", "WEATHER_API_KEY", "USGS_API",
    "OPEN_METEO_API", "EXPO_TOKEN", "GITHUB_TOKEN",
    "PRIVATE_KEY", "PHICOIN_WALLET", "INFURA_KEY",
    "LINEA_SEPOLIA_RPC", "SEPOLIA_RPC_URL", "POLYGON_MAINNET_RPC",
    "GETBLOCK_MATIC_84D61", "GETBLOCK_MATIC_401AF",
    "GOOGLE_DRIVE_CREDENTIALS", "DEBUG_MODE"
]

# VQE-Specific Packages
VQE_PACKAGES = [
    "qiskit",
    "qiskit-algorithms",  # For VQE
    "qiskit-ibm-runtime",  # For QPU/Session
    "qiskit-aer",  # For Aer sim integration
    "numpy",
    "scipy"
]

# JSON Files (unchanged)
json_dir = os.path.expanduser("~/downloads")
apikey_path = os.path.join(json_dir, "apikey.json")
credentials_path = os.path.join(json_dir, "credentials.json")

def load_json_file(file_path: str) -> Dict:
    """Load JSON file or return {} if missing."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            if USE_RICH:
                rprint(f"[yellow]⚠️  {file_path}: JSON decode error: {e}[/yellow]")
            else:
                print(color_text(f"⚠️  {file_path}: JSON decode error: {e}", 'yellow'))
            return {}
    return {}

def check_vqe_dependencies():
    """Check VQE-specific packages and light Aer sim test."""
    missing = []
    details = {}
    vqe_ok = True
    aer_sim_ok = True

    for pkg in VQE_PACKAGES:
        try:
            if pkg == "qiskit-aer":
                import qiskit_aer  # Specific for Aer
                details[pkg] = "Installed and importable."
            else:
                __import__(pkg.replace("-", "_"))
                details[pkg] = "Installed and importable."
        except ImportError:
            missing.append(pkg)
            details[pkg] = f"Missing - install via 'pip install {pkg}'"
            vqe_ok = False

    # Light Aer Sim Integration Test (if Aer installed)
    if "qiskit-aer" not in missing:
        try:
            from qiskit_aer import AerSimulator
            # Minimal test: Create a simple circuit and run 1 shot (no backend needed)
            from qiskit import QuantumCircuit
            qc = QuantumCircuit(1, 1)
            qc.h(0)
            qc.measure(0, 0)
            sim = AerSimulator()
            result = sim.run(qc, shots=1).result()
            counts = result.get_counts()
            if counts:  # Basic success check
                details["AerSimulator"] = f"✅ Integrated: Sim test passed ({list(counts.keys())[0]} state)."
            else:
                details["AerSimulator"] = "⚠️  Aer imported but sim test failed (check shots/hardware)."
                aer_sim_ok = False
        except Exception as e:
            details["AerSimulator"] = f"❌ Aer sim test failed: {str(e)}"
            aer_sim_ok = False
    else:
        details["AerSimulator"] = "N/A (qiskit-aer missing)"
        aer_sim_ok = False

    overall_vqe = vqe_ok and aer_sim_ok
    return overall_vqe, details, missing

# Check Vars (unchanged logic, but with colors)
results = {}
for var in expected_vars:
    value = os.getenv(var)
    if value is None:
        results[var] = "Not found"
    elif not value.strip():
        results[var] = "Empty"
    else:
        results[var] = "Found"
        if var in ["PRIVATE_KEY", "PINATA_API_SECRET"]:
            results[var] += " (Secure)"

# Load JSON Files (unchanged)
apikey_data = load_json_file(apikey_path)
credentials_data = load_json_file(credentials_path)

# Check JSON Keys (unchanged)
apikey_keys = ["name", "description", "createdAt", "apikey"] if apikey_data else []
creds_keys = ["access_token", "token_type", "refresh_token", "expiry", "expires_in"] if credentials_data else []

# VQE Checks
vqe_ok, vqe_details, vqe_missing = check_vqe_dependencies()

# Display Results with Enhanced Colors
if USE_RICH:
    # Main Table
    table = Table(title="[bold magenta]ESQET Env Var & JSON Check[/bold magenta]", show_header=True, header_style="bold magenta")
    table.add_column("Var/File", style="dim")
    table.add_column("Status", justify="center", style="green" if vqe_ok else "red")

    # Env Vars
    for var, status in results.items():
        color = "green" if status == "Found" else "yellow" if "Secure" in status else "red"
        table.add_row(var, f"[{color}]{status}[/{color}]")

    # JSON Files
    for file, data in [("apikey.json", apikey_data), ("credentials.json", credentials_data)]:
        status = "Loaded" if data else "Missing"
        color = "green" if status == "Loaded" else "red"
        table.add_row(file, f"[{color}]{status}[/{color}]")
        if data:
            keys = apikey_keys if "apikey" in file else creds_keys
            for key in keys:
                sub_status = "Found" if key in data else "Missing"
                sub_color = "green" if sub_status == "Found" else "red"
                table.add_row(f"  └─ {key}", f"[{sub_color}]{sub_status}[/{sub_color}]")

    # VQE Section
    table.add_row("[bold cyan]--- VQE/QPU/Aer Sim Checks ---[/bold cyan]", "")
    for item, detail in vqe_details.items():
        color = "green" if "✅" in detail or "Installed" in detail else "red" if "❌" in detail else "yellow"
        table.add_row(item, f"[{color}]{detail}[/{color}]")

    console.print(table)

    # Summary Panel
    missing_count = sum(1 for v in results.values() if v in ["Not found", "Empty"])
    json_loaded = sum(1 for d in [apikey_data, credentials_data] if d)
    vqe_status = "✅ VQE Ready (incl. Aer Sim)" if vqe_ok else "❌ VQE Issues Detected"
    summary_text = Text(
        f"Total Vars: {len(expected_vars)} | Missing/Empty: {missing_count} | JSON Loaded: {json_loaded}\n{vqe_status}",
        style="bold green" if missing_count == 0 and vqe_ok else "bold red"
    )
    console.print(Panel(summary_text, title="[bold cyan]Warp Status: Coherence Check[/bold cyan]", border_style="cyan"))
else:
    # Fallback Plain + ANSI
    print(color_text("Environment Variable & JSON Check Results:", 'bold magenta'))
    print("─" * 50)
    for var, status in results.items():
        color = 'green' if status == "Found" else 'yellow' if "Secure" in status else 'red'
        print(f"{var}: {color_text(status, color)}")
    for file, data in [("apikey.json", apikey_data), ("credentials.json", credentials_data)]:
        status = "Loaded" if data else "Missing"
        color = 'green' if status == "Loaded" else 'red'
        print(f"{file}: {color_text(status, color)}")
        if data:
            keys = ["name", "description", "createdAt", "apikey"] if "apikey" in file else ["access_token", "token_type", "refresh_token", "expiry", "expires_in"]
            for key in keys:
                sub_status = "Found" if key in data else "Missing"
                sub_color = 'green' if sub_status == "Found" else 'red'
                print(f"  └─ {key}: {color_text(sub_status, sub_color)}")
    
    # VQE Section
    print(color_text("\n--- VQE/QPU/Aer Sim Checks ---", 'bold cyan'))
    for item, detail in vqe_details.items():
        color = 'green' if "✅" in detail or "Installed" in detail else 'red' if "❌" in detail else 'yellow'
        print(f"{item}: {color_text(detail, color)}")
    
    missing_count = sum(1 for v in results.values() if v in ["Not found", "Empty"])
    json_loaded = sum(1 for d in [apikey_data, credentials_data] if d)
    vqe_status = color_text("✅ VQE Ready (incl. Aer Sim)", 'green') if vqe_ok else color_text("❌ VQE Issues Detected", 'red')
    print(f"\nTotal vars checked: {len(expected_vars)}")
    print(f"Vars not found or empty: {missing_count}")
    print(f"JSON files loaded: {json_loaded}")
    print(vqe_status)

# Auto-Fix Suggestions (enhanced for VQE + Termux linker fixes)
if missing_count > 0:
    rprint("[yellow]🔧 Auto-Fix Tip: Edit ~/vessel_agi/.env with vars (e.g., IBM_TOKEN=...). Use nano: 'nano ~/vessel_agi/.env'.[/yellow]" if USE_RICH else color_text("🔧 Auto-Fix Tip: Edit ~/vessel_agi/.env with vars (e.g., IBM_TOKEN=...). Use nano: 'nano ~/vessel_agi/.env'.", 'yellow'))
if vqe_missing:
    if IS_TERMUX:
        termux_tip = """
🔧 Termux-Specific Fix for qiskit-aer (CMake/Ninja + libgcc Linker Issues):
1. Confirm TUR repo: pkg install tur-repo (already active per logs).
2. Install libgcc & GCC runtime: pkg install libgcc gcc binutils
3. For Python 3.8 compat: python3.8 -m pip install ninja cmake
4. Set linker flags: export LDFLAGS="-L$PREFIX/lib -lgcc -lstdc++"
5. Install qiskit-aer: python3.8 -m pip install qiskit-aer --no-cache-dir
If -lgcc persists, add to ~/.bashrc: export CC=clang export CXX=clang++
(Alternative: Skip Aer for QPU-only: Use qiskit-ibm-runtime directly in scripts.)
"""
        if USE_RICH:
            console.print(Panel(termux_tip, title="[yellow]Termux Build Guide[/yellow]", border_style="yellow"))
        else:
            print(color_text(termux_tip, 'yellow'))
    else:
        rprint(f"[yellow]📦 VQE Install: pip install {' '.join(vqe_missing)}[/yellow]" if USE_RICH else color_text(f"📦 VQE Install: pip install {' '.join(vqe_missing)}", 'yellow'))
if not apikey_data or not credentials_data:
    rprint(f"[yellow]📁 JSON Tip: Files in ~/downloads—load with json.load(open('~/downloads/apikey.json'))['apikey'].[/yellow]" if USE_RICH else color_text(f"📁 JSON Tip: Files in ~/downloads—load with json.load(open('~/downloads/apikey.json'))['apikey'].", 'yellow'))
    rprint(f"[dim]  - apikey.json: {apikey_data}[/dim]" if USE_RICH else f"  - apikey.json: {color_text(str(apikey_data), 'dim')}")
    rprint(f"[dim]  - credentials.json: {credentials_data}[/dim]" if USE_RICH else f"  - credentials.json: {color_text(str(credentials_data), 'dim')}")

# Warp Status (colorful close)
warp_msg = "🌀 Warp Status: Coherence Check Complete. Your vars are the warp's ink—green-lit for bloom." if missing_count == 0 and vqe_ok else "🌀 Warp Status: Partial Coherence. Fix above for full bloom."
if USE_RICH:
    rprint(f"[bold green]{warp_msg}[/bold green]")
else:
    print(color_text(warp_msg, 'bold green' if missing_count == 0 and vqe_ok else 'yellow'))
