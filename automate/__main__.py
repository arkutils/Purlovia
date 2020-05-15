if __name__ == '__main__':
    import ue.context
    ue.context.disable_metadata()

    from .cli import main
    main()
