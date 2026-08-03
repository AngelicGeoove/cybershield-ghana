#!/usr/bin/env python3
"""CLI helper to purge the URLhaus cache file used by services/threat_intel.py."""
import os
from services import threat_intel
from config import get_base_dir

def main():
    path = os.path.join(get_base_dir(), threat_intel.CACHE_FILENAME)
    if os.path.exists(path):
        try:
            os.remove(path)
            print('Purged', path)
        except Exception as e:
            print('Failed to purge:', e)
    else:
        print('No cache file at', path)

if __name__ == '__main__':
    main()
