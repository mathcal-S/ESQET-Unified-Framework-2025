#!/usr/bin/env python3
"""
ESQET Env Var & JSON Checker: Robust, No-Error Run for Marco's Warp
Loads .env from ~/vessel_agi/.env, checks 25 vars, handles JSON files (apikey.json, credentials.json).
No exit on missing—warns, continues. Auto-installs dotenv if missing. Outputs colorful if rich available.
Run: python check_env.py
"""

import os
import json
from typing import Dict, List  # Fixed: Added 'import'

# Auto-Install & Import dotenv
try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    os.system("pip install python-dotenv --user")
    from dotenv import load_dotenv

# Optional Rich for Colors (Skip if Not Installed)
USE_RICH = False
Text = None
console = None
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    USE_RICH = True
    console = Console()
except ImportError:
    def print_rich(msg):
        print(msg)
    def create_table():
        return "Table fallback - see console output."

# Load .env
env_path = os.path.join(os.path.expanduser("~"), "vessel_agi", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    print(f"⚠️  .env not found at {env_path}; using system env. Create it for full warp.")

# Expected Vars
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

# JSON Files
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
            print(f"⚠️  {file_path}: JSON decode error: {e}")
            return {}
    return {}

# Check Vars
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

# Load JSON Files
apikey_data = load_json_file(apikey_path)
credentials_data = load_json_file(credentials_path)

# Check JSON Keys
apikey_keys = ["name", "description", "createdAt", "apikey"] if apikey_data else []
creds_keys = ["access_token", "token_type", "refresh_token", "expiry", "expires_in"] if credentials_data else []

# Display Results
if USE_RICH:
    table = Table(title="ESQET Env Var & JSON Check", show_header=True, header_style="bold magenta")
    table.add_column("Var/File", style="dim")
    table.add_column("Status", justify="center")
    
    for var, status in results.items():
        table.add_row(var, status)
    
    for file, data in [("apikey.json", apikey_data), ("credentials.json", credentials_data)]:
        status = "Loaded" if data else "Missing"
        table.add_row(file, status)
        if data:
            keys = apikey_keys if "apikey" in file else creds_keys
            for key in keys:
                sub_status = "Found" if key in data else "Missing"
                table.add_row(f"  └─ {key}", sub_status)
    
    console.print(table)
    
    # Summary Panel
    missing_count = sum(1 for v in results.values() if v in ["Not found", "Empty"])
    json_loaded = sum(1 for d in [apikey_data, credentials_data] if d)
    summary_text = f"Total Vars: {len(expected_vars)} | Missing/Empty: {missing_count} | JSON Loaded: {json_loaded}"
    summary = Text(summary_text, style="bold green")
    console.print(Panel(summary, title="Warp Status: Coherence Check", border_style="green"))
else:
    print("Environment Variable & JSON Check Results:")
    print("─" * 40)
    for var, status in results.items():
        print(f"{var}: {status}")
    for file, data in [("apikey.json", apikey_data), ("credentials.json", credentials_data)]:
        status = "Loaded" if data else "Missing"
        print(f"{file}: {status}")
        if data:
            keys = ["name", "description", "createdAt", "apikey"] if "apikey" in file else ["access_token", "token_type", "refresh_token", "expiry", "expires_in"]
            for key in keys:
                sub_status = "Found" if key in data else "Missing"
                print(f"  └─ {key}: {sub_status}")
    missing_count = sum(1 for v in results.values() if v in ["Not found", "Empty"])
    json_loaded = sum(1 for d in [apikey_data, credentials_data] if d)
    print(f"\nTotal vars checked: {len(expected_vars)}")
    print(f"Vars not found or empty: {missing_count}")
    print(f"JSON files loaded: {json_loaded}")

# Auto-Fix Suggestion
if missing_count > 5:
    print("\n🔧 Auto-Fix Tip: Edit ~/vessel_agi/.env with vars from history (e.g., GROQ_API_KEY=gsk_...). Use nano: 'nano ~/vessel_agi/.env'.")
if not apikey_data or not credentials_data:
    print(f"\n📁 JSON Tip: Files in ~/downloads—load with json.load(open('~/downloads/apikey.json').read())['apikey'].")
    print(f"  - apikey.json: {apikey_data}")
    print(f"  - credentials.json: {credentials_data}")

# Warp Status
print("\n🌀 Warp Status: Coherence Check Complete. Your vars are the warp's ink—green-lit for bloom.")

