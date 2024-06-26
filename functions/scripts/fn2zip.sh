#!/bin/bash

set -e
# set -x  # output commands logs 

# Function to display usage information
show_help() {
    echo "Usage: $0 [-h] [-o <output_zip_file>] [-e <exclude>] <project_directory>"
    echo "Create a zip file for an Azure Durable Function deployment."
    echo "Options:"
    echo "  -h, --help: Show this help message."
    echo "  -o, --output <output_zip_file>: Specify the output zip file name (default is the project directory name)."
    echo "  -e, --exclude <exclude>: Comma-separated list of directories and files to exclude (e.g., '.venv,.vscode,tests')."
}

# Clean up the temporary directory on script exit
cleanup() {
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -r "$TMP_DIR"
    fi
}

# Set up trap to call cleanup on exit or error
trap cleanup EXIT

# List of directories and files to exclude
EXCLUSIONS=(
    ".pytest_cache/*"
    "__pycache__/*"
    "requirements*"
    "tests/*"
    "pytest*"
    "*.sh"
)

# Parse command-line arguments
while getopts "ho:e:" opt; do
    case $opt in
        h)
            show_help
            exit 0
            ;;
        o)
            OUTPUT_ZIP_FILE="$OPTARG"
            ;;
        e)
            EXCLUSIONS+=("$OPTARG")
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_help
            exit 1
            ;;
    esac
done

# Shift the parsed options to process the non-option arguments
shift $((OPTIND - 1))

# Check for the number of arguments
if [ "$#" -lt 1 ]; then
    echo "Error: Project directory is not specified."
    show_help
    exit 1
fi

PROJECT_DIR="$1"

# If output zip file is not specified, use the project directory name
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR=$(readlink -f ${PROJECT_DIR})
fi

# Create a temporary directory
TMP_DIR=$(mktemp -d)

# Install dependencies in a temp folder environment
echo "Installing dependencies to deployment package..."
pip install -q --target "${TMP_DIR}/package/.python_packages/lib/site-packages" -r "${PROJECT_DIR}/requirements.txt"

pushd "${TMP_DIR}/package"
zip -q -r ../package.zip .
popd

ls -l ${TMP_DIR}/
echo "Updating package project files..."
pushd "${PROJECT_DIR}"
zip -x "${EXCLUSIONS[@]}" -r --update "${TMP_DIR}/package.zip" "."  
popd

OUTPUT_ZIP_FILE=${OUTPUT_DIR}/package.zip
mv "${TMP_DIR}/package.zip" ${OUTPUT_ZIP_FILE}

# Clean up temporary directory
cleanup

echo "Created ${OUTPUT_ZIP_FILE} with dependencies from requirements.txt."