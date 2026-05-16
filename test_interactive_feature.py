#!/usr/bin/env python3
"""Test script to demonstrate the interactive feature"""

import sys
import io

# Simulate the structured output with multiple NEXT options
test_output = """PROJECT:     Test Interactive Feature
STATE:       Ready for testing
LAST ACTION: Implemented interactive mode
NEXT:        Update documentation or run tests or create examples
DEAD ENDS:   None"""

# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Simulating reboot.py with --interactive flag\n")
print("Generated Restoration String:")
print("=" * 50)

# Parse the output
fields = {}
for line in test_output.split("\n"):
    if ":" in line:
        key, _, val = line.partition(":")
        fields[key.strip()] = val.strip()

# Check for multiple options in NEXT
import re
if "NEXT" in fields:
    next_value = fields["NEXT"]
    has_or = " or " in next_value.lower()
    
    if has_or:
        options = re.split(r'\s+or\s+', next_value, flags=re.IGNORECASE)
        
        if len(options) > 1:
            print("\nMultiple NEXT options detected:")
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            
            while True:
                try:
                    choice = input(f"\nSelect option (1-{len(options)}): ").strip()
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(options):
                        fields["NEXT"] = options[choice_num - 1]
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(options)}")
                except (ValueError, KeyboardInterrupt):
                    print("\nKeeping original NEXT value")
                    break

# Display final card
print("\n" + "=" * 50)
for key, val in fields.items():
    print(f"{key:<12} {val}")
print("=" * 50)

# Made with Bob
