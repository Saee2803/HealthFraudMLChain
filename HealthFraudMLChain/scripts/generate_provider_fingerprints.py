#!/usr/bin/env python3
"""
CLI script to generate provider behavioral fingerprints.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.provider_fingerprint import ProviderFingerprintGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Generate provider behavioral fingerprints from claims data'
    )
    parser.add_argument(
        '--claims', 
        required=True, 
        help='Path to claims CSV file'
    )
    parser.add_argument(
        '--output', 
        default='artifacts', 
        help='Output directory (default: artifacts)'
    )
    parser.add_argument(
        '--config',
        help='Path to JSON config file (optional)'
    )
    
    args = parser.parse_args()
    
    # Load config if provided
    config = None
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Generate fingerprints
    generator = ProviderFingerprintGenerator(config)
    
    try:
        parquet_path, jsonl_path = generator.generate_fingerprints(
            args.claims, args.output
        )
        
        print("✅ Provider fingerprints generated successfully!")
        print(f"📊 Parquet output: {parquet_path}")
        print(f"📝 JSONL output: {jsonl_path}")
        
    except Exception as e:
        print(f"❌ Error generating fingerprints: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()