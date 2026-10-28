import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load('console-setup')
backup = load('console-backup')


class ConsoleToolsTest(unittest.TestCase):
    def test_https_and_persian_are_opt_in(self):
        source = Path(__file__).parent.parent / 'docker-compose.yml'
        original = source.read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'docker-compose.yml'
            path.write_text(original)
            setup.configure_persian(directory, 'a' * 40)
            setup.configure_https(directory, 'console.example.com')
            result = path.read_text()
            self.assertNotIn("'21114:80'", result)
            self.assertNotIn('\n  updater:', result)
            self.assertIn('Dockerfile.persian', result)
            self.assertIn("'443:443'", result)
            self.assertIn('reverse_proxy rustdesk-console-web:80',
                          (Path(directory) / 'Caddyfile').read_text())
            self.assertEqual(source.read_text(), original)
            with self.assertRaises(ValueError):
                setup.configure_https(directory, 'example.com { import /etc/passwd }')

    def test_archive_rejects_paths_and_links(self):
        for name, kind in [('../outside', tarfile.REGTYPE),
                           ('/etc/passwd', tarfile.REGTYPE),
                           (backup.ROOT.name + '/link', tarfile.SYMTYPE),
                           (backup.ROOT.name + '/hardlink', tarfile.LNKTYPE)]:
            data = io.BytesIO()
            with tarfile.open(fileobj=data, mode='w') as archive:
                item = tarfile.TarInfo(name)
                item.type = kind
                item.linkname = '/etc/passwd'
                archive.addfile(item)
            data.seek(0)
            with tarfile.open(fileobj=data) as archive:
                with self.assertRaises(ValueError):
                    backup.archive_members(archive)

    @unittest.skipUnless(__import__('sys').platform == 'linux', 'Linux flock and ownership')
    def test_backup_restore_keeps_data_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'rustdesk-console-compose'
            root.mkdir()
            (root / 'data').mkdir()
            (root / 'data/important.txt').write_text('preserve me')
            (root / '.env').write_text(f'CONSOLE_INSTALL_DIR={root}\nDB_TYPE=sqlite\n')
            for name in ('docker-compose.yml', 'docker-compose.override.yml'):
                (root / name).write_text('services: {}\n')
            calls = []
            def compose(*args):
                calls.append(args)
                if args[0] == 'config':
                    return json.dumps({'services': {'rustdesk-console': {'environment': {'DB_TYPE': 'sqlite'}}}})
                if args[0] == 'ps':
                    return 'rustdesk-console'
                return ''
            archive = Path(directory) / 'backup.tar.gz'
            with patch.object(backup, 'ROOT', root), patch.object(backup, 'compose', compose):
                backup.backup(archive)
                self.assertIn(('stop', 'rustdesk-console'), calls)
                self.assertIn(('start', 'rustdesk-console'), calls)
                with self.assertRaises(ValueError):
                    backup.restore(archive)
                saved = root.with_name('original')
                root.rename(saved)
                with patch.object(backup.subprocess, 'check_output', return_value=''):
                    backup.restore(archive)
                self.assertEqual((root / 'data/important.txt').read_text(), 'preserve me')
                self.assertEqual((root / '.env').stat().st_mode & 0o777, 0o600)

    def test_active_update_prevents_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'updater-state/jobs').mkdir(parents=True)
            job = root / 'updater-state/jobs/job.json'
            job.write_text(json.dumps({'view': {'status': 'running'}}))
            with self.assertRaises(ValueError):
                backup.check_idle(root)
            job.write_text(json.dumps({'view': {'status': 'succeeded'}}))
            (root / 'updater-maintenance').mkdir()
            (root / 'updater-maintenance/maintenance.json').write_text('{"active":false}')
            backup.check_idle(root)


if __name__ == '__main__':
    unittest.main()
