
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.expanduser("~"), "vessel_agi", ".env")
if not os.path.exists(env_path):
    print(f"Error: .env file not found at {env_path}")
    exit(1)
load_dotenv(env_path)

# Define expected variables
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

# Check each variable
results = {}
for var in expected_vars:
    value = os.getenv(var)
    if value is None:
        results[var] = "Not found"
    elif not value.strip():
        results[var] = "Empty or whitespace only"
    else:
        results[var] = "Found" if var not in ["GOOGLE_DRIVE_CREDENTIALS", "DEBUG_MODE"] else f"Found: {value}"

# Display results
print("Environment Variable Check Results:")
print("-" * 40)
for var, status in results.items():
    print(f"{var}: {status}")
print("-" * 40)
print(f"Total variables checked: {len(expected_vars)}")
print(f"Variables not found or empty: {sum(1 for status in results.values() if status not in ['Found', 'Found: ~/downloads/credentials.json', 'Found: false'])}")
