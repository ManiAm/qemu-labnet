#!/usr/bin/env bash

ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
  export TARGETARCH=amd64
  export CONTAINER_NAME=qemu-x86
elif [ "$ARCH" = "aarch64" ]; then
  export TARGETARCH=arm64
  export CONTAINER_NAME=qemu-arm
else
  echo "Unsupported architecture: $ARCH"
  exit 1
fi

echo "Detected architecture: $ARCH"
echo "Set TARGETARCH=$TARGETARCH"
echo "Set CONTAINER_NAME=$CONTAINER_NAME"
