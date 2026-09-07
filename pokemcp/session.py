import re
from os import path, mkdir, remove, listdir
from shutil import copy

pokemonEmeraldSaveRegex = r"pokemon.*emerald.*\.sav$"

def find_save(gamesFolder: str, regexString: str):
    for file in listdir(gamesFolder):
        if re.match(regexString, file, re.IGNORECASE):
            return file
    return None

class Session:
    def __init__(self, projectPath: str, sessionName: str):
        self.projectPath = projectPath
        self.sessionName = sessionName

        if not path.exists(path.join(projectPath, "sessions")):
            mkdir(path.join(self.projectPath, "sessions"))

        self.resourcesPath = path.join(projectPath, "resources")
        self.sessionPath = path.join(projectPath, "sessions", sessionName)
        self.gamesPath = path.join(projectPath, "games")
        self.saveUpdateIndicator = path.join(self.gamesPath, "savefileUpdated")

        self.journalPath = path.join(self.sessionPath, "journal.md")

        if not path.exists(self.sessionPath):
            mkdir(self.sessionPath)
            copy(path.join(self.resourcesPath, "journal.md"), self.journalPath)

        if find_save(self.gamesPath, pokemonEmeraldSaveRegex):
            self.gameSavePath = path.join(self.gamesPath, find_save(self.gamesPath, pokemonEmeraldSaveRegex))
        else:
            self.gameSavePath = None

        if find_save(self.sessionPath, pokemonEmeraldSaveRegex):
            self.sessionSavePath = path.join(self.sessionPath, find_save(self.sessionPath, pokemonEmeraldSaveRegex))
        else:
            self.sessionSavePath = None

        if(self.gameSavePath):
            overwrite = input("[WARNING] There is currently a save file in the games folder, overwrite with session save? [Y/N]: ")
            if overwrite.lower() != 'y':
                print("[WARNING] Continuing with existing save, this could overwrite the current session's save if it does not belong to this session.")
                return

            try:
                remove(self.gameSavePath)
            except PermissionError:
                print("[ERROR] Cannot overwrite the save currently in the games folder, ensure the ROM isn't currently loaded in the emulator.")
                exit()

        if(self.sessionSavePath):
            if path.exists(self.sessionSavePath):
                copy(self.sessionSavePath, self.gamesPath)

        return

    def update_save(self):
        if not path.exists(self.saveUpdateIndicator):
            return

        if not self.gameSavePath:
            self.gameSavePath = path.join(self.projectPath, find_save(self.gamesPath, pokemonEmeraldSaveRegex))

        copy(self.gameSavePath, self.sessionPath)
        remove(self.saveUpdateIndicator)
        return