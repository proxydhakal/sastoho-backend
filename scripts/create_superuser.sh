#!/bin/bash
# Script to create superuser account

set -e

echo "============================================================"
echo "Creating Superuser Account"
echo "============================================================"
echo ""

# Run the Python script
python scripts/create_superuser.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Failed to create superuser"
    exit 1
fi

echo ""
echo "Script completed successfully!"
