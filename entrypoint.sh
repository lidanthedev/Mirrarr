#!/bin/bash
set -e

# Change ownership of the mounted volumes to the mirarr user
# This happens at runtime, so it fixes the host-mount issue
chown -R mirarr:mirarr /app/data /app/downloads

# Execute the CMD passed from Dockerfile/Compose
# We use gosu to run the app as the 'mirarr' user
exec runuser -u mirarr -- "$@"
