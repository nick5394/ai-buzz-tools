#!/bin/bash
# Install git hooks for the repository
# This script sets up the pre-push hook that runs tests before pushing to main

set -e

# Get the repository root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
PRE_PUSH_HOOK="$HOOKS_DIR/pre-push"
SCRIPT_SOURCE="$REPO_ROOT/scripts/pre-push"

# Check if we're in a git repository
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if pre-push script exists
if [ ! -f "$SCRIPT_SOURCE" ]; then
    echo "❌ Error: Pre-push script not found at $SCRIPT_SOURCE"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Check if pre-push hook already exists
if [ -f "$PRE_PUSH_HOOK" ]; then
    echo "⚠️  Pre-push hook already exists at $PRE_PUSH_HOOK"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Copy the hook script
cp "$SCRIPT_SOURCE" "$PRE_PUSH_HOOK"
chmod +x "$PRE_PUSH_HOOK"

echo "✅ Pre-push hook installed successfully!"
echo ""
echo "The hook will now:"
echo "  • Run pytest before pushing to main"
echo "  • Test changed tools on localhost"
echo "  • Block push if tests fail"
echo ""
echo "To bypass in emergencies: git push --no-verify"
echo ""
