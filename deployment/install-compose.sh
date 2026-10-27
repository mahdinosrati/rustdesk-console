#!/bin/sh
set -eu
umask 077

fail() { printf '%s\n' "$*" >&2; exit 1; }
usage() {
  echo 'Usage: sudo sh install-compose.sh --host rd.example.com | --console-only'
  echo 'Fresh local Linux installation in /opt/rustdesk-console-compose.'
  echo 'Installs Docker if absent (Debian/Ubuntu); keeps existing installations untouched.'
}

host=
case "${1:-}" in
  --host)
    [ "$#" = 2 ] || { usage; exit 1; }
    host=$2
    case "$host" in ''|*[!a-zA-Z0-9.-]*|-*|.*) fail 'Use a DNS name or IPv4 address, without scheme, port or path.' ;; esac
    ;;
  --console-only) [ "$#" = 1 ] || { usage; exit 1; } ;;
  --help|-h) usage; exit 0 ;;
  *) usage; exit 1 ;;
esac

[ "$(uname -s)" = Linux ] || fail 'A Linux Docker host is required.'
[ "$(id -u)" = 0 ] || fail 'Run with sudo or as root.'
root=/opt/rustdesk-console-compose
[ ! -e "$root" ] && [ ! -L "$root" ] || fail "Existing installation path: $root. Nothing overwritten. See docs/README-FA.md."
[ -z "${DOCKER_HOST:-}${DOCKER_CONTEXT:-}${COMPOSE_FILE:-}${COMPOSE_PROJECT_NAME:-}${COMPOSE_PROFILES:-}" ] || fail 'Unset Docker/Compose environment overrides before installing.'
command -v curl >/dev/null 2>&1 || fail 'Install curl first (sudo apt-get update && sudo apt-get install -y curl ca-certificates).'

tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
trap 'exit 1' HUP INT TERM
if ! command -v docker >/dev/null 2>&1; then
  [ -r /etc/os-release ] || fail 'Install Docker Engine and Compose v2 first.'
  . /etc/os-release
  case "$ID" in debian|ubuntu) ;; *) fail 'Automatic Docker installation supports Debian/Ubuntu only.' ;; esac
  echo 'Installing Docker Engine with the official get.docker.com installer...'
  curl -fsSL --retry 3 https://get.docker.com -o "$tmp/docker.sh"
  sh "$tmp/docker.sh"
fi
docker compose version >/dev/null || fail 'Install the Docker Compose v2 plugin first.'
[ "$(docker context inspect --format '{{.Endpoints.docker.Host}}')" = unix:///var/run/docker.sock ] || fail 'Use the local rootful Docker context.'
[ "$(docker info --format '{{.OSType}}')" = linux ] || fail 'A running Linux Docker daemon is required.'
case "$(docker info --format '{{json .SecurityOptions}}')" in *rootless*) fail 'Rootless Docker is not supported by the managed updater.' ;; esac
command -v openssl >/dev/null 2>&1 || fail 'Install openssl first.'

# Keep both deployment files at the same reviewed revision.
source_url=https://raw.githubusercontent.com/mahdinosrati/rustdesk-console/3c568c7c32f829cd85de4823cd63cf92ab12ed78
for file in docker-compose.yml docker-compose.override.yml; do
  curl -fsSL --retry 3 "$source_url/$file" -o "$tmp/$file"
done
jwt=$(openssl rand -hex 32)
password=$(openssl rand -hex 24)
token=$(openssl rand -hex 32)
{
  printf 'CONSOLE_INSTALL_DIR=%s\nJWT_SECRET=%s\nADMIN_PASSWORD=%s\n' "$root" "$jwt" "$password"
  if [ -n "$host" ]; then
    printf 'COMPOSE_PROFILES=server\nRUSTDESK_RELAY_ADDRESS=%s:21117\nSERVER_MANAGEMENT_TOKEN=%s\n' "$host" "$token"
  fi
} > "$tmp/.env"
mkdir "$root"
chmod 755 "$root"
cp "$tmp/docker-compose.yml" "$tmp/docker-compose.override.yml" "$tmp/.env" "$root/"
mkdir "$root/data"
chown 1000:1000 "$root/data"
cd "$root"
# Persisted values must also be the values seen by the updater on later runs.
unset JWT_SECRET ADMIN_PASSWORD CONSOLE_INSTALL_DIR DB_TYPE DB_HOST DB_PORT DB_USERNAME DB_PASSWORD DB_DATABASE DEVICE_CLONE_ISOLATION SYSTEM_UPDATE_MYSQL_EXCLUSIVE_SCHEMA SERVER_MANAGEMENT_TOKEN RUSTDESK_RELAY_ADDRESS
docker compose config --quiet
docker compose pull
docker compose up -d --wait --wait-timeout 180
printf '\nContainers started. Console: http://%s:21114\n' "${host:-SERVER_IP}"
printf 'Username: databk\nRead the generated password with: sudo cat %s/.env\n' "$root"
echo 'See docs/README-FA.md for HTTPS, client setup, server management and updater registration checks.'
