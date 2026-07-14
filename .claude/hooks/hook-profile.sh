#!/usr/bin/env bash
# Hook profile system — controls hook aggressiveness
# Usage: HOOK_PROFILE=minimal|standard|strict
#
# minimal  — Security-only, no observations, no gateguard
# standard — Default: security + observations + gateguard
# strict   — Maximum: full auditing on every edit

PROFILE="${HOOK_PROFILE:-standard}"

case "$PROFILE" in
  minimal)
    export HOOK_ENABLE_SECURITY=true
    export HOOK_ENABLE_OBSERVATIONS=false
    export HOOK_ENABLE_GATEGUARD=false
    export HOOK_ENABLE_GITNEXUS=false
    echo "[hook-profile] minimal — security only" >&2
    ;;
  standard)
    export HOOK_ENABLE_SECURITY=true
    export HOOK_ENABLE_OBSERVATIONS=true
    export HOOK_ENABLE_GATEGUARD=true
    export HOOK_ENABLE_GITNEXUS=true
    echo "[hook-profile] standard — security + observations + gateguard" >&2
    ;;
  strict)
    export HOOK_ENABLE_SECURITY=true
    export HOOK_ENABLE_OBSERVATIONS=true
    export HOOK_ENABLE_GATEGUARD=true
    export HOOK_ENABLE_GITNEXUS=true
    export HOOK_VERIFY_EVERY_EDIT=true
    echo "[hook-profile] strict — maximum verification" >&2
    ;;
  *)
    echo "[hook-profile] unknown profile '$PROFILE', using standard" >&2
    export HOOK_ENABLE_SECURITY=true
    export HOOK_ENABLE_OBSERVATIONS=true
    export HOOK_ENABLE_GATEGUARD=true
    export HOOK_ENABLE_GITNEXUS=true
    ;;
esac
