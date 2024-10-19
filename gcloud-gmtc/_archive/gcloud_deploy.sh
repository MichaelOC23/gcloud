#!/bin/bash

clear

gcloud run deploy gc-gmtc \
    --source . \
    --platform managed \
    --region us-west2 \
    --allow-unauthenticated
