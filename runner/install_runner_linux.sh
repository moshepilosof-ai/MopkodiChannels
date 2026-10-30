#!/usr/bin/env bash
# Installs a GitHub Actions self-hosted runner on this Linux computer (x64 or ARM64, e.g. Raspberry Pi) for the
# MopkodiChannels repo, as a systemd service. The refresh workflows then run HERE (Israeli address).
#
# Usage:  bash install_runner_linux.sh <registration token>
# The token comes from GitHub: repo Settings -> Actions -> Runners -> New self-hosted runner (valid one hour).
# Needs: git, python3, curl, tar. Do not run as root (the runner refuses); sudo is used only for the service.
set -euo pipefail
TOKEN="${1:-}"
if [ -z "$TOKEN" ]; then echo "usage: $0 <registration token>"; exit 1; fi
REPO_URL="https://github.com/moshepilosof-ai/MopkodiChannels"
RUNNER_VER="2.338.2"
case "$(uname -m)" in
  x86_64) ARCH=x64 ;;
  aarch64|arm64) ARCH=arm64 ;;
  armv7l) ARCH=arm ;;
  *) echo "unsupported arch $(uname -m)"; exit 1 ;;
esac
DIR="$HOME/actions-runner-mopkodi"
mkdir -p "$DIR" && cd "$DIR"
if [ ! -f run.sh ]; then
  echo "downloading runner $RUNNER_VER ($ARCH)..."
  curl -fsSL -o runner.tgz "https://github.com/actions/runner/releases/download/v${RUNNER_VER}/actions-runner-linux-${ARCH}-${RUNNER_VER}.tar.gz"
  tar xzf runner.tgz && rm runner.tgz
  if [ -x bin/installdependencies.sh ]; then sudo ./bin/installdependencies.sh || true; fi
fi
echo "registering with $REPO_URL ..."
./config.sh --url "$REPO_URL" --token "$TOKEN" --name "$(hostname)-israel" --labels israel --unattended --replace
sudo ./svc.sh install
sudo ./svc.sh start
echo
echo "Runner installed as a service. Check: GitHub repo -> Settings -> Actions -> Runners (should be Idle)."
echo "To remove later:  cd $DIR && sudo ./svc.sh uninstall && ./config.sh remove --token <removal token>"
