#!/bin/bash
# One-click orchestrated deployment for AIIP Patent RPA System
# Usage: ./deploy_full.sh [phase]
# phase options: all|infra|openai|search|images|aks|monitor|validate
# If omitted defaults to 'all'.
set -e
PHASE=${1:-all}
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
ENV_FILE="$ROOT_DIR/.azure-deploy.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing .azure-deploy.env. Aborting." >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

log(){ echo -e "[deploy_full][$(date +%H:%M:%S)] $1"; }

az_account(){
  az account show >/dev/null 2>&1 || az login
  CURRENT=$(az account show --query id -o tsv)
  if [ "$CURRENT" != "$SUBSCRIPTION_ID" ]; then
    log "Setting subscription to $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
  fi
}

patch_scripts(){
  # Make original scripts consume .azure-deploy.env values instead of randomness
  sed -i 's/PatentRPASystemRG/'"$RESOURCE_GROUP"'/g' provision_azure_infra.sh || true
  sed -i 's/LOCATION="eastus"/LOCATION="'"$LOCATION"'"/g' provision_azure_infra.sh || true
  # Remove RANDOM usage & replace with deterministic names
  sed -i 's/ACR_NAME="patentRpaAcr$RANDOM"/ACR_NAME="'"$ACR_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/AKS_CLUSTER_NAME="PatentRPACluster"/AKS_CLUSTER_NAME="'"$AKS_CLUSTER_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/POSTGRES_SERVER_NAME="patent-rpa-postgres-$RANDOM"/POSTGRES_SERVER_NAME="'"$POSTGRES_SERVER_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/REDIS_CACHE_NAME="patent-rpa-redis-$RANDOM"/REDIS_CACHE_NAME="'"$REDIS_CACHE_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/SEARCH_SERVICE_NAME="patent-rpa-search-$RANDOM"/SEARCH_SERVICE_NAME="'"$SEARCH_SERVICE_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/OPENAI_SERVICE_NAME="patent-rpa-openai-$RANDOM"/OPENAI_SERVICE_NAME="'"$OPENAI_SERVICE_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/STORAGE_ACCOUNT_NAME="patentrpastorage$RANDOM"/STORAGE_ACCOUNT_NAME="'"$STORAGE_ACCOUNT_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/KEY_VAULT_NAME="patent-rpa-keyvault-$RANDOM"/KEY_VAULT_NAME="'"$KEY_VAULT_NAME"'"/' provision_azure_infra.sh || true
  sed -i 's/your_secure_password_here_P@ssw0rd123!/"'$POSTGRES_ADMIN_PASSWORD'"/' provision_azure_infra.sh || true

  # Patch other scripts random names
  sed -i 's/SEARCH_SERVICE_NAME="patent-rpa-search-$RANDOM"/SEARCH_SERVICE_NAME="'"$SEARCH_SERVICE_NAME"'"/' setup_ai_search.sh || true
  sed -i 's/STORAGE_ACCOUNT_NAME="patentrpastorage$RANDOM"/STORAGE_ACCOUNT_NAME="'"$STORAGE_ACCOUNT_NAME"'"/' setup_ai_search.sh || true
  sed -i 's/OPENAI_SERVICE_NAME="patent-rpa-openai-$RANDOM"/OPENAI_SERVICE_NAME="'"$OPENAI_SERVICE_NAME"'"/' setup_ai_search.sh || true
  sed -i 's/KEY_VAULT_NAME="patent-rpa-keyvault-$RANDOM"/KEY_VAULT_NAME="'"$KEY_VAULT_NAME"'"/' setup_ai_search.sh || true

  sed -i 's/OPENAI_SERVICE_NAME="patent-rpa-openai-$RANDOM"/OPENAI_SERVICE_NAME="'"$OPENAI_SERVICE_NAME"'"/' deploy_openai_models.sh || true

  sed -i 's/PatentRPASystemRG/'"$RESOURCE_GROUP"'/g' setup_monitoring.sh || true
  sed -i 's/PatentRPACluster/'"$AKS_CLUSTER_NAME"'/g' setup_monitoring.sh || true
  sed -i 's/eastus/'"$LOCATION"'/g' setup_monitoring.sh || true
  [ -z "$NOTIFICATION_EMAIL" ] && sed -i 's/NOTIFICATION_EMAIL="admin@your-company.com"/NOTIFICATION_EMAIL=""/' setup_monitoring.sh || true

  sed -i 's/ACR_NAME="patentRpaAcr"/ACR_NAME="'"$ACR_NAME"'"/' deploy_to_aks.sh || true
  sed -i 's/PatentRPASystemRG/'"$RESOURCE_GROUP"'/g' deploy_to_aks.sh || true
  sed -i 's/PatentRPACluster/'"$AKS_CLUSTER_NAME"'/g' deploy_to_aks.sh || true
}

phase_infra(){ log "(infra) Provision base infrastructure"; bash provision_azure_infra.sh; }
phase_openai(){ [ "$ENABLE_GPT4" = true ] || log "GPT4 disabled"; log "(openai) Deploy models"; bash deploy_openai_models.sh || true; }
phase_search(){ log "(search) Configure Azure AI Search"; bash setup_ai_search.sh; }
phase_images(){
  log "(images) Building and pushing images to ACR $ACR_NAME"
  az acr login --name "$ACR_NAME"
  BACKEND_IMAGE="$ACR_NAME.azurecr.io/patent-rpa-backend:$IMAGE_TAG"
  FRONTEND_IMAGE="$ACR_NAME.azurecr.io/patent-rpa-frontend:$IMAGE_TAG"
  BOTS_IMAGE="$ACR_NAME.azurecr.io/patent-rpa-bots:$IMAGE_TAG"
  docker build -t "$BACKEND_IMAGE" -f Dockerfile .
  # front-end placeholder: reuse same context; in real scenario separate Dockerfiles
  docker build -t "$FRONTEND_IMAGE" -f Dockerfile .
  docker build -t "$BOTS_IMAGE" -f Dockerfile .
  docker push "$BACKEND_IMAGE"; docker push "$FRONTEND_IMAGE"; docker push "$BOTS_IMAGE"
}
phase_aks(){ log "(aks) Deploy to AKS"; bash deploy_to_aks.sh "$IMAGE_TAG"; }
phase_monitor(){ [ "$ENABLE_MONITORING_DASHBOARD" = true ] && { log "(monitor) Setup monitoring"; bash setup_monitoring.sh; } || log "Monitoring disabled"; }
phase_validate(){ log "(validate) Running basic validation"; python validate_deployment.py || true; python integration_tests.py || true; }

run_all(){ phase_infra; phase_openai; phase_search; phase_images; phase_aks; phase_monitor; phase_validate; }

az_account
patch_scripts
case $PHASE in
  infra) phase_infra ;;
  openai) phase_openai ;;
  search) phase_search ;;
  images) phase_images ;;
  aks) phase_aks ;;
  monitor) phase_monitor ;;
  validate) phase_validate ;;
  all) run_all ;;
  *) echo "Unknown phase: $PHASE"; exit 2 ;;
esac
log "Deployment script finished phase: $PHASE"