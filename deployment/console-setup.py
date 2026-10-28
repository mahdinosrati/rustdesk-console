#!/usr/bin/env python3
"""Preflight and optional HTTPS configuration for fresh Compose installations."""
import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def domain(value):
    require(len(value) <= 253 and re.fullmatch(
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,63}", value), "دامنهٔ HTTPS معتبر نیست؛ بدون پروتکل و پورت وارد کنید.")
    return value


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def preflight(host, https_domain):
    require(not any(value for key, value in os.environ.items()
                    if key.startswith(('DOCKER_', 'COMPOSE_'))),
            'متغیرهای محیطی Docker/Compose را پیش از نصب پاک کنید.')
    require(platform.machine().lower() in ("x86_64", "amd64", "aarch64", "arm64"),
            "معماری پشتیبانی نمی‌شود؛ amd64 یا arm64 لازم است.")
    require(shutil.disk_usage('/opt').free >= 2 * 1024**3,
            "کمتر از ۲ گیگابایت فضای آزاد در /opt وجود دارد.")
    tcp = [21114] if not https_domain else [80, 443]
    if host:
        tcp += list(range(21115, 21120))
    ports = {(p, "tcp") for p in tcp}
    if host:
        ports.add((21116, "udp"))
    for name in filter(None, [host, https_domain]):
        try:
            addresses = sorted({item[4][0] for item in socket.getaddrinfo(name, None)})
        except socket.gaierror as error:
            raise ValueError(f"DNS برای {name} پاسخ نمی‌دهد.") from error
        print(f"DNS {name}: {', '.join(addresses)}")
    for port, protocol in sorted(ports):
        kind = socket.SOCK_STREAM if protocol == 'tcp' else socket.SOCK_DGRAM
        with socket.socket(socket.AF_INET, kind) as listener:
            try:
                listener.bind(('0.0.0.0', port))
            except OSError as error:
                raise ValueError(f"پورت {port}/{protocol} اشغال است.") from error
    if shutil.which('docker'):
        info = json.loads(docker('info', '--format', '{{json .}}'))
        require(info.get('OSType') == 'linux' and not any(
            'rootless' in option for option in info.get('SecurityOptions', [])),
            "Docker باید محلی، لینوکسی و بدون rootless باشد.")
        require(docker('context', 'inspect', '--format', '{{.Endpoints.docker.Host}}')
                == 'unix:///var/run/docker.sock', "Docker context باید محلی باشد.")
        docker('compose', 'version')
        containers = docker('ps', '-aq').split()
        if containers:
            for container in json.loads(docker('inspect', *containers)):
                require(not host or container.get('Name') not in ('/hbbs', '/hbbr'),
                        "کانتینر hbbs یا hbbr از قبل وجود دارد؛ نصب قبلی را بررسی کنید.")
                if container.get('State', {}).get('Running'):
                    bindings = container.get('HostConfig', {}).get('PortBindings') or {}
                    for key, values in bindings.items():
                        protocol = key.split('/')[-1]
                        for binding in values or []:
                            require((int(binding['HostPort']), protocol) not in ports,
                                    f"پورت Docker اشغال است: {binding['HostPort']}/{protocol}")
    else:
        require(platform.freedesktop_os_release().get('ID') in ('ubuntu', 'debian'),
                'ابتدا Docker Engine و Compose را روی این توزیع نصب کنید.')
        print('Docker نصب نیست؛ نصب واقعی آن را آماده خواهد کرد.')
    for url in ('https://raw.githubusercontent.com/mahdinosrati/rustdesk-console/main/docker-compose.yml',
                'https://registry-1.docker.io/v2/'):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                response.read(1)
        except urllib.error.HTTPError as error:
            if error.code != 401 or 'registry-1.docker.io' not in url:
                raise ValueError(f"دریافت فایل یا دسترسی رجیستری ناموفق است: {url}") from error
    print("بررسی اولیه موفق بود. مسیر DNS به IP واقعی سرور و دسترسی خارجی فایروال را نیز بررسی کنید.")


def configure_https(directory, name):
    domain(name)
    path = Path(directory) / 'docker-compose.yml'
    original = path.read_text()
    require(original.count("      - '21114:80'") == 1,
            "ساختار پورت Compose ناشناخته است؛ تغییری انجام نشد.")
    # Caddy reaches the web service over the private Compose network.
    updated = original.replace("    ports:\n      - '21114:80'\n", '')
    services, networks = updated.rsplit('\nnetworks:', 1)
    service = '''
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./caddy/data:/data
      - ./caddy/config:/config
    depends_on:
      - rustdesk-console-web
'''
    (Path(directory) / 'Caddyfile').write_text(
        f'{name} {{\n    reverse_proxy rustdesk-console-web:80\n}}\n')
    path.write_text(services + '\n' + service + '\nnetworks:' + networks)


def configure_persian(directory, revision):
    require(re.fullmatch(r'[a-f0-9]{40}', revision), 'نسخهٔ رابط وب معتبر نیست.')
    path = Path(directory) / 'docker-compose.yml'
    original = path.read_text()
    require(original.count('    image: databk/rustdesk-console-web:latest') == 1,
            'ایمیج رابط وب در Compose شناخته‌شده نیست.')
    updated = original.replace('    image: databk/rustdesk-console-web:latest',
        '    image: rustdesk-console-web:persian\n'
        '    build:\n'
        f'      context: https://github.com/mahdinosrati/rustdesk-console-web.git#{revision}\n'
        '      dockerfile: Dockerfile.persian')
    before, updater = updated.split('\n  updater:\n', 1)
    _, after = updater.split('\n  # Optional RustDesk server', 1)
    path.write_text(before + '\n  # Optional RustDesk server' + after)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'https', 'persian'])
    parser.add_argument('--host', default='')
    parser.add_argument('--https-domain', default='')
    parser.add_argument('--directory')
    parser.add_argument('--revision')
    args = parser.parse_args()
    if args.https_domain:
        domain(args.https_domain)
    if args.command == 'check':
        preflight(args.host, args.https_domain)
    elif args.command == 'https':
        require(args.directory and args.https_domain, 'مسیر و دامنه لازم است.')
        configure_https(args.directory, args.https_domain)
    else:
        require(args.directory and args.revision, 'مسیر و نسخه لازم است.')
        configure_persian(args.directory, args.revision)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'خطا: {error}', file=sys.stderr)
        sys.exit(1)
