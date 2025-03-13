"""
Test the phone number validation
"""

import pandas as pd
import re
import sys

# Import Excel file
try:
    file_path = sys.argv[1] if len(sys.argv) > 1 else "info.xlsx"
    df = pd.read_excel(file_path)
    print(f"Loaded Excel file with {len(df)} rows")
except Exception as e:
    print(f"Error loading Excel file: {e}")
    exit(1)

# Check column names
print("\nColumn names:", df.columns.tolist())

# Find the phone number column
phone_column = None
possible_names = ['cell_phone', 'phone', 'телефон', 'mobile', 'мобилен']
for name in possible_names:
    if name in df.columns:
        phone_column = name
        break

if not phone_column:
    print("\nCould not find a phone number column. Available columns:")
    for col in df.columns:
        print(f"  - {col}")
    exit(1)

print(f"\nUsing phone column: '{phone_column}'")

# Check types of phone numbers
def validate_phone_improved(phone):
    # Convert to string and handle None/NaN values
    if pd.isna(phone) or phone is None:
        return (True, "Empty value")
        
    phone_str = str(phone).strip().lower()
    
    # Empty values
    if phone_str == "" or phone_str in ('none', 'n/a', 'no phone'):
        return (True, "Empty text")
    
    # Home phones
    if phone_str.startswith('home:') or phone_str.startswith('home '):
        return (True, "Home phone")
    
    # Clean and check pattern
    cleaned_phone = re.sub(r'[\s\-\(\)\.]', '', phone_str)
    pattern = r'^\+?[0-9]{7,15}$'
    if re.match(pattern, cleaned_phone):
        return (True, "Valid number")
    
    return (False, f"Invalid format: {cleaned_phone}")

# Test validation on all phone numbers
print(f"\nValidating {len(df)} phone numbers:")
print("-" * 50)

valid_count = 0
invalid_count = 0
invalid_phones = []

for idx, row in df.iterrows():
    phone = row[phone_column]
    valid, reason = validate_phone_improved(phone)
    
    if valid:
        valid_count += 1
    else:
        invalid_count += 1
        invalid_phones.append((idx, phone, reason))
    
    # Print only the first 10 and any invalid ones
    if idx < 10 or not valid:
        print(f"Row {idx}: '{phone}' - {'VALID' if valid else 'INVALID'} ({reason})")

print("-" * 50)
print(f"Valid phones: {valid_count}")
print(f"Invalid phones: {invalid_count}")

if invalid_count > 0:
    print("\nDetails on invalid phones:")
    for idx, phone, reason in invalid_phones:
        print(f"Row {idx}: '{phone}' - {reason}")