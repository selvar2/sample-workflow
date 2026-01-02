# Google Jules CLI - Complete Installation & Troubleshooting Guide

> **Version:** 0.1.42  
> **Last Updated:** January 2, 2026  
> **Environments:** GitHub Codespaces, VS Code Dev Containers, Remote Workspaces

---

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
   - [Method 1: Direct Installation (Local Machine)](#method-1-direct-installation-local-machine)
   - [Method 2: Docker-Based Installation (Dev Containers/Codespaces)](#method-2-docker-based-installation-dev-containerscodespaces)
4. [Authentication Setup](#authentication-setup)
   - [Local Machine Authentication](#local-machine-authentication)
   - [Codespaces/Dev Container Authentication](#codespacesdev-container-authentication)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Error Reference Table](#error-reference-table)
9. [FAQ](#faq)

---

## Overview

**Google Jules** is an asynchronous coding agent from Google that can be used via CLI to create coding sessions, manage tasks, and integrate with your development workflow.

### Key Features
- Create and manage coding sessions
- Assign tasks to Jules for autonomous execution
- Pull and apply patches from completed sessions
- Integration with GitHub repositories

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Linux (glibc 2.32+), macOS 12+, Windows 10+ (via WSL2) |
| **Node.js** | v18.0.0 or higher |
| **npm** | v8.0.0 or higher |
| **glibc** | 2.32 or higher (Linux only) |
| **Internet** | Required for authentication and API calls |
| **Google Account** | Required for OAuth authentication |

### Environment-Specific Requirements

| Environment | Additional Requirements |
|-------------|------------------------|
| **Local Machine** | Direct npm installation supported |
| **GitHub Codespaces** | Docker required (glibc compatibility) |
| **Dev Containers** | Docker required (Debian 11 has older glibc) |
| **WSL2** | Ubuntu 22.04+ recommended |

### Verify System Requirements

```bash
# Check Node.js version
node --version

# Check npm version
npm --version

# Check glibc version (Linux only)
ldd --version | head -1

# Check Docker availability (for containerized environments)
docker --version
```

**Expected Output:**
```
v20.x.x (Node.js 18+ required)
10.x.x (npm 8+ required)
ldd (GNU libc) 2.34+ (for direct installation)
Docker version 24.x.x
```

---

## Installation Methods

### Method 1: Direct Installation (Local Machine)

Use this method on systems with **glibc 2.32 or higher** (Ubuntu 22.04+, Fedora 36+, macOS, Windows WSL2 with Ubuntu 22.04+).

#### Step 1: Install Globally via npm

```bash
# Install Google Jules CLI globally
npm install -g @google/jules
```

#### Step 2: Verify Installation

```bash
# Check Jules version
jules version
```

**Expected Output:**
```
Version: v0.1.42
Commit: 4bd6b25084aa1af52d6d3979cda31f3a3d99fc04
Date: 2025-12-16T20:26:09Z
OAuth Client ID: 716860248198-t1s5lv1n1msgfoe3dt7vekro8b1fpd9g.apps.googleusercontent.com
```

#### Step 3: Authenticate

```bash
# Login to Google account
jules login
```

This will open your default browser for OAuth authentication.

---

### Method 2: Docker-Based Installation (Dev Containers/Codespaces)

Use this method when running in environments with **older glibc** (Debian 11, older Ubuntu, etc.).

#### Why Docker is Required

The Jules CLI binary requires glibc 2.32+. Many dev containers and Codespaces use Debian 11 (Bullseye) which has glibc 2.31, causing this error:

```
jules: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.34' not found (required by jules)
jules: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.32' not found (required by jules)
```

#### Step 1: Create Shell Function

Add this function to your `~/.bashrc` or `~/.zshrc`:

```bash
# Jules CLI alias (runs via Docker with newer glibc)
jules() {
  docker run -it --rm \
    --network host \
    -v "$(pwd):/workspace" \
    -v "$HOME/.jules:/root/.jules:rw" \
    -w /workspace \
    node:20 npx -y @google/jules "$@"
}
```

#### Step 2: Reload Shell Configuration

```bash
source ~/.bashrc
# or for zsh
source ~/.zshrc
```

#### Step 3: Verify Docker-Based Installation

```bash
jules version
```

**Expected Output:**
```
Version: v0.1.42
Commit: 4bd6b25084aa1af52d6d3979cda31f3a3d99fc04
Date: 2025-12-16T20:26:09Z
OAuth Client ID: 716860248198-t1s5lv1n1msgfoe3dt7vekro8b1fpd9g.apps.googleusercontent.com
```

---

## Authentication Setup

### Local Machine Authentication

On a local machine with a browser, authentication is straightforward:

```bash
jules login
```

1. Browser opens automatically
2. Select your Google account
3. Click "Allow" to grant permissions
4. Browser redirects to `localhost` callback
5. Terminal shows "Login successful!"

#### Verify Authentication

```bash
jules remote list --session
```

---

### Codespaces/Dev Container Authentication

**⚠️ IMPORTANT:** OAuth authentication **cannot be completed directly** in Codespaces/Dev Containers due to localhost callback limitations.

#### The Problem

When running `jules login` in a container:
1. Jules starts a local OAuth callback server on a random port (e.g., `127.0.0.1:43933`)
2. Google OAuth redirects to this localhost URL after authentication
3. The redirect fails because `127.0.0.1` in the browser points to your local machine, not the container

#### Solution: Copy Credentials from Local Machine

##### Step 1: Login on Your Local Machine

On your **local computer** (not in Codespace):

```bash
# Install Jules if not already installed
npm install -g @google/jules

# Login
jules login

# Verify login worked
jules remote list --session
```

##### Step 2: Locate Credentials File

```bash
# Find the credentials file
ls -la ~/.jules/cache/

# View the credentials (do not share publicly!)
cat ~/.jules/cache/oauth_creds.json
```

**Credentials Location by Platform:**

| Platform | Credentials Path |
|----------|-----------------|
| Linux/macOS | `~/.jules/cache/oauth_creds.json` |
| Windows (WSL) | `~/.jules/cache/oauth_creds.json` |
| Windows (PowerShell) | `%USERPROFILE%\.jules\cache\oauth_creds.json` |

##### Step 3: Copy Credentials to Codespace

**Option A: Create file manually in Codespace**

```bash
# In your Codespace terminal
mkdir -p ~/.jules/cache

# Create the credentials file (paste your JSON content)
cat > ~/.jules/cache/oauth_creds.json << 'EOF'
{"access_token":"ya29.xxxxx","token_type":"Bearer","refresh_token":"1//xxxxx","expiry":"2026-01-02T18:20:52.445628903Z","expires_in":3599}
EOF

# Set proper permissions
chmod 600 ~/.jules/cache/oauth_creds.json
```

**Option B: Copy via file upload**

1. Copy `oauth_creds.json` from local machine
2. Upload to Codespace via VS Code file explorer
3. Move to correct location:

```bash
mkdir -p ~/.jules/cache
mv /path/to/uploaded/oauth_creds.json ~/.jules/cache/
chmod 600 ~/.jules/cache/oauth_creds.json
```

##### Step 4: Verify Authentication in Codespace

```bash
jules remote list --session
```

**Expected Output:**
```
           ID                Description                 Repo        Last active     Status
17470084344…  create a new branch and test th…  selvar2/ci-…  1h41m24s ago  Completed
```

---

## Configuration

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `oauth_creds.json` | `~/.jules/cache/` | OAuth tokens and credentials |
| `cli.log` | `~/.jules/cache/` | CLI operation logs |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOME` | User home directory | System default |
| `JULES_CONFIG_DIR` | Custom config directory | `~/.jules` |

### Docker Mount Configuration

When using Docker-based installation, ensure proper volume mounts:

```bash
# Required mounts
-v "$HOME/.jules:/root/.jules:rw"     # Credentials
-v "$(pwd):/workspace"                 # Working directory

# Network configuration
--network host                         # Required for API access
```

---

## Usage Examples

### Basic Commands

```bash
# Launch interactive TUI
jules

# Get help
jules --help

# Show version
jules version
```

### Session Management

```bash
# Create a new coding session (uses current repo)
jules new "write unit tests for the auth module"

# Create session for a specific repository
jules new --repo owner/repo-name "implement feature X"

# Create multiple parallel sessions
jules new --repo owner/repo-name --parallel 3 "write tests"

# List all sessions
jules remote list --session

# List all repositories
jules remote list --repo

# Pull session results
jules remote pull --session 123456

# Pull and apply patch to local repository
jules remote pull --session 123456 --apply

# Clone repo and apply session changes
jules teleport 123456
```

### Advanced Usage

```bash
# Create sessions for each task in a TODO file
cat TODO.md | while IFS= read -r line; do
  jules new "$line"
done

# Create session based on first GitHub issue assigned to you
gh issue list --assignee @me --limit 1 --json title | jq -r '.[0].title' | jules new
```

---

## Troubleshooting Guide

### Installation Issues

#### Error: GLIBC Version Not Found

**Error Message:**
```
jules: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.34' not found (required by jules)
jules: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.32' not found (required by jules)
```

**Cause:** The system's glibc version is older than 2.32.

**Solution:** Use Docker-based installation method:

```bash
# Add to ~/.bashrc
jules() {
  docker run -it --rm \
    --network host \
    -v "$(pwd):/workspace" \
    -v "$HOME/.jules:/root/.jules:rw" \
    -w /workspace \
    node:20 npx -y @google/jules "$@"
}

# Reload shell
source ~/.bashrc
```

**Verification:**
```bash
jules version
```

---

#### Error: Permission Denied During Global Install

**Error Message:**
```
npm error code EACCES
npm error syscall mkdir
npm error path /usr/lib/node_modules/@google
npm error errno -13
npm error Error: EACCES: permission denied
```

**Cause:** Insufficient permissions for global npm installation.

**Solution:**

```bash
# Option 1: Use sudo
sudo npm install -g @google/jules

# Option 2: Configure npm to use a different directory
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g @google/jules
```

**Verification:**
```bash
jules version
```

---

### Authentication Issues

#### Error: Failed to Open Browser

**Error Message:**
```
Failed to open browser: exec: "xdg-open,x-www-browser,www-browser": executable file not found in $PATH. Please navigate to the URL manually.
```

**Cause:** No browser available in the current environment (common in containers/SSH sessions).

**Solution:** Copy the displayed URL and open it manually in your browser:

```
https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=...
```

---

#### Error: OAuth Callback to Localhost Fails

**Error Message:**
Browser shows: `This site can't be reached - 127.0.0.1 refused to connect`

**Cause:** OAuth callback redirects to localhost, but the OAuth server is running inside a container that isn't accessible from your browser.

**Solution:** Authenticate on local machine and copy credentials:

```bash
# On LOCAL machine
jules login
cat ~/.jules/cache/oauth_creds.json

# In Codespace - create credentials file
mkdir -p ~/.jules/cache
cat > ~/.jules/cache/oauth_creds.json << 'EOF'
<paste your credentials JSON here>
EOF
chmod 600 ~/.jules/cache/oauth_creds.json
```

---

#### Error: Google 403 Error in Simple Browser

**Error Message:**
```
403. That's an error.
```

**Cause:** Google blocks OAuth from embedded browsers/webviews (including VS Code's Simple Browser) for security reasons.

**Solution:** Use a regular browser for authentication, not VS Code's Simple Browser. Complete authentication on your local machine and copy credentials.

---

#### Error: Trying to Make a GET Request Without a Valid Client

**Error Message:**
```
Error: failed to list tasks: Trying to make a GET request without a valid client (did you forget to login?)
Tip: you can use "/login" in the TUI or "jules login" in the command line to login
```

**Cause:** One of the following:
1. Not logged in
2. Credentials file missing
3. Credentials in wrong location
4. Token expired and cannot refresh

**Solution:**

##### Check 1: Verify credentials file exists
```bash
ls -la ~/.jules/cache/oauth_creds.json
```

##### Check 2: Verify file is valid JSON
```bash
cat ~/.jules/cache/oauth_creds.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('Valid JSON'); print('Keys:', list(d.keys()))"
```

##### Check 3: Verify correct mount in Docker
```bash
# Ensure you're mounting ~/.jules not ~/.config/jules
docker run --rm -v "$HOME/.jules:/root/.jules:rw" node:20 ls -la /root/.jules/cache/
```

##### Check 4: Re-authenticate if token expired
```bash
# On local machine
jules login

# Copy fresh credentials to Codespace
```

---

#### Error: Credentials in Wrong Directory

**Symptom:** Credentials exist but Jules doesn't recognize them.

**Cause:** Credentials placed in `~/.config/jules/` instead of `~/.jules/cache/`

**Solution:**

```bash
# Check current location
ls -la ~/.config/jules/
ls -la ~/.jules/cache/

# Move to correct location
mkdir -p ~/.jules/cache
mv ~/.config/jules/oauth_creds.json ~/.jules/cache/
chmod 600 ~/.jules/cache/oauth_creds.json
```

**Correct Directory Structure:**
```
~/.jules/
└── cache/
    ├── cli.log
    └── oauth_creds.json
```

---

### Docker Issues

#### Error: Docker Not Found

**Error Message:**
```
docker: command not found
```

**Cause:** Docker is not installed or not in PATH.

**Solution:**

```bash
# Check if Docker is installed
which docker

# If using Dev Container, ensure Docker-in-Docker is enabled
# Add to devcontainer.json:
{
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  }
}
```

---

#### Error: Permission Denied on Docker Socket

**Error Message:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Cause:** Current user is not in the docker group.

**Solution:**

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Restart terminal or run
newgrp docker

# Verify
docker ps
```

---

#### Error: Volume Mount Permission Issues

**Error Message:**
```
touch: cannot touch '/root/.jules/cache/cli.log': Permission denied
```

**Cause:** File ownership mismatch between host and container.

**Solution:**

```bash
# Fix ownership on host
sudo chown -R $(id -u):$(id -g) ~/.jules/

# Or run container as current user
docker run --rm -u $(id -u):$(id -g) ...
```

---

### Network Issues

#### Error: Network Timeout

**Error Message:**
```
Error: network timeout at: https://api.google.com/...
```

**Cause:** Network connectivity issues or firewall blocking.

**Solution:**

```bash
# Test connectivity
curl -v https://accounts.google.com

# If behind proxy, configure environment
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

---

### VS Code / Codespaces Issues

#### Error: Port Not Forwarded

**Symptom:** OAuth callback fails even with correct setup.

**Cause:** OAuth callback port not forwarded in Codespaces.

**Solution:**
1. Check the OAuth URL for the port number (e.g., `127.0.0.1:43933`)
2. Go to **Ports** tab in VS Code
3. Add the port manually
4. Set visibility to **Public**
5. Complete OAuth in external browser

**Note:** This approach rarely works reliably; copying credentials is recommended.

---

## Error Reference Table

| Error Message | Cause | Quick Fix |
|---------------|-------|-----------|
| `GLIBC_2.34 not found` | Old glibc version | Use Docker-based installation |
| `EACCES: permission denied` | npm permission issue | Use `sudo` or configure npm prefix |
| `Failed to open browser` | No browser in environment | Open URL manually |
| `127.0.0.1 refused to connect` | OAuth callback in container | Copy credentials from local |
| `403. That's an error.` | Embedded browser blocked | Use regular browser |
| `GET request without valid client` | Missing/invalid credentials | Check credentials file location |
| `docker: command not found` | Docker not installed | Install Docker or use local install |
| `permission denied...docker socket` | User not in docker group | Add user to docker group |
| `network timeout` | Connectivity issue | Check network/proxy settings |

---

## FAQ

### Q: Can I use Jules without Docker in Codespaces?

**A:** No, if your Codespace runs on Debian 11 or similar with older glibc. The Jules binary requires glibc 2.32+, and Docker provides a compatible environment.

### Q: How long do OAuth tokens last?

**A:** Access tokens expire after ~1 hour, but Jules uses the refresh token to automatically obtain new access tokens. Refresh tokens typically last much longer but may expire after extended periods of inactivity.

### Q: Can I use multiple Google accounts?

**A:** Currently, Jules supports one authenticated account at a time. To switch accounts:

```bash
# Remove existing credentials
rm ~/.jules/cache/oauth_creds.json

# Login with different account
jules login
```

### Q: Is my OAuth token secure?

**A:** The token is stored with file permissions `600` (owner read/write only). However:
- Never share your `oauth_creds.json` file
- Never commit it to version control
- Add `~/.jules/` to your global gitignore

### Q: How do I update Jules?

**A:** 

For direct installation:
```bash
npm update -g @google/jules
```

For Docker-based installation, the alias uses `npx -y` which automatically fetches the latest version.

### Q: Can I use Jules offline?

**A:** No, Jules requires internet connectivity to communicate with Google's API.

---

## Additional Resources

- [Jules CLI npm Package](https://www.npmjs.com/package/@google/jules)
- [Google AI Documentation](https://ai.google.dev/)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)

---

## Persistence Across Codespace Rebuilds

When a Codespace is rebuilt or recreated, customizations outside the workspace folder are lost. This repository includes automatic persistence for Jules.

### Automatic Setup (This Repository)

This repository is pre-configured with:

1. **`setup-jules.sh`** - Automatically runs during Codespace creation
2. **Credentials storage** - Saved in `.devcontainer/secrets/` (gitignored)
3. **Shell configuration** - Jules function added to `.bashrc` automatically

### How It Works

```
.devcontainer/
├── devcontainer.json          # Runs setup-jules.sh on create
├── setup-jules.sh             # Configures Jules CLI
├── secrets/
│   ├── README.md              # Instructions
│   └── jules_oauth_creds.json # Your credentials (gitignored)
└── .gitignore                 # Excludes secrets/ from git
```

### First-Time Setup for Persistence

1. Login on your local machine:
   ```bash
   jules login
   ```

2. Save credentials to workspace:
   ```bash
   # In Codespace
   mkdir -p /workspaces/sample-workflow/.devcontainer/secrets
   cat > /workspaces/sample-workflow/.devcontainer/secrets/jules_oauth_creds.json << 'EOF'
   <paste your credentials JSON here>
   EOF
   ```

3. Run setup script:
   ```bash
   bash /workspaces/sample-workflow/.devcontainer/setup-jules.sh
   ```

Now when you rebuild the Codespace, Jules will be automatically configured with your credentials.

### Alternative: GitHub Codespaces Secrets

For enhanced security, use GitHub Codespaces Secrets:

1. Go to **GitHub** → **Settings** → **Codespaces** → **Secrets**
2. Add secret named `JULES_OAUTH_CREDS` with your JSON credentials
3. Access in Codespace via `$JULES_OAUTH_CREDS` environment variable

---

## Contributing

Found an issue or have a suggestion? Please open an issue or pull request in this repository.

---

## License

This documentation is provided as-is for educational purposes. Google Jules is a product of Google and subject to Google's terms of service.
