#!/bin/bash
# Dependency Security Scanning Script for Linux/Mac
# Scans Python dependencies for known vulnerabilities using pip-audit

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Default values
INSTALL=false
FIX=false
JSON=false
STRICT=false
OUTPUT="security-scan-report.txt"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install)
            INSTALL=true
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        --json)
            JSON=true
            OUTPUT="security-scan-report.json"
            shift
            ;;
        --strict)
            STRICT=true
            shift
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--install] [--fix] [--json] [--strict] [--output FILE]"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  NikNotes Dependency Security Scanner${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    if [ "$INSTALL" = true ]; then
        echo -e "${YELLOW}Installing pip-audit...${NC}"
        pip install pip-audit
        echo -e "${GREEN}pip-audit installed successfully!${NC}"
        echo ""
    else
        echo -e "${RED}ERROR: pip-audit is not installed.${NC}"
        echo -e "${YELLOW}Run this script with --install flag to install it:${NC}"
        echo -e "${NC}  ./scripts/scan_dependencies.sh --install${NC}"
        echo ""
        echo -e "${YELLOW}Or install manually:${NC}"
        echo -e "${NC}  pip install pip-audit${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}Starting dependency scan...${NC}"
echo -e "${GRAY}Scan date: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# Build pip-audit command
CMD="pip-audit --desc"

if [ "$JSON" = true ]; then
    CMD="$CMD --format json --output $OUTPUT"
else
    CMD="$CMD --format columns"
fi

if [ "$FIX" = true ]; then
    echo -e "${YELLOW}Auto-fix mode enabled - will attempt to upgrade vulnerable packages${NC}"
    CMD="$CMD --fix"
fi

if [ "$STRICT" = true ]; then
    echo -e "${YELLOW}Strict mode enabled - will fail on any vulnerability${NC}"
fi

# Run pip-audit
echo -e "${GRAY}Running: $CMD${NC}"
echo ""

if [ "$JSON" = true ]; then
    # JSON output goes to file
    eval "$CMD"
    echo ""
    echo -e "${GREEN}JSON report saved to: $OUTPUT${NC}"
else
    # Capture output for both display and file
    eval "$CMD" | tee "$OUTPUT"
    echo ""
    echo -e "${GREEN}Report saved to: $OUTPUT${NC}"
fi

echo ""
echo -e "${GREEN}Scan completed successfully!${NC}"

if [ "$STRICT" = true ]; then
    echo ""
    echo -e "${YELLOW}Running strict check...${NC}"
    if pip-audit --strict --require-hashes=false; then
        echo -e "${GREEN}No vulnerabilities found!${NC}"
    else
        echo -e "${RED}Vulnerabilities detected! See report above.${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Scan Summary:${NC}"
echo -e "${NC}  - Date: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${NC}  - Report: $OUTPUT${NC}"
echo -e "${NC}  - Mode: $(if [ "$FIX" = true ]; then echo "Auto-fix"; elif [ "$STRICT" = true ]; then echo "Strict"; else echo "Scan only"; fi)${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Display next steps
echo -e "${YELLOW}Next steps:${NC}"
echo -e "${NC}  1. Review the report above or in $OUTPUT${NC}"
echo -e "${NC}  2. Update vulnerable packages: pip install --upgrade <package>${NC}"
echo -e "${NC}  3. Run again with --fix to auto-upgrade: ./scripts/scan_dependencies.sh --fix${NC}"
echo -e "${NC}  4. Add to CI/CD: See .github/workflows/security-scan.yml${NC}"
echo ""
