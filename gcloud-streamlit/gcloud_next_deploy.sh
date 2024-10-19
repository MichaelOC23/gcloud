#!/bin/bash

clear

GCLOUD_SERVICE_NAME="simpleappservice-next"
REDIRECT_URI="https://simpleappservice-next-236139179984.us-west2.run.app"

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
    # Remove any double quotes around the value and escape special characters
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    echo "$key: \"$value\"" >>$OUTPUT_FILE
done <env_vars.env
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

rm -rf classes-temp # Remove any existing temp directory
rm -rf env_vars.yaml # Remove any existing temp directory

echo "Deployment complete."
