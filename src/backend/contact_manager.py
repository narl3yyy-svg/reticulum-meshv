"""Persistent contact management with discovery tracking."""

import json
import time
from pathlib import Path
from typing import List, Optional


class Contact:
    def __init__(self, hash_hex: str, name: str = "", notes: str = ""):
        self.hash_hex = hash_hex
        self.name = name or hash_hex[:12]
        self.notes = notes
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.is_favourite = False
        self.is_trusted = False

    def to_dict(self) -> dict:
        return {
            "hash": self.hash_hex,
            "name": self.name,
            "notes": self.notes,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "is_favourite": self.is_favourite,
            "is_trusted": self.is_trusted,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Contact":
        c = cls(d["hash"], d.get("name", ""), d.get("notes", ""))
        c.first_seen = d.get("first_seen", time.time())
        c.last_seen = d.get("last_seen", time.time())
        c.is_favourite = d.get("is_favourite", False)
        c.is_trusted = d.get("is_trusted", False)
        return c


class ContactManager:
    def __init__(self, app_config_dir: str):
        self.data_path = Path(app_config_dir) / "contacts.json"
        self.contacts: dict[str, Contact] = {}
        self._load()

    def _load(self):
        if self.data_path.exists():
            try:
                data = json.loads(self.data_path.read_text())
                for item in data:
                    c = Contact.from_dict(item)
                    self.contacts[c.hash_hex] = c
            except:
                pass

    def _save(self):
        data = [c.to_dict() for c in self.contacts.values()]
        self.data_path.write_text(json.dumps(data, indent=2))

    def add_or_update(self, hash_hex: str, name: str = "", notes: str = "") -> Contact:
        if hash_hex in self.contacts:
            c = self.contacts[hash_hex]
            if name:
                c.name = name
            if notes:
                c.notes = notes
            c.last_seen = time.time()
        else:
            c = Contact(hash_hex, name or hash_hex[:12], notes)
            self.contacts[hash_hex] = c
        self._save()
        return c

    def remove(self, hash_hex: str) -> bool:
        if hash_hex in self.contacts:
            del self.contacts[hash_hex]
            self._save()
            return True
        return False

    def get(self, hash_hex: str) -> Optional[Contact]:
        return self.contacts.get(hash_hex)

    def get_all(self) -> List[Contact]:
        return list(self.contacts.values())

    def search(self, query: str) -> List[Contact]:
        q = query.lower()
        return [
            c for c in self.contacts.values()
            if q in c.name.lower() or q in c.hash_hex.lower()
        ]

    def touch(self, hash_hex: str):
        if hash_hex in self.contacts:
            self.contacts[hash_hex].last_seen = time.time()
            self._save()
        else:
            self.add_or_update(hash_hex)

    def set_trusted(self, hash_hex: str, trusted: bool) -> bool:
        c = self.get(hash_hex)
        if c:
            c.is_trusted = trusted
            self._save()
            return True
        return False

    def check_trusted(self, hash_hex: str) -> bool:
        c = self.get(hash_hex)
        return c.is_trusted if c else False

    def get_trusted(self) -> list:
        return [c for c in self.contacts.values() if c.is_trusted]
