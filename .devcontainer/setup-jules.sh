#!/bin/bash
# ============================================================================
# Google Jules CLI Setup Script for Dev Containers / GitHub Codespaces
# ============================================================================
# This script sets up Google Jules CLI to work in environments with older glibc
# by configuring a Docker-based wrapper function.
#
# Jules requires glibc 2.32+, but Debian 11 (bullseye) has glibc 2.31
# Solution: Run Jules inside a Docker container with Node.js 20
# ============================================================================

set -e

echo "🚀 Setting up Google Jules CLI..."

# ============================================================================
# Step 1: Create Jules config directory structure
# ============================================================================
echo "📁 Creating Jules config directories..."
mkdir -p ~/.jules/cache

# ============================================================================
# Step 2: Check for credentials in order of priority
# ============================================================================
# Priority order:
#   1. GitHub Codespaces Secret (JULES_OAUTH_CREDS environment variable)
#   2. Workspace file (.devcontainer/secrets/jules_oauth_creds.json)
#   3. Existing local credentials (~/.jules/cache/oauth_creds.json)

WORKSPACE_CREDS="/workspaces/sample-workflow/.devcontainer/secrets/jules_oauth_creds.json"
LOCAL_CREDS="$HOME/.jules/cache/oauth_creds.json"

# Option 1: GitHub Codespaces Secret (most secure)
if [ -n "$JULES_OAUTH_CREDS" ]; then
    echo "✅ Found Jules credentials in GitHub Codespaces Secret"
    echo "$JULES_OAUTH_CREDS" > "$LOCAL_CREDS"
    chmod 600 "$LOCAL_CREDS"
    echo "✅ Credentials configured from environment variable"

# Option 2: Workspace file (persists across rebuilds)
elif [ -f "$WORKSPACE_CREDS" ]; then
    echo "✅ Found Jules credentials in workspace, copying to local config..."
    cp "$WORKSPACE_CREDS" "$LOCAL_CREDS"
    chmod 600 "$LOCAL_CREDS"
    echo "✅ Credentials copied successfully"

# Option 3: Existing local credentials
elif [ -f "$LOCAL_CREDS" ]; then
    echo "✅ Jules credentials already exist at $LOCAL_CREDS"

# No credentials found
else
    echo "⚠️  No Jules credentials found."
    echo ""
    echo "   To set up authentication, choose ONE of these methods:"
    echo ""
    echo "   📌 Method 1: GitHub Codespaces Secret (Recommended - Most Secure)"
    echo "      1. Go to GitHub → Settings → Codespaces → Secrets"
    echo "      2. Add secret named: JULES_OAUTH_CREDS"
    echo "      3. Value: Your oauth_creds.json content"
    echo "      4. Rebuild the Codespace"
    echo ""
    echo "   📌 Method 2: Workspace File (Persists in repo - gitignored)"
    echo "      1. Login on local machine: jules login"
    echo "      2. Copy credentials to: $WORKSPACE_CREDS"
    echo "      3. Rebuild the Codespace"
    echo ""
    echo "   📌 Method 3: Manual Setup (Current session only)"
    echo "      1. Login on local machine: jules login"
    echo "      2. Create file: $LOCAL_CREDS"
    echo "      3. Paste your credentials JSON"
fi

# ============================================================================
# Step 3: Add Jules function to shell configuration
# ============================================================================
echo "📝 Configuring shell aliases..."

# Create jules wrapper script
cat > ~/.local/bin/jules-wrapper << 'WRAPPER_EOF'
#!/bin/bash
# Jules CLI Docker Wrapper
# Runs Google Jules in a Docker container with glibc 2.32+ compatibility

docker run -it --rm \
    --network host \
    -v "$(pwd):/workspace" \
    -v "$HOME/.jules:/root/.jules:rw" \
    -w /workspace \
    node:20 npx -y @google/jules "$@"
WRAPPER_EOF

chmod +x ~/.local/bin/jules-wrapper

# Add to .bashrc if not already present
if ! grep -q "# Google Jules CLI Configuration" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'BASHRC_EOF'

# ============================================================================
# Google Jules CLI Configuration
# ============================================================================
# Jules requires glibc 2.32+, running via Docker for compatibility

jules() {
  docker run -it --rm \
    --network host \
    -v "$(pwd):/workspace" \
    -v "$HOME/.jules:/root/.jules:rw" \
    -w /workspace \
    node:20 npx -y @google/jules "$@"
}

export -f jules

# Alias for quick access
alias jules-tui='jules'
alias jules-list='jules remote list --session'
alias jules-repos='jules remote list --repo'

BASHRC_EOF
    echo "✅ Added Jules configuration to ~/.bashrc"
else
    echo "✅ Jules configuration already in ~/.bashrc"
fi

# Also add to .zshrc if it exists
if [ -f ~/.zshrc ]; then
    if ! grep -q "# Google Jules CLI Configuration" ~/.zshrc 2>/dev/null; then
        cat >> ~/.zshrc << 'ZSHRC_EOF'

# ============================================================================
# Google Jules CLI Configuration
# ============================================================================
jules() {
  docker run -it --rm \
    --network host \
    -v "$(pwd):/workspace" \
    -v "$HOME/.jules:/root/.jules:rw" \
    -w /workspace \
    node:20 npx -y @google/jules "$@"
}

alias jules-tui='jules'
alias jules-list='jules remote list --session'
alias jules-repos='jules remote list --repo'

ZSHRC_EOF
        echo "✅ Added Jules configuration to ~/.zshrc"
    fi
fi

# ============================================================================
# Step 4: Pre-pull Docker image for faster first run
# ============================================================================
echo "🐳 Pre-pulling Node.js 20 Docker image (for faster Jules startup)..."
if docker pull node:20 > /dev/null 2>&1; then
    echo "✅ Docker image node:20 pulled successfully"
else
    echo "⚠️  Could not pre-pull Docker image (will be pulled on first use)"
fi

# ============================================================================
# Step 5: Verify setup
# ============================================================================
echo ""
echo "============================================================================"
echo "✅ Google Jules CLI Setup Complete!"
echo "============================================================================"
echo ""
echo "📋 Quick Commands:"
echo "   jules                    - Launch interactive TUI"
echo "   jules version            - Show version"
echo "   jules new 'task'         - Create new coding session"
echo "   jules remote list --session  - List all sessions"
echo "   jules-list               - Alias for listing sessions"
echo ""

# Check authentication status
if [ -f "$LOCAL_CREDS" ]; then
    echo "🔐 Authentication: Configured"
    echo "   Credentials: $LOCAL_CREDS"
else
    echo "🔐 Authentication: NOT CONFIGURED"
    echo ""
    echo "   ⚠️  To authenticate:"
    echo "   1. On your LOCAL machine, run: jules login"
    echo "   2. Copy ~/.jules/cache/oauth_creds.json content"
    echo "   3. Create file in Codespace: ~/.jules/cache/oauth_creds.json"
    echo "   4. For persistence, also save to:"
    echo "      $WORKSPACE_CREDS"
fi

echo ""
echo "============================================================================"
