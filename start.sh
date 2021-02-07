#!/bin/bash
timestamp() {
    date +"%Y-%m-%d %H-%M-%S"
}
filename() {
    "./logs/"$(timestamp)".txt"
}

python3 ./src/main.py | filename