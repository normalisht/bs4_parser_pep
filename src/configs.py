import argparse
import configparser
import logging
from logging.handlers import RotatingFileHandler

from constants import BASE_DIR, LOGGER_CONFIG_FILE


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=('pretty', 'file'),
        help='Дополнительные способы вывода данных'
    )
    return parser


def get_logger():
    config = configparser.ConfigParser()
    config.read(LOGGER_CONFIG_FILE)
    logging_config = config['Logger']

    log_dir = BASE_DIR / logging_config.get('log_dir', 'logs')
    log_dir.mkdir(exist_ok=True)
    log_file = (
            log_dir / f'{(logging_config.get("log_file_name", "parser"))}.log'
    )
    rotating_handler = RotatingFileHandler(
        log_file,
        maxBytes=int(logging_config.get('max_bytes', '1_000_000')),
        backupCount=int(logging_config.get('backup_count', '5')),
        encoding=logging_config.get('encoding', 'utf-8')
    )
    rotating_handler.setFormatter(
        logging.Formatter(
            fmt=logging_config.get(
                'log_format', '"%(asctime)s - [%(levelname)s] - %(message)s"'
            ),
            datefmt=logging_config.get('dt_format', '%d.%m.%Y %H:%M:%S')
        )
    )
    logger = logging.getLogger(
        logging_config.get('logger_name', 'Main logger')
    )
    logger.setLevel(logging_config.get('log_level', 'INFO'))
    logger.addHandler(rotating_handler)
    logger.addHandler(logging.StreamHandler())

    return logger
