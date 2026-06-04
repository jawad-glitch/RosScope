#!/bin/bash
set -e

echo "======================================"
echo "  ROSscope - ROS 2 Observability"
echo "======================================"

echo "[1/3] Starting Prometheus + Grafana..."
docker compose up -d

echo "[2/3] Sourcing ROS 2 Humble..."
source /opt/ros/humble/setup.bash

echo "[3/3] Starting ROSscope collector..."
echo ""
echo "  Grafana:  http://localhost:3000  (admin/rosscope)"
echo "  Graph UI: http://localhost:8001"
echo "  Metrics:  http://localhost:8000/metrics"
echo ""
pip3 install -r requirements.txt --quiet
python3 main.py
