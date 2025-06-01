# Placeholder for core profile data structures (Python-based) for the Overclocker's Logbook Module.
class Profile:
    def __init__(self, id, name, type, settings, notes=None):
        self.id = id
        self.name = name
        self.type = type
        self.settings = settings # dict
        self.notes = notes

class SettingsCategory:
    def __init__(self, id, name, description=None):
        self.id = id
        self.name = name
        self.description = description
