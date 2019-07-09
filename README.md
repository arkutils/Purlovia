# Project Purlovia

###### Project Purlovia: digging up Ark data

This project aims to give developers the tools they need to extract species data from the game Ark: Survival Evolved.

**NOTE: This tool is for developers and will not be useful to end-users.**

While still early in development, it aims to:
 * Automate extraction of species information for [ArkSmartBreeding](https://github.com/cadon/ARKStatsExtractor/)
 * Reach feature parity with the previous closed-source extraction solution that is no longer maintained
 * Handle previously impossible creatures such as the Gacha
 * Extend extraction to handle modded species fully

Covering:
 * Species multipliers
 * Breeding times, multipliers
 * Color regions and sets
 * *(future)* Taming stats and foods
 * *(future)* Immobilzed-by list
 * *(future)* Bone damage multipliers

*This project does not contain assets from Ark. It install and updates them via regular Steam tools.*

### Getting Started

Create virtualenv and install the required packages (needs Python 3.7):
```sh
pipenv install --dev
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
* Produce requested data files for ASB in the `output` directory

### Browsing
*(requires a previous full automation run to ensure data is present)*

Browse asset properties with `browseprop.py`, for example:
```sh
python browseprop.py /Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant
```
Or look at the guts of an asset with `browseasset.py`.
