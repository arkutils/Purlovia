from tabulate import tabulate


def init_tables():
    return


def display_table(data: list[list], headers: list[str]):
    print(tabulate(data, headers))
