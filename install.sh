#!/usr/bin/env bash
#
# SCP:SL Health Monitor — Installer (Go Edition)
#
# Installs:
#   - Go monitor agent + web dashboard + Prometheus metrics
#
# Detects Linux distro and package manager for dependency hints.
#
set -Eeuo pipefail

base_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { printf '\033[0;36m[INFO]\033[0m  %s\n' "$*"; }
warn()  { printf '\033[0;33m[WARN]\033[0m  %s\n' "$*"; }
error() { printf '\033[0;31m[ERR ]\033[0m %s\n' "$*" >&2; }
ok()    { printf '\033[0;32m[OK]\033[0m   %s\n' "$*"; }

require_root() {
    if [[ "$(id -u)" -ne 0 ]]; then
        error "This installer must be run as root (use sudo)."
        exit 1
    fi
}

detect_distro() {
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release 2>/dev/null || true
        echo "${ID:-unknown}"
    elif [[ -f /etc/redhat-release ]]; then
        echo "rhel"
    else
        echo "unknown"
    fi
}

detect_pkg_manager() {
    for mgr in apt dnf yum zypper pacman apk; do
        command -v "$mgr" &>/dev/null && { echo "$mgr"; return; }
    done
    echo ""
}

detect_arch() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64)  echo "amd64" ;;
        aarch64) echo "arm64" ;;
        armv7l)  echo "arm" ;;
        *)       echo "$arch" ;;
    esac
}

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
require_root

DISTRO=$(detect_distro)
PKG_MANAGER=$(detect_pkg_manager)
ARCH=$(detect_arch)

echo ""
info "SCP:SL Health Monitor — Installer"
info "Detected distro:  ${DISTRO}"
info "Package manager:  ${PKG_MANAGER:-none found}"
info "Architecture:     ${ARCH}"
echo ""

# Check required commands
MISSING_CMDS=()
for cmd in systemctl ss df awk grep logger; do
    if ! command -v "$cmd" &>/dev/null; then
        MISSING_CMDS+=("$cmd")
    fi
done

if [[ ${#MISSING_CMDS[@]} -gt 0 ]]; then
    warn "Missing required commands: ${MISSING_CMDS[*]}"
    case "$PKG_MANAGER" in
        apt)    warn "  Install with: apt install -y procps iproute2 util-linux" ;;
        dnf|yum) warn "  Install with: ${PKG_MANAGER} install -y procps-ng iproute util-linux" ;;
        zypper) warn "  Install with: zypper install -y procps iproute2 util-linux" ;;
        pacman) warn "  Install with: pacman -S --noconfirm procps-ng iproute2 util-linux" ;;
        apk)    warn "  Install with: apk add --no-cache procps iproute2 util-linux" ;;
        *)      warn "  Please install: procps, iproute2, util-linux" ;;
    esac
    read -rp "Continue anyway? [y/N] " yn
    [[ "$yn" =~ ^[Yy]$ ]] || { error "Aborted by user."; exit 1; }
fi

# ---------------------------------------------------------------------------
# Install Go monitor agent
# ---------------------------------------------------------------------------
AGENT_BINARY="/usr/local/sbin/server-health-monitor-agent"
AGENT_SERVICE="/etc/systemd/system/server-health-monitor-agent.service"
AGENT_CONFIG="/etc/server-health-monitor-agent.conf"

info ""
info "=== Installing Go Monitor Agent ==="

# Find the binary
AGENT_SRC=""
if [[ -f "$base_dir/build/server-health-monitor-agent" ]]; then
    AGENT_SRC="$base_dir/build/server-health-monitor-agent"
elif [[ -f "$base_dir/server-health-monitor-agent" ]]; then
    AGENT_SRC="$base_dir/server-health-monitor-agent"
fi

if [[ -n "$AGENT_SRC" ]]; then
    info "Installing binary → ${AGENT_BINARY}"
    install -o root -g root -m 0755 "$AGENT_SRC" "$AGENT_BINARY"
else
    warn "Pre-built binary not found. Looking for Go toolchain..."
    if command -v go &>/dev/null; then
        info "Compiling from source (this may take a minute)..."
        cd "$base_dir"
        go build -ldflags="-s -w" -o /tmp/server-health-monitor-agent ./cmd/agent
        install -o root -g root -m 0755 /tmp/server-health-monitor-agent "$AGENT_BINARY"
        rm -f /tmp/server-health-monitor-agent
    else
        warn "Go compiler not found and no pre-built binary available."
        warn "Skipping agent installation because no binary or Go compiler was found."
        warn "To install the Go agent, either:"
        warn "  1. Install Go and re-run: bash install.sh"
        warn "  2. Or copy a pre-built binary to the same directory and re-run"
        AGENT_SKIPPED=1
    fi
fi

if [[ -z "${AGENT_SKIPPED:-}" ]]; then
    # systemd unit
    if [[ -f "$base_dir/deploy/systemd/server-health-monitor-agent.service" ]]; then
        info "Installing agent service → ${AGENT_SERVICE}"
        install -o root -g root -m 0644 \
            "$base_dir/deploy/systemd/server-health-monitor-agent.service" "$AGENT_SERVICE"
    fi

    # Config
    if [[ ! -f "$AGENT_CONFIG" ]]; then
        if [[ -f "$base_dir/server-health-monitor-agent.conf.example" ]]; then
            info "Deploying agent config → ${AGENT_CONFIG}"
            install -o root -g root -m 0640 "$base_dir/server-health-monitor-agent.conf.example" "$AGENT_CONFIG"
        fi
    else
        info "Agent config already exists, leaving untouched."
    fi

    info "Enabling and starting agent..."
    systemctl enable --now server-health-monitor-agent.service 2>/dev/null || warn "Agent start failed, check: journalctl -u server-health-monitor-agent"
fi

# ---------------------------------------------------------------------------
# Finalize
# ---------------------------------------------------------------------------
info ""
info "=== Finalizing ==="

systemctl daemon-reload

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo ""
echo "============================================================"
echo "  Installation complete!"
echo "============================================================"
echo ""
echo "  Services:"
if [[ -z "${AGENT_SKIPPED:-}" ]]; then
    echo "    - server-health-monitor-agent.service  (web dashboard + Prometheus)"
    echo ""
    echo "  Dashboard:   http://${SERVER_IP:-<server-ip>}:8080/"
    echo "  API:         http://${SERVER_IP:-<server-ip>}:8080/api/status"
    echo "  Prometheus:  http://${SERVER_IP:-<server-ip>}:8080/metrics"
else
    echo "    - Go agent: skipped (no binary / no Go compiler)"
fi
echo ""
echo "  Config files:"
if [[ -z "${AGENT_SKIPPED:-}" ]]; then
    echo "    - ${AGENT_CONFIG}"
fi
echo ""
echo "  Useful commands:"
echo "    systemctl status server-health-monitor-agent.service"
echo "    journalctl -t server-health-monitor -n 50"
echo "    journalctl -u server-health-monitor-agent -n 50"
echo ""
echo "  Notifications: edit config file to set"
echo "    - serverchan_key (方糖, 微信推送)"
echo "    - webhook_url (Discord / Slack)"
echo ""
echo "============================================================"
