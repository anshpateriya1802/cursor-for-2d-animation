#!/bin/bash

# Create necessary directories
mkdir -p temp/generated
mkdir -p temp/output/videos
mkdir -p static

# Set proper permissions
chmod -R 755 temp
chmod -R 755 static

# Create empty files to ensure directories are tracked by git
touch temp/.gitkeep
touch temp/generated/.gitkeep
touch temp/output/.gitkeep
touch temp/output/videos/.gitkeep
touch static/.gitkeep 