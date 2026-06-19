"""Multi-identity lifecycle manager."""

import os
import json
import shutil
from pathlib import Path
from typing import Optional, List
import RNS


class IdentityManager:
    def __init__(self, app_config_dir: str):
        self.base_dir = Path(app_config_dir) / "identities"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "index.json"
        self.identities: dict[str, RNS.Identity] = {}
        self._load_index()

    def _load_index(self):
        self._index = {}
        if self.index_path.exists():
            try:
                self._index = json.loads(self.index_path.read_text())
            except:
                self._index = {}

    def _save_index(self):
        self.index_path.write_text(json.dumps(self._index, indent=2))

    def list_identities(self) -> List[dict]:
        results = []
        for hash_hex, info in self._index.items():
            results.append({
                "hash": hash_hex,
                "name": info.get("name", hash_hex[:12]),
                "created": info.get("created", 0),
                "is_active": info.get("is_active", False),
            })
        return results

    def create_identity(self, name: str = "") -> RNS.Identity:
        identity = RNS.Identity()
        hash_hex = identity.hash.hex()
        key_path = self.base_dir / f"{hash_hex}.key"
        identity.to_file(str(key_path))
        self._index[hash_hex] = {
            "name": name or hash_hex[:12],
            "created": __import__("time").time(),
            "key_file": str(key_path),
            "is_active": False,
        }
        self._save_index()
        self.identities[hash_hex] = identity
        return identity

    def load_identity(self, hash_hex: str) -> Optional[RNS.Identity]:
        if hash_hex in self.identities:
            return self.identities[hash_hex]
        info = self._index.get(hash_hex)
        if not info:
            return None
        key_path = info.get("key_file")
        if not key_path or not Path(key_path).exists():
            return None
        try:
            identity = RNS.Identity.from_file(key_path)
            self.identities[hash_hex] = identity
            return identity
        except:
            return None

    def delete_identity(self, hash_hex: str) -> bool:
        info = self._index.pop(hash_hex, None)
        if info:
            key_path = info.get("key_file")
            if key_path and Path(key_path).exists():
                Path(key_path).unlink()
            self.identities.pop(hash_hex, None)
            self._save_index()
            return True
        return False

    def set_active(self, hash_hex: str) -> bool:
        for h in self._index:
            self._index[h]["is_active"] = (h == hash_hex)
        self._save_index()
        return hash_hex in self._index

    def get_active(self) -> Optional[dict]:
        for h, info in self._index.items():
            if info.get("is_active"):
                return {"hash": h, **info}
        return None

    def import_identity(self, key_file_path: str) -> Optional[RNS.Identity]:
        key_path = Path(key_file_path)
        if not key_path.exists():
            return None
        try:
            identity = RNS.Identity.from_file(str(key_path))
            hash_hex = identity.hash.hex()
            dest = self.base_dir / f"{hash_hex}.key"
            shutil.copy2(key_path, dest)
            self._index[hash_hex] = {
                "name": hash_hex[:12],
                "created": __import__("time").time(),
                "key_file": str(dest),
                "is_active": False,
            }
            self._save_index()
            self.identities[hash_hex] = identity
            return identity
        except:
            return None
