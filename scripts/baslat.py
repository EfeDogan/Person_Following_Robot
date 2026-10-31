#!/usr/bin/env python3
"""Tek Gazebo sahnesini ve hafif arayüzü birlikte başlatır ve temiz kapatır."""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scene', choices=['robot', 'insan', 'takip'], nargs='?', default='insan')
    parser.add_argument('--distance', choices=[0.6, 1.2, 2.0], type=float, default=1.2)
    parser.add_argument('--headless', action='store_true', help='Arayüzsüz kontrol denemesi')
    parser.add_argument('--duration', type=float, help='Belirtilen duvar saati saniyesinde kapat')
    args = parser.parse_args()
    if not shutil.which('gz'):
        parser.error('gz komutu bulunamadı.')
    cache = ROOT / '.cache'
    cache.mkdir(exist_ok=True)
    # Kilit dosyası yerinde kalır; aktif kilit süreç kapanınca otomatik bırakılır.
    lock = (cache / 'gazebo.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('Bu başlatıcıyla açılmış bir sahne zaten çalışıyor. Önce onun terminalinde Ctrl+C yapın.', flush=True)
        return 2
    env = os.environ.copy()
    env['GZ_IP'] = '127.0.0.1'
    # Eski elle açılan örneklerin topic ve servisleriyle karışmasını önler.
    env['GZ_PARTITION'] = 'hri_launcher'
    world = 'hri_baslangic' if args.scene == 'robot' else 'hri_takip'
    path = ROOT / 'worlds' / ('01_robot.sdf' if args.scene == 'robot' else '02_insan.sdf')
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    run = logs / (time.strftime('%Y%m%d-%H%M%S') + f'-{os.getpid()}')
    run.mkdir()
    children, streams = [], []

    def launch(label, command):
        stream = (run / f'{label}.log').open('w')
        streams.append(stream)
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        children.append(process)
        return process

    def stop_on_signal(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop_on_signal)
    try:
        print(f'Sahne: {args.scene} | Günlükler: {run}', flush=True)
        server = launch('sunucu', ['gz', 'sim', '-s', str(path), '-v', '3'])
        if args.scene == 'takip':
            python = ROOT / '.venv' / 'bin' / 'python'
            if not python.exists():
                raise RuntimeError('Bu Mac için .venv bulunamadı; BASLANGIC.md kurulumunu kontrol edin.')
            launch('takip', [str(python), str(ROOT / 'scripts/takip.py'), '--distance', str(args.distance)])
        deadline = time.monotonic() + 25
        while True:
            if server.poll() is not None:
                raise RuntimeError('Fizik sunucusu kapandı; sunucu.log dosyasına bakın.')
            ready = subprocess.run(
                ['gz', 'service', '-s', f'/world/{world}/control',
                 '--reqtype', 'gz.msgs.WorldControl', '--reptype', 'gz.msgs.Boolean',
                 '--timeout', '500', '--req', 'pause: false'],
                env=env, capture_output=True, text=True, timeout=4)
            if 'data: true' in ready.stdout:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Sunucu 25 saniyede hazır olmadı; sunucu.log dosyasına bakın.')
            time.sleep(0.1)
        gui = None
        if not args.headless:
            config = (ROOT / 'gui/hafif.config').read_text()
            config_path = run / 'gui.config'
            config_path.write_text(config)
            gui = launch('arayuz', ['gz', 'sim', '-g', '--gui-config', str(config_path),
                                   '--render-engine-gui', 'ogre2', '-v', '3'])
        print('Simülasyon otomatik başladı; Play düğmesine basmanız gerekmiyor.', flush=True)
        print('Kapatmak için bu terminalde Ctrl+C. Yeni bir sahne için önce bunu kapatın.', flush=True)
        started = time.monotonic()
        while True:
            if server.poll() is not None:
                raise RuntimeError('Sunucu beklenmedik biçimde kapandı; sunucu.log dosyasına bakın.')
            if gui is not None and gui.poll() is not None:
                print(f'Arayüz kapandı (çıkış kodu {gui.returncode}); sunucu da kapatılıyor.', flush=True)
                return 0 if gui.returncode == 0 else 1
            if args.duration is not None and time.monotonic() - started >= args.duration:
                return 0
            time.sleep(0.2)
    except KeyboardInterrupt:
        print('\nSahne kapatılıyor.', flush=True)
        return 0
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        for process in reversed(children):
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGINT)
                    process.wait(timeout=3)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    if process.poll() is None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.wait()
        for stream in streams:
            stream.close()
        lock.close()


if __name__ == '__main__':
    sys.exit(main())
