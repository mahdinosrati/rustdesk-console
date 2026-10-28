#!/usr/bin/env python3
"""Offline SQLite backup/restore for the standard local Compose installation."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path('/opt/rustdesk-console-compose')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compose(*args):
    return subprocess.check_output(['docker', 'compose', '--project-directory', str(ROOT),
                                    *args], cwd=ROOT, text=True).strip()


def check_idle(root):
    require(not (root / 'updater-state/bootstrap-pending.json').exists(),
            'ثبت updater ناتمام است؛ ابتدا آن را تکمیل کنید.')
    maintenance = root / 'updater-maintenance/maintenance.json'
    if maintenance.exists():
        require(json.loads(maintenance.read_text()).get('active') is False,
                'حالت maintenance فعال است؛ ابتدا update/recovery را تکمیل کنید.')
    for file in (root / 'updater-state/jobs').glob('*.json'):
        job = json.loads(file.read_text())
        require(job['view']['status'] in ('succeeded', 'failed', 'rolled_back'),
                'عملیات update/recovery ناتمام است؛ بکاپ انجام نشد.')


def archive_members(archive):
    members = archive.getmembers()
    names = set()
    for item in members:
        path = PurePosixPath(item.name)
        require(not path.is_absolute() and '..' not in path.parts and
                path.parts and path.parts[0] == ROOT.name and
                (item.isfile() or item.isdir()) and item.name not in names,
                'آرشیو نامعتبر است: مسیر، لینک یا نوع فایل غیرمجاز.')
        require(not (item.mode & 0o7000), 'بیت دسترسی ویژه در آرشیو مجاز نیست.')
        names.add(item.name)
    for name in ('.env', 'docker-compose.yml', 'docker-compose.override.yml'):
        require(f'{ROOT.name}/{name}' in names, f'فایل {name} در بکاپ وجود ندارد.')
    return members


def backup(destination):
    import fcntl

    require(ROOT.is_dir() and not ROOT.is_symlink(), 'مسیر نصب معتبر نیست.')
    destination = Path(destination).absolute()
    require(not destination.exists() and not destination.is_symlink(), 'فایل خروجی از قبل وجود دارد.')
    require(not destination.resolve().is_relative_to(ROOT.resolve()), 'بکاپ باید بیرون پوشهٔ نصب باشد.')
    config = json.loads(compose('config', '--format', 'json'))
    require(config['services']['rustdesk-console'].get('environment', {}).get('DB_TYPE', 'sqlite') == 'sqlite',
            'این ابزار فقط SQLite را پشتیبانی می‌کند؛ MySQL به بکاپ مستقل نیاز دارد.')
    if 'updater' in config['services']:
        require((ROOT / 'updater-state/installation.json').is_file(),
                'ابتدا ثبت updater و نصب اولیه را تکمیل کنید.')
    (ROOT / 'updater-state').mkdir(mode=0o700, exist_ok=True)
    with (ROOT / 'updater-state/execution.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_idle(ROOT)
        running = compose('ps', '--status', 'running', '--services').split()
        try:
            if running:
                compose('stop', *running)
            check_idle(ROOT)
            def filter_member(item):
                if item.name.endswith(('/execution.lock', '/control.lock')):
                    return None
                require(item.isfile() or item.isdir(),
                        f'بکاپ لینک‌ها و فایل‌های ویژه پشتیبانی نمی‌شود: {item.name}')
                return item
            with destination.open('xb') as output:
                os.chmod(destination, 0o600)
                with tarfile.open(fileobj=output, mode='w:gz', dereference=False) as archive:
                    archive.add(ROOT, arcname=ROOT.name, filter=filter_member)
            print(f'بکاپ ساخته شد: {destination}')
        except BaseException:
            # A partial archive must never be presented as a usable backup.
            if destination.exists():
                destination.unlink()
            raise
        finally:
            if running:
                compose('start', *running)


def restore(source):
    require(not ROOT.exists() and not ROOT.is_symlink(),
            'بازیابی فقط روی مسیر نصب خالی مجاز است؛ نصب موجود بازنویسی نمی‌شود.')
    containers = subprocess.check_output(['docker', 'ps', '-aq', '--filter',
        f'label=com.docker.compose.project.working_dir={ROOT}'], text=True).strip()
    require(not containers, 'کانتینرهای نصب قبلی هنوز وجود دارند؛ بازیابی روی میزبان تازه انجام شود.')
    # Validate before extracting; never extract links or arbitrary paths as root.
    with tarfile.open(source, 'r:gz') as archive:
        members = archive_members(archive)
        with tempfile.TemporaryDirectory(prefix='.console-restore-', dir=ROOT.parent) as staging:
            options = {'filter': 'fully_trusted'} if hasattr(tarfile, 'fully_trusted_filter') else {}
            archive.extractall(staging, members=members, numeric_owner=True, **options)
            restored = Path(staging) / ROOT.name
            env = (restored / '.env').read_text()
            require(f'CONSOLE_INSTALL_DIR={ROOT}' in env.splitlines(), 'مسیر نصب در بکاپ با مسیر استاندارد یکسان نیست.')
            require(not any(line.startswith('DB_TYPE=') and line != 'DB_TYPE=sqlite'
                            for line in env.splitlines()), 'بازیابی خودکار فقط برای SQLite است.')
            check_idle(restored)
            os.chmod(restored / '.env', 0o600)
            # Root was checked before extraction and is never replaced intentionally.
            require(not ROOT.exists() and not ROOT.is_symlink(), 'مسیر نصب در حین بازیابی ایجاد شد.')
            restored.rename(ROOT)
    print(f'بازیابی تمام شد. سرویس‌ها هنوز اجرا نشده‌اند. اجرا: cd {ROOT} && sudo docker compose up -d --wait')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['backup', 'restore'])
    parser.add_argument('archive', help='Absolute archive path; backup never overwrites an existing file')
    args = parser.parse_args()
    require(sys.platform == 'linux' and os.geteuid() == 0, 'ابزار را روی لینوکس با sudo اجرا کنید.')
    require(not any(os.environ.get(key) for key in os.environ
                    if key.startswith(('COMPOSE_', 'DOCKER_'))), 'متغیرهای محیطی Docker/Compose را پاک کنید.')
    require(Path(args.archive).is_absolute(), 'مسیر آرشیو باید مطلق باشد.')
    endpoint = subprocess.check_output(['docker', 'context', 'inspect', '--format',
                                       '{{.Endpoints.docker.Host}}'], text=True).strip()
    require(endpoint == 'unix:///var/run/docker.sock', 'Docker باید روی همین میزبان اجرا شود.')
    if args.command == 'backup':
        backup(args.archive)
    else:
        restore(args.archive)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as error:
        print(f'خطا: {error}', file=sys.stderr)
        sys.exit(1)
