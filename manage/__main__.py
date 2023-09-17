if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('manage')

    from pathlib import Path
    Path('livedata').mkdir(exist_ok=True)

    from utils.flockish import ensure_process_lock, set_lock_path
    set_lock_path("livedata/manage.lock")
    ensure_process_lock()

    from .cli import main
    try:
        main()
    except KeyboardInterrupt:
        logger.error('Interrupted by Ctrl-C')
