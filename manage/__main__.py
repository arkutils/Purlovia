if __name__ == '__main__':
    from utils.flockish import ensure_process_lock, set_lock_path
    set_lock_path("livedata/manage.lock")
    ensure_process_lock()

    from .cli import main
    main()
