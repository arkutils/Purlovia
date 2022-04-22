# Project Purlovia

###### Project Purlovia: digging up Ark data

This project aims to give developers the tools they need to extract data from the game Ark: Survival Evolved.

**NOTE: This tool is for developers and will not be useful to end-users.**

While the project will be in perpetual development, it aims to:

* Automate extraction of species information for [ArkSmartBreeding](https://github.com/cadon/ARKStatsExtractor/)
* Automate extraction of other information for [the Ark wiki](https://ark.wiki.gg/)
* Reach feature parity with the previous closed-source extraction solution that is no longer maintained
* Handle previously impossible creatures such as the Gacha
* Extend extraction to handle modded species fully

Covering:

* Species multipliers
* Breeding times, multipliers
* Color regions and sets
* Bone damage multipliers
* Immobilized-by list
* *(future)* Taming stats and foods

*This project does not contain assets from Ark. It installs and updates them via regular Steam tools.*

### Requirements

* Git
* Python 3.10 (probably compatible with later but untested)
* pipenv

### Getting Started

1. Make sure you have the [Obelisk](https://github.com/arkutils/Obelisk) git repo cloned to `output`
   ```sh
   git clone https://github.com/arkutils/Obelisk.git output
   ```

2. Create virtualenv and install the required packages (needs Python 3.10):
    (suggest setting PIPENV_VENV_IN_PROJECT to 1 globally or creating an empty `.venv` directory in the project first)

   ```sh
   pipenv install --deploy --dev
   pipenv shell
   ```

### Full Automation Run

Tailor `config.ini` to your needs, then run:

```sh
python -m automate
```

This will:

* Ensure SteamCmd is downloaded
* Install/update a copy of the game (server version) using SteamCmd
* Install/update the mods listed in `config.ini`
* Produce requested data files in the `output` directory

Add `--help` for information on more options.

### Browsing Asset Contents

**NOTE: Requires a previous full automation run to ensure data is present**

Browse asset properties in a basic UI with `browseprop.py`, for example:

```sh
python browseprop.py Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant
```

Or look at the complete guts of an asset with `browseasset.py`.

### Search Inheritance Hierarchy

**NOTE: Requires a previous full automation run to ensure data is present**

Search for entries in the inheritance hierarchy, for example:

```sh
$ python uegrep.py --subs Dodo_Character_BP
/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP.Dodo_Character_BP_C
  /Game/Genesis/Dinos/MissionVariants/Gauntlet/Bog/Dodo_Character_BP_Aggressive.Dodo_Character_BP_Aggressive_C
  /Game/Genesis/Dinos/MissionVariants/Gauntlet/Bog/Dodo_Character_BP_Aggressive_Large.Dodo_Character_BP_Aggressive_Large_C
  /Game/Genesis/Dinos/MissionVariants/Sport/Dodo_Character_BP_Basketball.Dodo_Character_BP_Basketball_C
  /Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant.Dodo_Character_BP_Aberrant_C
```
