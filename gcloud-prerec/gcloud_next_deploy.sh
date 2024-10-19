#!/bin/bash

clear

# Prepare the classes-temp directory
echo "Preparing classes-temp directory..."
rm -rf classes-temp # Remove any existing temp directory
mkdir -p classes-temp
cp -f ../gcloud-classes/*.py classes-temp/

# Deploy to Google Cloud Run
gcloud run deploy next-gc-prerec \
    --source . \
    --platform managed \
    --region us-west2 \
    --allow-unauthenticated \
    --env-vars-file env_vars.yaml

rm -rf classes-temp # Remove any existing temp directory
