#!/bin/bash
# Quick setup and run script for Empirical-Roofline-Toolkit

# Don't exit on error - we'll handle errors gracefully

ERT_DIR="$HOME/Desktop/ER"
ERT_BUILD_DIR="$ERT_DIR/Empirical_Roofline_Tool-1.1.0"
STREAM_DIR="$HOME/Desktop/STREAM"

echo "=========================================="
echo "Empirical-Roofline-Toolkit Setup Script"
echo "=========================================="
echo ""

# Step 1: Clone ERT repository if not exists
if [ ! -d "$ERT_DIR" ]; then
    echo "[1/5] Cloning ERT repository..."
    cd ~/Desktop
    git clone https://github.com/ebugger/Empirical-Roofline-Toolkit.git ER
    echo "✓ Repository cloned"
else
    echo "[1/5] ERT repository already exists at $ERT_DIR"
fi

# Step 2: Navigate to ERT directory
cd "$ERT_BUILD_DIR"

# Step 3: Check if ERT script exists
# Note: ERT handles compilation automatically when you run it
echo ""
echo "[3/5] Checking for ERT script..."
if [ -f "./ert" ]; then
    # Make sure it's executable
    chmod +x ./ert
    ERT_EXEC="./ert"
    echo "✓ Found ERT script: $ERT_EXEC"
    
    # Check for Python 2 (ERT requires Python 2)
    if command -v python2 &> /dev/null || command -v python2.7 &> /dev/null; then
        PYTHON2_CMD=$(command -v python2 || command -v python2.7)
        echo "✓ Python 2 found: $PYTHON2_CMD"
        # Update the ERT script to use python2 explicitly
        if ! head -1 ./ert | grep -q python2; then
            sed -i '1s|#!/usr/bin/env python|#!/usr/bin/env python2|' ./ert
            echo "✓ Updated ERT script to use Python 2"
        fi
    else
        echo "⚠ Warning: Python 2 not found. ERT requires Python 2."
        echo "   Try: sudo apt-get install python2"
        exit 1
    fi
else
    echo "⚠ ERT script not found at $ERT_BUILD_DIR/ert"
    exit 1
fi

# Step 4: Check for configuration file
echo ""
echo "[4/5] Checking for configuration file..."
# Look for a config file - ERT needs one
CONFIG_FILE=""
if [ -d "Config" ]; then
    # Prefer Tegra config if it exists, otherwise use any available config
    if [ -f "Config/config.tegra.01" ]; then
        CONFIG_FILE="Config/config.tegra.01"
        echo "   Using Tegra-specific config: $CONFIG_FILE"
    else
        # Try to find a suitable config file (prefer simpler CPU configs)
        CONFIG_FILE=$(find Config -name "config.*" | grep -v gpu | head -1)
        if [ -n "$CONFIG_FILE" ]; then
            echo "   Found config file: $CONFIG_FILE"
            echo "   Note: You may want to create a custom config for your system"
        else
            echo "   ⚠ No config file found in Config/ directory"
            echo "   ERT requires a configuration file. See ERT_Users_Manual.pdf"
        fi
    fi
else
    echo "   ⚠ Config directory not found"
fi

# Step 5: Run ERT
echo ""
echo "[5/5] Running ERT..."
echo "   Note: ERT will automatically compile the drivers when needed"
echo "   This may take several minutes..."
echo ""

# Create output directory for results
RESULTS_DIR="$STREAM_DIR/ert_results"
mkdir -p "$RESULTS_DIR"

# Detect CPU threads
NUM_THREADS=$(nproc)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$RESULTS_DIR/ert_output_${NUM_THREADS}threads_${TIMESTAMP}.txt"

echo "Running: $ERT_EXEC"
if [ -n "$CONFIG_FILE" ]; then
    echo "Using config: $CONFIG_FILE"
    echo "Command: $ERT_EXEC $CONFIG_FILE"
    echo "Output: $OUTPUT_FILE"
    echo ""
    $ERT_EXEC "$CONFIG_FILE" > "$OUTPUT_FILE" 2>&1 || {
        echo "⚠ ERT execution encountered issues. Check output file for details."
        echo "   Output saved to: $OUTPUT_FILE"
    }
else
    echo "⚠ Cannot run ERT without a configuration file."
    echo "   Please create or specify a config file."
    echo "   Example: $ERT_EXEC Config/your_config.txt"
    echo ""
    echo "   Available config files:"
    find Config -name "*.txt" -o -name "*.cfg" 2>/dev/null | head -5 || echo "   (none found)"
    exit 1
fi

if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo "=========================================="
    echo "ERT Run Complete!"
    echo "=========================================="
    echo "Results saved to: $OUTPUT_FILE"
    echo ""
    echo "Key metrics (if available):"
    grep -i "bandwidth\|throughput\|peak\|gflop\|gb/s" "$OUTPUT_FILE" | head -10 || echo "   (Check output file for results)"
    echo ""
    echo "Next steps:"
    echo "  1. Review the output file: $OUTPUT_FILE"
    echo "  2. Compare with your STREAM results"
    echo "  3. See ERT_USAGE_GUIDE.md for detailed usage instructions"
fi

