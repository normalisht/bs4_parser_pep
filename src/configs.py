import argparse
import configparser
import logging
from logging.handlers import RotatingFileHandler

from constants import (BASE_DIR, LOGGER_CONFIG_FILE, DEFAULT_LOG_FORMAT,
                       DEFAULT_DT_FORMAT)


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


def configure_logging():
    config = configparser.ConfigParser()
    config.read(LOGGER_CONFIG_FILE)

    if config.has_section('Logger'):
        logging_config = config['Logger']
        log_dir = BASE_DIR / logging_config.get('log_dir', 'logs')
        log_dir.mkdir(exist_ok=True)
        log_file = (
                log_dir / (f'{(logging_config.get("log_file_name", "parser"))}'
                           f'.log')
        )
        rotating_handler = RotatingFileHandler(
            log_file,
            maxBytes=int(logging_config.get('max_bytes', '1_000_000')),
            backupCount=int(logging_config.get('backup_count', '5')),
            encoding=logging_config.get('encoding', 'utf-8')
        )
        rotating_handler.setFormatter(
            logging.Formatter(
                fmt=logging_config.get('log_format', DEFAULT_LOG_FORMAT),
                datefmt=logging_config.get('dt_format', DEFAULT_DT_FORMAT)
            )
        )
        logger = logging.getLogger(
            logging_config.get('logger_name', 'Main logger')
        )
        logger.setLevel(logging_config.get('log_level', 'INFO'))
        logger.addHandler(rotating_handler)
        logger.addHandler(logging.StreamHandler())

        return logger

    log_dir = BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'parser.log'
    rotating_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=5, encoding='utf-8'
    )
    rotating_handler.setFormatter(
        logging.Formatter(fmt=DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DT_FORMAT)
    )
    logger = logging.getLogger('Main logger')
    logger.setLevel(logging.INFO)
    logger.addHandler(rotating_handler)
    logger.addHandler(logging.StreamHandler())

    return logger
