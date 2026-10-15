#!/usr/bin/env bash
# Deploy MatchMind to Azure Container Apps. Requires: az login (done once).
set -euo pipefail
RG="${RG:-matchmind-rg}"
LOC="${LOC:-eastus}"
APP="${APP:-matchmind}"
ENVNAME="${ENVNAME:-matchmind-env}"

az group create -n "$RG" -l "$LOC" -o none
# Builds the Dockerfile in the cloud (ACR) and deploys to Container Apps:
az containerapp up \
  --name "$APP" \
  --resource-group "$RG" \
  --environment "$ENVNAME" \
  --location "$LOC" \
  --source . \
  --ingress external \
  --target-port 8000

echo "Live URL:"
az containerapp show -n "$APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv
