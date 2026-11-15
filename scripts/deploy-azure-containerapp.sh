#!/usr/bin/env bash
set -Eeuo pipefail

# Run this script from any directory. It deploys only the SkyTrace backend.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

APP_NAME="${AZURE_CONTAINERAPP_NAME:-skytrace-backend}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-skytrace}"
ENVIRONMENT="${AZURE_CONTAINERAPPS_ENV:-skytrace-env}"
LOCATION="${AZURE_LOCATION:-centralindia}"
CPU="${AZURE_CPU:-0.5}"
MEMORY="${AZURE_MEMORY:-1.0Gi}"
MIN_REPLICAS="${AZURE_MIN_REPLICAS:-0}"
MAX_REPLICAS="${AZURE_MAX_REPLICAS:-2}"
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
ALLOWED_ORIGINS="${AZURE_ALLOWED_ORIGINS:-}"
ENV_ARGS=()
if [[ -n "$ALLOWED_ORIGINS" ]]; then
  ENV_ARGS+=(--env-vars "ALLOWED_ORIGINS=$ALLOWED_ORIGINS")
fi

if ! command -v az >/dev/null 2>&1; then
  echo "ERROR: Azure CLI (az) is not installed. Install it first: https://learn.microsoft.com/cli/azure/install-azure-cli"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required for the post-deployment health check."
  exit 1
fi

if ! az account show >/dev/null 2>&1; then
  echo "No active Azure CLI session. Starting device-code login..."
  az login --use-device-code
fi

if [[ -z "$SUBSCRIPTION_ID" ]]; then
  echo "ERROR: Set AZURE_SUBSCRIPTION_ID explicitly."
  echo "Available subscriptions:"
  az account list --query "[].{Name:name,SubscriptionId:id,State:state,IsDefault:isDefault}" --output table
  echo
  echo "Then run: AZURE_SUBSCRIPTION_ID='<subscription-id>' bash scripts/deploy-azure-containerapp.sh"
  exit 2
fi

az account set --subscription "$SUBSCRIPTION_ID"
ACCOUNT_NAME="$(az account show --query name --output tsv)"
ACCOUNT_ID="$(az account show --query id --output tsv)"
ACCOUNT_STATE="$(az account show --query state --output tsv)"

if [[ "$ACCOUNT_STATE" != "Enabled" ]]; then
  echo "ERROR: Selected Azure subscription is not enabled (state: $ACCOUNT_STATE)."
  exit 1
fi

cat <<EOF
Azure deployment target
-----------------------
Subscription : $ACCOUNT_NAME ($ACCOUNT_ID)
Resource group: $RESOURCE_GROUP
Region        : $LOCATION
Container App : $APP_NAME
Environment   : $ENVIRONMENT
Compute       : $CPU vCPU / $MEMORY
Scale         : $MIN_REPLICAS-$MAX_REPLICAS replicas
Allowed CORS  : ${ALLOWED_ORIGINS:-not set (localhost + *.vercel.app only)}
Source        : $REPO_ROOT/backend

Cost note: Container Apps Consumption includes monthly free usage grants, but
the Azure Container Registry created for source builds and any excess usage
can incur charges. Review your subscription budget before proceeding.
EOF

read -r -p "Provision/deploy these Azure resources? [y/N] " answer
if [[ ! "$answer" =~ ^[Yy]$ ]]; then
  echo "Cancelled. No Azure resources were created."
  exit 0
fi

echo "Installing/updating the Azure Container Apps CLI extension..."
az extension add --name containerapp --upgrade

echo "Registering required Azure resource providers..."
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az provider register --namespace Microsoft.ContainerRegistry --wait

echo "Creating or reusing resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --tags project=skytrace component=backend managed-by=azure-cli \
  --output none

echo "Building and deploying backend from ./backend..."
az containerapp up \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --environment "$ENVIRONMENT" \
  --source ./backend \
  --ingress external \
  --target-port 8000 \
  "${ENV_ARGS[@]}"

echo "Applying compute and scale-to-zero settings..."
az containerapp update \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --cpu "$CPU" \
  --memory "$MEMORY" \
  --min-replicas "$MIN_REPLICAS" \
  --max-replicas "$MAX_REPLICAS" \
  --output none

FQDN="$(az containerapp show \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn \
  --output tsv)"

if [[ -z "$FQDN" || "$FQDN" == "None" ]]; then
  echo "ERROR: Azure did not return an external ingress hostname."
  exit 1
fi

BASE_URL="https://$FQDN"
HEALTH_URL="$BASE_URL/health"

echo
echo "Deployment returned URL: $BASE_URL"
echo "Waiting for /health to return HTTP 200..."

for attempt in $(seq 1 60); do
  if curl --fail --silent --show-error --max-time 15 "$HEALTH_URL"; then
    echo
    echo "SUCCESS: SkyTrace backend health endpoint is responding."
    echo "API root : $BASE_URL/"
    echo "Swagger  : $BASE_URL/docs"
    echo "Health   : $HEALTH_URL"
    exit 0
  fi
  sleep 5
done

echo "ERROR: The app was created, but /health did not return HTTP 200 within 5 minutes."
echo "Inspect logs with:"
echo "az containerapp logs show --name $APP_NAME --resource-group $RESOURCE_GROUP --type console --follow"
exit 1
