#!/usr/bin/env python3

import sys
import json
import urllib.request
import urllib.error

def get_system_info(host):
    url = f"http://{host}/api/system/info"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"Error: Received status code {response.status}")
                return None
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Error connecting to {host}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def calculate_error_rate(info):
    if not info or 'stratum' not in info or 'pools' not in info['stratum']:
        print("Error: Invalid system info structure.")
        return

    pools = info['stratum']['pools']
    active_pool_mode = info['stratum'].get('activePoolMode', 0) # 0: primary/fallback, 1: dual

    # Check if dual pool mode is active
    is_dual_pool = active_pool_mode == 1

    # In primary/fallback mode (0), we usually care about the active pool,
    # but the dashboard shows stats for pool 0 (primary).
    # However, the pools array might have data for both.

    # Let's iterate through all available pools data and calculate rates.
    for i, pool in enumerate(pools):
        accepted = pool.get('accepted', 0)
        rejected = pool.get('rejected', 0)

        if accepted == 0 and rejected == 0:
            error_rate = 0.0
        else:
            error_rate = (rejected / (accepted + rejected)) * 100

        pool_name = "Primary Pool" if i == 0 else "Fallback/Secondary Pool"
        if is_dual_pool:
            pool_name = f"Pool {i+1}"

        print(f"{pool_name}:")
        print(f"  Accepted Shares: {accepted}")
        print(f"  Rejected Shares: {rejected}")
        print(f"  Error Rate (Reject Rate): {error_rate:.2f}%")
        print("-" * 20)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 get_error_rate.py <hostname_or_ip>")
        sys.exit(1)

    host = sys.argv[1]
    info = get_system_info(host)

    if info:
        calculate_error_rate(info)

if __name__ == "__main__":
    main()
