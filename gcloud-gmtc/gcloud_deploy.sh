#!/bin/bash

clear

GCLOUD_SERVICE_NAME="gc-gmtc"
REDIRECT_URI="https://gc-gmtc-236139179984.us-west2.run.app"

# Capture the start time
start_time=$(date +%s)

# Print the start time in human-readable format
echo "${GCLOUD_SERVICE_NAME} to google cloud: start time: $(date -d @$start_time)"

# Prepare the classes-temp directory
echo "Preparing classes-temp directory..."
rm -rf classes-temp  # Remove any existing temp directory
rm -rf env_vars.yaml # Remove any existing temp directory
mkdir -p classes-temp
cp -f ../gcloud-classes/*.py classes-temp/

# Create the YAML header
echo "Creating env_vars.yaml..."
OUTPUT_FILE="env_vars.yaml"

# Read the .env file and convert each line to YAML format
while IFS='=' read -r key value; do
    # Skip empty lines and lines starting with '#'
    if [[ -z "$key" || "$key" =~ ^# ]]; then
        continue
    fi

    # Remove any double quotes around the value and escape special characters
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')

    # Ensure the key doesn't have leading/trailing spaces
    key=$(echo "$key" | xargs)

    # Write the key-value pair to the output file in YAML format
    echo "$key: \"$value\"" >>"$OUTPUT_FILE"
done <.env

echo "REDIRECT_URI: \"${REDIRECT_URI}\"" >>$OUTPUT_FILE
echo "env_vars.yaml created."

# Deploy to Google Cloud Run
gcloud run deploy "${GCLOUD_SERVICE_NAME}" \
    --source . \
    --platform managed \
    --region us-west2 \
    --allow-unauthenticated \
    --env-vars-file env_vars.yaml \
    --service-account 236139179984-compute@developer.gserviceaccount.com

rm -rf classes-temp  # Remove any existing temp directory
rm -rf env_vars.yaml # Remove any existing temp directory

end_time=$(date +%s)
duration=$((end_time - start_time))

# Convert the duration to a more human-readable format (hours, minutes, seconds)
hours=$((duration / 3600))
minutes=$(( (duration % 3600) / 60 ))
seconds=$((duration % 60))

echo "${GCLOUD_SERVICE_NAME} to google cloud | Completed at ${end_time} | Deployment Duration: ${hours}h ${minutes}m ${seconds}s"
echo "Deployment complete."
