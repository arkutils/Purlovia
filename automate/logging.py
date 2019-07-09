import os
import logging
import logging.config

import yaml


def setup_logging(path='config/logging.yaml', level=logging.INFO):
    '''Setup logging configuration.'''
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=level)

    logging.captureWarnings(True)

    logger = logging.getLogger()
    logging.addLevelName(100, 'STARTUP')
    logger.log(100, '')
    logger.log(100, '-' * 100)
    logger.log(100, '')
