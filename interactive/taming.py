from ark.mod import get_official_mods
from ark.taming_food.datatypes import *
from ark.taming_food.debug import *
from ark.taming_food.evaluate import *
from ark.taming_food.items import *
from ark.taming_food.simplify import *
from ark.taming_food.species import *
from tests.common import *

CORE_MODIDS = ['', *set(get_official_mods()) - {'111111111'}]
