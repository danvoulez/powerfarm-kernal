#!/usr/bin/env bash

PF_KEYCHAIN_ACCOUNT="${PF_KEYCHAIN_ACCOUNT:-powerfarm}"

pf_keychain_service() {
  case "$1" in
    supabase-access-token) printf '%s' 'powerfarm.supabase.access-token' ;;
    supabase-secret-key) printf '%s' 'powerfarm.supabase.secret-key' ;;
    github-app-id) printf '%s' 'powerfarm.github.app-id' ;;
    github-client-id) printf '%s' 'powerfarm.github.client-id' ;;
    github-client-secret) printf '%s' 'powerfarm.github.client-secret' ;;
    github-webhook-secret) printf '%s' 'powerfarm.github.webhook-secret' ;;
    *) return 1 ;;
  esac
}

pf_keychain_get() {
  local service
  service="$(pf_keychain_service "$1")" || return 1
  security find-generic-password -a "$PF_KEYCHAIN_ACCOUNT" -s "$service" -w 2>/dev/null
}

pf_keychain_set() {
  local name="$1"
  local value="$2"
  local service
  service="$(pf_keychain_service "$name")" || return 1
  security add-generic-password -U -a "$PF_KEYCHAIN_ACCOUNT" -s "$service" -w "$value" >/dev/null
}

pf_keychain_delete() {
  local service
  service="$(pf_keychain_service "$1")" || return 1
  security delete-generic-password -a "$PF_KEYCHAIN_ACCOUNT" -s "$service" >/dev/null 2>&1 || true
}

pf_secret_or_keychain() {
  local variable="$1"
  local keychain_name="$2"
  local value="${!variable:-}"
  if [ -n "$value" ]; then
    printf '%s' "$value"
    return
  fi
  pf_keychain_get "$keychain_name"
}
