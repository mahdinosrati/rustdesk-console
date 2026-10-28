#!/bin/sh
set -eu
umask 077

fail() { printf '%s\n' "$*" >&2; exit 1; }
usage() {
  echo 'Usage: sudo sh install-compose.sh (--host rd.example.com | --console-only) [--https-domain console.example.com] [--persian-web] [--check]'
  echo 'Fresh local Linux installation in /opt/rustdesk-console-compose.'
  echo 'Installs Docker if absent (Debian/Ubuntu); keeps existing installations untouched.'
}

host=
https_domain=
check_only=false
persian_web=false
mode=
while [ "$#" -gt 0 ]; do
case "$1" in
  --host)
    [ "$#" -ge 2 ] && [ -z "$mode" ] || { usage; exit 1; }
    mode=server
    host=$2
    case "$host" in ''|*[!a-zA-Z0-9.-]*|-*|.*) fail 'Use a DNS name or IPv4 address, without scheme, port or path.' ;; esac
    shift
    ;;
  --console-only) [ -z "$mode" ] || { usage; exit 1; }; mode=console ;;
  --https-domain) [ "$#" -ge 2 ] || { usage; exit 1; }; https_domain=$2; shift ;;
  --check) check_only=true ;;
  --persian-web) persian_web=true ;;
  --help|-h) usage; exit 0 ;;
  *) usage; exit 1 ;;
esac
shift
done
[ -n "$mode" ] || { usage; exit 1; }

[ "$(uname -s)" = Linux ] || fail 'A Linux Docker host is required.'
[ "$(id -u)" = 0 ] || fail 'Run with sudo or as root.'
root=/opt/rustdesk-console-compose
[ ! -e "$root" ] && [ ! -L "$root" ] || fail "Existing installation path: $root. Nothing overwritten. See docs/README-FA.md."
[ -z "${DOCKER_HOST:-}${DOCKER_CONTEXT:-}${COMPOSE_FILE:-}${COMPOSE_PROJECT_NAME:-}${COMPOSE_PROFILES:-}" ] || fail 'Unset Docker/Compose environment overrides before installing.'
command -v curl >/dev/null 2>&1 || fail 'Install curl first (sudo apt-get update && sudo apt-get install -y curl ca-certificates).'
command -v python3 >/dev/null 2>&1 || fail 'ابتدا python3 را نصب کنید: sudo apt-get install -y python3'
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || fail 'Python 3.10 یا جدیدتر لازم است.'
command -v openssl >/dev/null 2>&1 || fail 'ابتدا openssl را نصب کنید: sudo apt-get install -y openssl'

tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
trap 'exit 1' HUP INT TERM
tools_url=https://raw.githubusercontent.com/mahdinosrati/rustdesk-console/main/deployment
curl -fsSL --retry 3 "$tools_url/console-setup.py" -o "$tmp/console-setup.py"
python3 "$tmp/console-setup.py" check --host "$host" --https-domain "$https_domain"
if [ "$check_only" = true ]; then exit 0; fi
curl -fsSL --retry 3 "$tools_url/console-backup.py" -o "$tmp/console-backup.py"
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
cp "$tmp/console-backup.py" "$root/console-backup.py"
if [ "$persian_web" = true ]; then
  python3 "$tmp/console-setup.py" persian --directory "$root" --revision ffdbe338c46c683312f6d30355870d3d7203c17e
fi
if [ -n "$https_domain" ]; then
  python3 "$tmp/console-setup.py" https --directory "$root" --https-domain "$https_domain"
fi
mkdir "$root/data"
chown 1000:1000 "$root/data"
cd "$root"
# Persisted values must also be the values seen by the updater on later runs.
unset JWT_SECRET ADMIN_PASSWORD CONSOLE_INSTALL_DIR DB_TYPE DB_HOST DB_PORT DB_USERNAME DB_PASSWORD DB_DATABASE DEVICE_CLONE_ISOLATION SYSTEM_UPDATE_MYSQL_EXCLUSIVE_SCHEMA SERVER_MANAGEMENT_TOKEN RUSTDESK_RELAY_ADDRESS
docker compose config --quiet
if [ "$persian_web" = true ]; then
  docker compose build rustdesk-console-web
  docker compose pull --ignore-buildable
else
  docker compose pull
fi
docker compose up -d --wait --wait-timeout 180
if [ -z "$https_domain" ]; then
  printf '\nContainers started. Console: http://%s:21114\n' "${host:-SERVER_IP}"
fi
printf 'Username: databk\nRead the generated password with: sudo cat %s/.env\n' "$root"
if [ -n "$https_domain" ]; then
  echo "در حال بررسی گواهی HTTPS برای $https_domain ..."
  curl -fsS --retry 12 --retry-delay 5 --retry-all-errors --connect-timeout 5 --max-time 10 \
    --resolve "$https_domain:443:127.0.0.1" "https://$https_domain/" -o /dev/null \
    || fail 'کانتینرها اجرا شدند ولی HTTPS تأیید نشد؛ DNS، پورت‌های 80/443 و لاگ caddy را بررسی کنید.'
  printf 'HTTPS آماده است: https://%s\n' "$https_domain"
fi
if [ "$persian_web" = true ]; then
  echo 'نسخهٔ فارسی آماده است؛ از منوی زبان، فارسی را انتخاب کنید. این نصب به‌روزرسانی دستی دارد.'
fi
echo 'See docs/README-FA.md for HTTPS, client setup, server management and updater registration checks.'
