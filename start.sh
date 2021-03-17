#!/bin/bash
touch ./logs/$(date +"%Y-%m-%d_%H-%M-%S").txt
python3 ./src/main.py > ./logs/$(date +"%Y-%m-%d_%H-%M-%S").txt