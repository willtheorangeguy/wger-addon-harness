"""Portable Docker Compose harness controller; Python 3.10+, no pip dependencies."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

def compose(*args):
    command = ['docker', 'compose', '-f', 'compose.yaml']
    if (ROOT / 'compose.override.yaml').exists():
        command += ['-f', 'compose.override.yaml']
    return subprocess.run(command + list(args), check=True)

def init():
    env = ROOT / '.env'
    if not env.exists():
        content = (ROOT / '.env.example').read_text()
        for key in ['DB_PASSWORD', 'APP_DB_PASSWORD', 'SECRET_KEY', 'ENCRYPTION_KEY']:
            content = content.replace('GENERATE_' + key, secrets.token_hex(32))
        env.write_text(content, encoding='utf-8')
    for name in ['runtime', 'reports']:
        (ROOT / name).mkdir(exist_ok=True)
        (ROOT / name).chmod(0o777)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['up', 'seed', 'test', 'down', 'reset', 'logs', 'status', 'config'])
    parser.add_argument('--yes', action='store_true', help='Required for reset: deletes this project volumes and generated state')
    args = parser.parse_args()
    init()
    if args.command == 'up':
        compose('up', '-d', '--build', '--wait', '--wait-timeout', '600')
        compose('run', '--rm', 'seed')
        compose('--profile', 'addon', 'up', '-d', '--build', '--wait', 'example-addon')
        print('Ready. See README.md for the app URL and demo login.')
    elif args.command == 'seed':
        compose('run', '--rm', 'seed')
    elif args.command == 'test':
        compose('up', '-d', '--build', '--wait', '--wait-timeout', '600')
        compose('run', '--rm', 'seed')
        compose('--profile', 'addon', 'up', '-d', '--build', '--wait', 'example-addon')
        compose('run', '--rm', 'test')
    elif args.command == 'reset':
        if not args.yes:
            parser.error('reset deletes ONLY this harness data; pass --yes to confirm')
        compose('--profile', '*', 'down', '--volumes', '--remove-orphans')
        for folder in ['runtime', 'reports']:
            for p in (ROOT / folder).iterdir():
                if p.is_file() and p.name != '.gitkeep':
                    p.unlink()
        print('Data removed. Run: python harness.py up')
    elif args.command == 'down':
        compose('--profile', '*', 'down', '--remove-orphans')
    elif args.command == 'logs':
        compose('logs', '--tail', '100', '-f')
    elif args.command == 'status':
        compose('--profile', '*', 'ps', '-a')
    else:
        compose('config', '--quiet')

if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f'Harness failed: {error}', file=sys.stderr)
        sys.exit(1)
