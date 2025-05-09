#!/bin/bash

# Author: Mani Amoozadeh
# Email: mani.amoozadeh2@gmail.com

set -euo pipefail

TAP_IF=tap1
BRIDGE=br0
VXLAN_IF=vxlan100
VXLAN_ID=100
VXLAN_PORT=4789
PEER_IP=""
DEV_IF=""

function log() {
  echo -e "\e[1;34m[INFO]\e[0m $*"
}

function warn() {
  echo -e "\e[1;33m[WARN]\e[0m $*"
}

function err_exit() {
  echo -e "\e[1;31m[ERROR]\e[0m $*"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --peer-ip)
      PEER_IP="$2"
      shift 2
      ;;
    --tap)
      TAP_IF="$2"
      shift 2
      ;;
    --dev)
      DEV_IF="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$PEER_IP" ]]; then
  echo "Usage: $0 --peer-ip <other_host_ip> [--tap tap1] [--dev <auto-detect>]"
  exit 1
fi

# Detect default interface if not specified
if [[ -z "$DEV_IF" ]]; then
  DEV_IF=$(ip route get "$PEER_IP" | awk '{ for(i=1;i<=NF;i++) if ($i=="dev") print $(i+1); exit }')
  echo "Detected outbound interface: $DEV_IF"
fi

# Create TAP
if ip link show "$TAP_IF" &>/dev/null; then
  warn "TAP interface $TAP_IF already exists"
else
  log "Creating TAP interface: $TAP_IF"
  ip tuntap add dev "$TAP_IF" mode tap || err_exit "Failed to create TAP interface"
fi
ip link set "$TAP_IF" up || err_exit "Failed to bring TAP up"

# Create Bridge
if ip link show "$BRIDGE" &>/dev/null; then
  warn "Bridge $BRIDGE already exists"
else
  log "Creating bridge: $BRIDGE"
  ip link add "$BRIDGE" type bridge || err_exit "Failed to create bridge"
fi
ip link set "$BRIDGE" up || err_exit "Failed to bring bridge up"

# Create VXLAN
if ip link show "$VXLAN_IF" &>/dev/null; then
  warn "VXLAN interface $VXLAN_IF already exists"
else
  log "Creating VXLAN interface: $VXLAN_IF (remote: $PEER_IP)"
  ip link add "$VXLAN_IF" type vxlan id "$VXLAN_ID" dev "$DEV_IF" remote "$PEER_IP" dstport "$VXLAN_PORT" || err_exit "Failed to create VXLAN"
fi
ip link set "$VXLAN_IF" up || err_exit "Failed to bring VXLAN up"

# Add interfaces to bridge
for iface in "$VXLAN_IF" "$TAP_IF"; do
  if bridge link show | grep -q "$iface"; then
    warn "$iface is already part of $BRIDGE"
  else
    log "Adding $iface to bridge $BRIDGE"
    brctl addif "$BRIDGE" "$iface" || err_exit "Failed to add $iface to $BRIDGE"
  fi
done

log "VM Network configured: $TAP_IF <-> $BRIDGE <-> $VXLAN_IF <-> $PEER_IP"
