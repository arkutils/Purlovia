git fetch
git reset --hard origin/live
pipenv sync --bare
pipenv run python -m automate --live
