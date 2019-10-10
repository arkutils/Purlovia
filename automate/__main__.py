if __name__ == '__main__':
    import ue.context
    ue.context.disable_metadata()

    from .run import main
    main()
