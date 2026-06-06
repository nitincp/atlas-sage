#!/bin/bash
set -e

echo "=== ATLAS-SAGE Dev Container Setup ==="

# Install Claude Code
echo "Installing Claude Code..."
npm install -g @anthropic-ai/claude-code

# Fix SSH agent socket to use VM host agent
echo "Configuring SSH agent forwarding..."
echo 'export SSH_AUTH_SOCK=/ssh-agent' >> ~/.bashrc

# Python toolchain
echo "Setting up Python environment..."
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
if [ -f pyproject.toml ]; then
  pip install -e ".[dev]"
fi

echo "=== Setup Complete ==="
