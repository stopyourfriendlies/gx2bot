#! /bin/bash

# Bash script that updates the gx2bot code
# Used for remote shenanigans
git reset --hard
git pull
pipenv shell "pipenv sync"
