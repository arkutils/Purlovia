if __name__ == '__main__':
    from utils.flockish import ensure_process_lock, set_lock_path
    set_lock_path("livedata/automate.lock")
    ensure_process_lock()

    import ue.context
    ue.context.disable_metadata()

    from .cli import main
    main()
