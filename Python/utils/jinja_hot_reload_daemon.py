#!/usr/bin/env python3
"""
Jinja Hot Reload Monitor - Daemon Runner
Скрипт для запуска мониторинга как фоновой службы
"""

import os
import sys
import time
import signal
import daemon
import lockfile
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Импортируем основной модуль
sys.path.insert(0, str(Path(__file__).parent))
from jinja_hot_reload_v2_0_0 import JinjaHotReloadMonitor


class JinjaHotReloadDaemon:
    """Класс для запуска мониторинга как daemon процесса"""

    def __init__(self, base_path: str, pid_file: str, log_file: str):
        """
        Инициализация daemon

        Args:
            base_path: Базовый путь для мониторинга
            pid_file: Путь к PID файлу
            log_file: Путь к файлу логов
        """
        self.base_path = base_path
        self.pid_file = pid_file
        self.log_file = log_file
        self.monitor = None

        # Настройка логирования в файл
        self.setup_logging()

    def setup_logging(self):
        """Настройка логирования в файл"""
        # Создаём директорию для логов если не существует
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Настраиваем логирование
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('JinjaHotReloadDaemon')

    def start(self):
        """Запуск daemon процесса"""
        # Проверяем, не запущен ли уже daemon
        if Path(self.pid_file).exists():
            self.logger.error(f"PID файл {self.pid_file} уже существует. Daemon возможно уже запущен.")
            sys.exit(1)

        self.logger.info("Запуск Jinja Hot Reload Daemon...")

        # Настройка контекста daemon
        context = daemon.DaemonContext(
            working_directory=str(Path.home()),
            umask=0o002,
            pidfile=lockfile.FileLock(self.pid_file),
            files_preserve=[
                sys.stdout,
                sys.stderr,
            ],
            signal_map={
                signal.SIGTERM: self.shutdown,
                signal.SIGINT: self.shutdown,
            }
        )

        # Запуск в контексте daemon
        with context:
            self.run()

    def run(self):
        """Основной цикл работы daemon"""
        try:
            # Записываем PID
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))

            self.logger.info(f"Daemon запущен с PID: {os.getpid()}")
            self.logger.info(f"Мониторинг директории: {self.base_path}")
            self.logger.info(f"Логи пишутся в: {self.log_file}")

            # Создаём и запускаем монитор
            self.monitor = JinjaHotReloadMonitor(self.base_path)

            # Запускаем мониторинг (блокирующий вызов)
            self.monitor.start()

        except Exception as e:
            self.logger.error(f"Ошибка в daemon: {e}", exc_info=True)
            self.cleanup()
            sys.exit(1)

    def stop(self):
        """Остановка daemon процесса"""
        if not Path(self.pid_file).exists():
            self.logger.error("PID файл не найден. Daemon не запущен.")
            return

        # Читаем PID
        with open(self.pid_file, 'r') as f:
            pid = int(f.read())

        # Отправляем сигнал остановки
        try:
            os.kill(pid, signal.SIGTERM)
            self.logger.info(f"Отправлен сигнал остановки процессу {pid}")

            # Ждём завершения процесса
            for _ in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(1)
                except ProcessLookupError:
                    break

            # Удаляем PID файл
            Path(self.pid_file).unlink(missing_ok=True)
            self.logger.info("Daemon остановлен")

        except ProcessLookupError:
            self.logger.warning("Процесс уже остановлен")
            Path(self.pid_file).unlink(missing_ok=True)
        except Exception as e:
            self.logger.error(f"Ошибка при остановке: {e}")

    def restart(self):
        """Перезапуск daemon процесса"""
        self.logger.info("Перезапуск daemon...")
        self.stop()
        time.sleep(2)
        self.start()

    def status(self):
        """Проверка статуса daemon"""
        if not Path(self.pid_file).exists():
            print("❌ Daemon не запущен")
            return False

        with open(self.pid_file, 'r') as f:
            pid = int(f.read())

        try:
            # Проверяем, жив ли процесс
            os.kill(pid, 0)
            print(f"✅ Daemon запущен (PID: {pid})")

            # Показываем информацию из лога
            if Path(self.log_file).exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        # Показываем последние 5 строк лога
                        print("\n📄 Последние записи в логе:")
                        for line in lines[-5:]:
                            print(f"  {line.strip()}")

            return True

        except ProcessLookupError:
            print("❌ Daemon не запущен (процесс не найден)")
            Path(self.pid_file).unlink(missing_ok=True)
            return False

    def shutdown(self, signum, frame):
        """Обработчик сигналов завершения"""
        self.logger.info(f"Получен сигнал {signum}, завершение работы...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Очистка ресурсов"""
        if self.monitor:
            self.monitor.stop()

        # Удаляем PID файл
        Path(self.pid_file).unlink(missing_ok=True)
        self.logger.info("Очистка завершена")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Jinja Hot Reload Monitor - Daemon Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s start    - Запустить daemon
  %(prog)s stop     - Остановить daemon
  %(prog)s restart  - Перезапустить daemon
  %(prog)s status   - Проверить статус daemon
        """
    )

    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status'],
        help='Действие для выполнения'
    )

    parser.add_argument(
        '--base-path',
        default='/Users/username/Documents/front-middle-schema/.JSON',
        help='Базовый путь для мониторинга (по умолчанию: /Users/username/Documents/front-middle-schema/.JSON)'
    )

    parser.add_argument(
        '--pid-file',
        default='/tmp/jinja_hot_reload.pid',
        help='Путь к PID файлу (по умолчанию: /tmp/jinja_hot_reload.pid)'
    )

    parser.add_argument(
        '--log-file',
        default='/tmp/jinja_hot_reload.log',
        help='Путь к файлу логов (по умолчанию: /tmp/jinja_hot_reload.log)'
    )

    args = parser.parse_args()

    # Проверяем наличие модуля python-daemon
    try:
        import daemon
        import lockfile
    except ImportError:
        print("❌ Отсутствует модуль python-daemon")
        print("📦 Установите: pip install python-daemon")
        sys.exit(1)

    # Создаём экземпляр daemon
    daemon_runner = JinjaHotReloadDaemon(
        base_path=args.base_path,
        pid_file=args.pid_file,
        log_file=args.log_file
    )

    # Выполняем действие
    if args.action == 'start':
        daemon_runner.start()
    elif args.action == 'stop':
        daemon_runner.stop()
    elif args.action == 'restart':
        daemon_runner.restart()
    elif args.action == 'status':
        daemon_runner.status()


if __name__ == '__main__':
    main()