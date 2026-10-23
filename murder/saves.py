"""Atomic saves with three previous valid versions and automatic recovery."""
import json
import math
import os
import shutil
import tempfile

BACKUPS = 3


def validate_state(state):
    if not isinstance(state, dict) or type(state.get("day")) is not int or state["day"] < 1:
        raise ValueError("Save has no valid game day")
    for field in ("agents", "room_items", "npcs"):
        if not isinstance(state.get(field), dict):
            raise ValueError(f"Save has no valid {field}")
    # Early saves predate custom casts; upgrade_state supplies the original cast.
    if "cast" in state and (not isinstance(state["cast"], dict) or any(not isinstance(c, dict) for c in state["cast"].values())):
        raise ValueError("Save has no valid cast")
    if not isinstance(state["npcs"].get("neovi"), dict):
        raise ValueError("Save has no valid housemaid state")
    if any(not isinstance(items, dict) for items in state["room_items"].values()):
        raise ValueError("Save has invalid room items")
    for agent in state["agents"].values():
        if not isinstance(agent, dict) or not all(k in agent for k in ("room", "hp", "sanity", "inv", "aff")):
            raise ValueError("Save has an invalid participant")
        if not isinstance(agent["room"], str) or not isinstance(agent["inv"], dict) or not isinstance(agent["aff"], dict):
            raise ValueError("Save has invalid participant belongings or relationships")
        if any(not isinstance(agent[k], (int, float)) or not math.isfinite(agent[k]) for k in ("hp", "sanity")):
            raise ValueError("Save has invalid participant health")
    return state


class SaveStore:
    def __init__(self, directory):
        self.directory = directory
        self.path = os.path.join(directory, "current.json")
        self.recovery = None

    def backup(self, index):
        return os.path.join(self.directory, f"current.backup-{index}.json")

    @staticmethod
    def read(path):
        with open(path, encoding="utf-8") as f:
            return validate_state(json.load(f))

    def _write(self, path, state):
        fd, tmp = tempfile.mkstemp(prefix="current-", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=1)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def save(self, state):
        # Serialize first, so an unserializable new state cannot rotate the backups.
        json.dumps(state)
        validate_state(state)
        try:
            previous = self.read(self.path)
        except (OSError, ValueError):
            previous = None
        if previous is not None:
            for i in range(BACKUPS, 1, -1):
                try:
                    older = self.read(self.backup(i - 1))
                except (OSError, ValueError):
                    continue
                self._write(self.backup(i), older)
            self._write(self.backup(1), previous)
        self._write(self.path, state)

    def load(self):
        try:
            return self.read(self.path)
        except (OSError, ValueError) as original:
            for i in range(1, BACKUPS + 1):
                try:
                    state = self.read(self.backup(i))
                except (OSError, ValueError):
                    continue
                if os.path.exists(self.path):
                    shutil.copyfile(self.path, os.path.join(self.directory, "current.corrupt.json"))
                self._write(self.path, state)
                self.recovery = {"backup": i, "day": state["day"], "reason": type(original).__name__}
                return state
            raise ValueError("Cannot read the current save or any valid backup. Preserve state/ and restore a named save.") from original

    def info(self):
        versions = []
        for i in range(1, BACKUPS + 1):
            try:
                state = self.read(self.backup(i))
            except (OSError, ValueError):
                continue
            versions.append({"backup": i, "day": state["day"]})
        return {"backups": versions, "recovered": self.recovery}
