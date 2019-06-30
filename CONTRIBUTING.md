## Development

The project uses `pipenv` to manage both the virtual Python environment and the required modules.

To get setup:
```sh
pipenv install --dev
```

IPython is supported throughout the data system, and each of the `*_i.py` files are designed to used interactively in a live session for experimentation. This works both on IPython's command-line and in VSCode's interactive Python window.

## Editor

Any editor could be used, but VSCode is preconfigured to:
* Format on save using `yapf`
* Lint using `pylint` and `mypy`
* Run tests using `PyTest`

## Testing

There are a few `PyTest` tests present, but many have been removed to avoid using game assets.

Run the tests in the editor or using:
```sh
pytest
```

Test files **and** functions must be prefixed `test_`, but `doctest`-style tests are discovered and run automatically anywhere in the code.

## Formatting

The project *strictly* uses `yapf` for formatting, and VSCode is set to format on save.

## Linting

The project attempts to follow the recommendations of `pylint`, but given this is an experimental/prototyping project we aren't strict about it.

The project is also checked with `mypy`. Some areas of the code have extensive typing in place while others have very little.

```sh
mypy .
```

Both linters are enabled in VSCode.
