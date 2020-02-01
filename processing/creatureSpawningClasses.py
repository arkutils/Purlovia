# Helper for creatureSpawningMaps.py

class SpawnFrequency:
    def __init__(self, path, frequency):
        self.path = path
        self.frequency = frequency

class SpawnRectangle:
    def __init__(self, x1, y1, x2, y2, cave, untameable):
        self.x = x1
        self.y = y1
        self.w = x2 - x1
        self.h = y2 - y1
        self.cave = cave
        self.untameable = untameable

class SpawnPoint:
    def __init__(self, x, y, cave, untameable):
        self.x = x
        self.y = y
        self.cave = cave
        self.untameable = untameable
