## Development

The project uses `pipenv` to manage both the virtual Python environment and the required modules. Requires Python 3.7.

To get setup:
```sh
pipenv sync --dev
pipenv shell
```

IPython is supported throughout the data system, and each of the `*_i.py` files are designed to used interactively in a live session for experimentation. This works both on IPython's command-line and in VSCode's interactive Python window.

## Editor

Any editor could be used, but VSCode is preconfigured to:
* Format on save using `yapf` and `isort`
* Lint using `flake8` and `mypy`
* Run tests using `PyTest`

## Testing

There are a few `PyTest` tests present, but many have been removed to avoid using game assets. Some still require a game install and the presence of the PurloviaTEST mod.

Run the tests in the editor or using:
```sh
pipenv run tests
```

Test files **and** functions must be prefixed `test_`, but `doctest`-style tests are also discovered and run automatically anywhere in the code.

## Formatting

The project *strictly* uses `yapf` for formatting and `isort` for import ordering, and VSCode is set to do both of these on save.

To check these project-wide:
```sh
pipenv run isort
pipenv run yapf
```

To actively fix issues project-wide:
```sh
pipenv run fix-isort
pipenv run fix-yapf
```

## Linting

The project is checked with `flake8` and `mypy`, and the results should be clean before commit.

```sh
pipenv run flake
pipenv run mypy
```

Both checkers are enabled in VSCode.

## Pre-commit Checks

A pre-commit hook has been introduced to verify `flake8` and `mypy` cleanliness, along with some other basic and fast checks. No changes will be made to project files during commit hooks.

Useful commands:
```sh
pre-commit install          # install this hook in your local repo
pre-commit run              # run pre-commit checks against currently *staged* files
pre-commit run --all-files  # run pre-commit checks against all files
```
