#!/bin/bash
# CONFIG / SETTINGS
ENV_PATH="${HOME}/code/scripts/env_variables.sh"
VENV_PATH="${HOME}/code/gcloud/gcloud_venv"
RUNPY_DIR="${HOME}/code/gcloud/gcloud-classes"

# Check if at least one argument (the Python script) is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <python_script> [arg1] [arg2]"
    exit 1
fi

# Path to the Python script
PYTHON_SCRIPT=$1

# Load environment variables
source "${ENV_PATH}"

# Optional parameters for the Python script
ARG1=${2:-}
ARG2=${3:-}

# echo -e "${PYTHON_SCRIPT} \n${ARG1} \n${ARG2}"

# Activate the virtual environment
source "${VENV_PATH}/bin/activate"

# Change directory to the live script folder
cd "${RUNPY_DIR}"

# Run the Python script with up to two optional parameters using the venv's Python
# Capture the Python script's output in a variable
python_output=$("$VENV_PATH/bin/python" "$PYTHON_SCRIPT" "$ARG1" "$ARG2")

# Deactivate the virtual environment
deactivate

# Check if the platform is macOS or Linux and copy the output to the clipboard
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Use pbcopy to copy output to clipboard
    echo "$python_output" | pbcopy
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux: Use xclip or xsel to copy output to clipboard (install xclip or xsel if not installed)
    echo "$python_output" | xclip -selection clipboard
    # Alternatively, for xsel:
    # echo "$python_output" | xsel --clipboard
else
    echo "Clipboard functionality is not supported on this OS."
fi

# Output the Python script result
echo "$python_output"
