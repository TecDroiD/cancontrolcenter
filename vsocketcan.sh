#!/bin/bash
# run with sudo
modprobe vcan
ip link add dev vcan0 type vcan
ip link set vcan0 up
