#!/bin/bash
set -e

# Change ownership of the mounted volumes to the mirarr user
# This happens at runtime, so it fixes the host-mount issue
fix_permissions() {
    local dir="$1"
    
    if [ -d "$dir" ]; then
        # Check ownership of the directory itself
        if [ "$(stat -c '%U' "$dir")" != "mirarr" ]; then
            echo "Fixing permissions for $dir..."
            chown -R mirarr:mirarr "$dir" || true
        else
            echo "Permissions for $dir are correct. Skipping recursive chown."
        fi
    fi
}

fix_permissions "/app/data"
fix_permissions "/app/downloads"

# Execute the CMD passed from Dockerfile/Compose
# We use runuser to run the app as the 'mirarr' user
exec runuser -u mirarr -- "$@"
