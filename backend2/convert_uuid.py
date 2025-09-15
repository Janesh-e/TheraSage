#!/usr/bin/env python3
"""
Script to convert UUID columns to SQLite-compatible string columns
"""

import re

def convert_uuid_references(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace UUID column definitions
    content = re.sub(
        r'Column\(UUID\(as_uuid=True\)',
        'Column(get_uuid_column()',
        content
    )
    
    # Replace default=uuid.uuid4 with default=generate_uuid
    content = re.sub(
        r'default=uuid\.uuid4',
        'default=generate_uuid',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    convert_uuid_references("C:/Users/Harish/Desktop/Janesh/TheraSage/backend2/models.py")
    print("UUID conversion completed!")
