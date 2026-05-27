#!/bin/bash
set -e

# Build script for devicebase-mcp

echo "Building devicebase-mcp..."

# Clean
rm -rf build/ dist/ *.egg-info/

# Build
echo "Building wheel..."
uv build

echo ""
echo "Build complete!"
ls -la dist/