#!/bin/bash
# cloud-init for the booth site instance: nothing but a current Ubuntu with python3 (already there).
apt-get update -qq && apt-get install -y -qq python3 >/dev/null
