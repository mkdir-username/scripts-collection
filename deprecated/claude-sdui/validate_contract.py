#!/usr/bin/env python3
"""
Validate Web SDUI contract against metaschema
"""

import json
import jsonschema
from pathlib import Path

def validate_contract():
    # Load the metaschema
    metaschema_path = Path("/Users/username/Documents/FMS_GIT/metaschema/schema/strict_unversioned.json")
    # Get contract path from command line argument or use default
    import sys
    if len(sys.argv) > 1:
        contract_path = Path(sys.argv[1])
    else:
        contract_path = Path("/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/salary-main-screen-block.json")

    try:
        with open(metaschema_path, 'r') as f:
            metaschema = json.load(f)
    except FileNotFoundError:
        print(f"❌ Metaschema not found at: {metaschema_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in metaschema: {e}")
        return False

    try:
        with open(contract_path, 'r') as f:
            contract = json.load(f)
    except FileNotFoundError:
        print(f"❌ Contract not found at: {contract_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in contract: {e}")
        return False

    # Validate the contract
    try:
        jsonschema.validate(instance=contract, schema=metaschema)
        print(f"✅ Contract is valid against metaschema!")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        return False
    except jsonschema.SchemaError as e:
        print(f"❌ Schema error: {e.message}")
        return False

if __name__ == "__main__":
    validate_contract()