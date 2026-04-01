#!/bin/bash
# Reconstructs large binary app files from compressed chunks
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_BIN="$SCRIPT_DIR/app-binaries"

echo "Extracting Caprine..."
cat "$APP_BIN/caprine.tar.gz.part_"* > "$APP_BIN/caprine.tar.gz"
tar -xzf "$APP_BIN/caprine.tar.gz" -C "$SCRIPT_DIR"
rm -f "$APP_BIN/caprine.tar.gz"

echo "Extracting Caprine SquashFS..."
cat "$APP_BIN/caprine-squashfs.tar.gz.part_"* > "$APP_BIN/caprine-squashfs.tar.gz"
tar -xzf "$APP_BIN/caprine-squashfs.tar.gz" -C "$SCRIPT_DIR"
rm -f "$APP_BIN/caprine-squashfs.tar.gz"

echo "Extracting Marketing Manager..."
cat "$APP_BIN/marketing-manager.tar.gz.part_"* > "$APP_BIN/marketing-manager.tar.gz"
tar -xzf "$APP_BIN/marketing-manager.tar.gz" -C "$SCRIPT_DIR/marketing-manager-app/dist/linux-unpacked/"
rm -f "$APP_BIN/marketing-manager.tar.gz"

echo "Done! Apps extracted."
