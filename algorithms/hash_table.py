"""Custom hash table - implemented from scratch (no ``dict`` for the core
storage; Python ``dict`` is only used for the serialised view).

DAA facts
---------
Hash function : djb2 (h = h*33 + c) - cheap, good avalanche on short keys.
Chaining      : average O(1), worst O(n) when every key collides.
Open addressing (linear probing): average O(1) as long as load factor
               alpha < 0.75, worst O(n).
Rehash (doubling) at alpha > 0.75 keeps the expected chain length < 1.

Both strategies are implemented so the Algorithm Lab can *show* collision
resolution side by side:

    HashTable(strategy="chaining")   -> buckets hold python lists
    HashTable(strategy="open")       -> buckets hold a single key/value
                                        and collisions probe linearly

Used by NexaSearch for keyword -> document-set mapping and O(1) document
lookup by id.
"""

from __future__ import annotations

import time
from typing import Any, Iterable

TOMBSTONE = "\x00deleted\x00"


def djb2_hash(key: str) -> int:
    """Classic djb2 string hash (h = h * 33 + c)."""
    h = 5381
    for char in key:
        h = ((h << 5) + h + ord(char)) & 0xFFFFFFFF
    return h


def polynomial_hash(key: str, base: int = 31, mod: int = 1_000_003) -> int:
    """Alternative hash (base-31 rolling polynomial) used for comparison."""
    h = 0
    for char in key:
        h = (h * base + ord(char)) % mod
    return h


class HashTableChaining:
    """Separate-chaining hash table: each bucket is a list of (key, value)."""

    strategy = "chaining"

    def __init__(self, capacity: int = 16, hash_func=djb2_hash) -> None:
        self.hash_func = hash_func
        self.capacity = max(4, int(capacity))
        self.buckets: list[list[tuple[str, Any]]] = [[] for _ in range(self.capacity)]
        self.count = 0
        self.collisions = 0
        self.rehashes = 0
        self.max_chain_length = 0

    # -- internals -----------------------------------------------------
    def _index(self, key: str) -> int:
        return self.hash_func(key) % self.capacity

    def _find_in_chain(self, key: str) -> tuple[int, Any] | None:
        chain = self.buckets[self._index(key)]
        for position, (existing, value) in enumerate(chain):
            if existing == key:
                return position, value
        return None

    def _resize(self, new_capacity: int) -> None:
        old = self.buckets
        self.capacity = new_capacity
        self.buckets = [[] for _ in range(self.capacity)]
        self.count = 0
        self.rehashes += 1
        for chain in old:
            for key, value in chain:
                self.put(key, value, _rehash_pass=True)

    # -- public API ----------------------------------------------------
    def put(self, key: str, value: Any = None, _rehash_pass: bool = False) -> dict:
        """Insert/update. Returns a trace dict (used by the visualizer)."""
        if key is None:
            raise ValueError("Hash table keys cannot be None")
        key = str(key)
        steps: list[dict] = []
        bucket = self._index(key)
        steps.append({
            "action": "hash",
            "bucket": bucket,
            "description": f"hash('{key}') = {self.hash_func(key)}, index = {self.hash_func(key)} % {self.capacity} = {bucket}",
        })
        found = self._find_in_chain(key)
        chain = self.buckets[bucket]
        if found is not None:
            position, _ = found
            chain[position] = (key, value)
            steps.append({"action": "update", "bucket": bucket,
                          "description": "key already present -> value replaced"})
            return {"bucket": bucket, "steps": steps, "action": "updated", "collisions": 0}

        collided = len(chain) > 0
        if collided:
            self.collisions += 1
            steps.append({
                "action": "collision", "bucket": bucket,
                "description": f"bucket {bucket} occupied -> chain a new node "
                               f"(chaining resolves the collision, average O(1))",
            })
        chain.append((key, value))
        self.count += 1
        self.max_chain_length = max(self.max_chain_length, len(chain))
        steps.append({"action": "insert", "bucket": bucket,
                      "description": f"appended to bucket {bucket} (chain length {len(chain)})"})

        load = self.load_factor
        if load > 0.75:
            new_capacity = self.capacity * 2
            steps.append({"action": "rehash", "bucket": bucket,
                          "description": f"load factor {load:.2f} > 0.75 -> rehash "
                                         f"{self.capacity} to {new_capacity} buckets"})
            self._resize(new_capacity)
        return {"bucket": bucket, "steps": steps, "action": "inserted",
                "collisions": 1 if collided else 0}

    def get(self, key: str, default: Any = None) -> Any:
        found = self._find_in_chain(str(key))
        return found[1] if found else default

    def contains(self, key: str) -> bool:
        return self._find_in_chain(str(key)) is not None

    def delete(self, key: str) -> bool:
        bucket = self._index(str(key))
        chain = self.buckets[bucket]
        for position, (existing, _) in enumerate(chain):
            if existing == str(key):
                chain.pop(position)
                self.count -= 1
                return True
        return False

    # -- introspection -------------------------------------------------
    @property
    def load_factor(self) -> float:
        return self.count / self.capacity if self.capacity else 0.0

    def snapshot(self) -> list[list[str]]:
        """Bucket view for the front-end table widget."""
        return [[k for k, _ in chain] for chain in self.buckets]

    def stats(self) -> dict:
        lengths = [len(chain) for chain in self.buckets]
        return {
            "strategy": self.strategy,
            "capacity": self.capacity,
            "size": self.count,
            "load_factor": round(self.load_factor, 3),
            "collisions": self.collisions,
            "rehashes": self.rehashes,
            "max_chain_length": max(lengths) if lengths else 0,
            "avg_chain_length": round(sum(lengths) / len(lengths), 3) if lengths else 0,
            "empty_buckets": sum(1 for length in lengths if length == 0),
        }


class HashTableOpenAddressing:
    """Linear-probing open addressing with tombstones and doubling."""

    strategy = "open_addressing"

    def __init__(self, capacity: int = 16, hash_func=djb2_hash) -> None:
        self.hash_func = hash_func
        self.capacity = max(4, int(capacity))
        self.slots: list[tuple[str, Any] | None | str] = [None] * self.capacity
        self.count = 0
        self.collisions = 0
        self.probes = 0
        self.rehashes = 0

    def _index(self, key: str) -> int:
        return self.hash_func(key) % self.capacity

    def _probe(self, key: str, insert: bool = False) -> int | None:
        """Linear probing: h, h+1, h+2 ... mod capacity.

        A deleted slot holds ``TOMBSTONE`` rather than ``None``: clearing the
        slot to ``None`` would truncate the probe chain and hide keys that sit
        further along it.
        """
        start = self._index(key)
        first_free: int | None = None
        for offset in range(self.capacity):
            slot = (start + offset) % self.capacity
            self.probes += 1
            current = self.slots[slot]
            if current is TOMBSTONE:
                if first_free is None:
                    first_free = slot
                continue
            if current is None:
                return (first_free if first_free is not None else slot) if insert else None
            if current[0] == key:
                return slot
            self.collisions += 1
        return first_free if insert else None

    def put(self, key: str, value: Any = None, _rehash_pass: bool = False) -> dict:
        key = str(key)
        start = self._index(key)
        steps: list[dict] = [{
            "action": "hash", "bucket": start,
            "description": f"hash('{key}') % {self.capacity} = {start}",
        }]
        before = self.collisions
        slot = self._probe(key, insert=True)
        if slot is None:
            self._resize(self.capacity * 2)
            slot = self._probe(key, insert=True)
            steps.append({"action": "rehash", "bucket": start,
                          "description": "table full -> doubled and rehashed"})
        occupied = self.slots[slot] is not None and self.slots[slot] is not TOMBSTONE
        self.slots[slot] = (key, value)
        if occupied:
            steps.append({"action": "update", "bucket": slot, "description": "key updated in place"})
            action = "updated"
        else:
            self.count += 1
            action = "inserted"
            steps.append({"action": "insert", "bucket": slot,
                          "description": f"stored at slot {slot}"})
        if self.collisions > before:
            steps.append({"action": "collision", "bucket": slot,
                          "description": f"{self.collisions - before} linear probe(s) needed"})
        if self.load_factor > 0.75:
            new_capacity = self.capacity * 2
            steps.append({"action": "rehash", "bucket": slot,
                          "description": f"load factor {self.load_factor:.2f} > 0.75 -> resize to {new_capacity}"})
            self._resize(new_capacity)
        return {"bucket": slot, "steps": steps, "action": action}

    def _resize(self, new_capacity: int) -> None:
        old = self.slots
        self.capacity = new_capacity
        self.slots = [None] * new_capacity
        self.count = 0
        self.rehashes += 1
        for entry in old:
            if entry is not None and entry is not TOMBSTONE:
                self.put(entry[0], entry[1], _rehash_pass=True)

    def get(self, key: str, default: Any = None) -> Any:
        slot = self._probe(str(key))
        return self.slots[slot][1] if slot is not None else default

    def contains(self, key: str) -> bool:
        return self._probe(str(key)) is not None

    def delete(self, key: str) -> bool:
        slot = self._probe(str(key))
        if slot is None:
            return False
        self.slots[slot] = TOMBSTONE
        self.count -= 1
        return True

    @property
    def load_factor(self) -> float:
        return self.count / self.capacity if self.capacity else 0.0

    def snapshot(self) -> list[str]:
        return [("" if entry is None else
                 ("<deleted>" if entry is TOMBSTONE else entry[0]))
                for entry in self.slots]

    def stats(self) -> dict:
        occupied = sum(1 for entry in self.slots
                       if entry is not None and entry is not TOMBSTONE)
        tombstones = sum(1 for entry in self.slots if entry is TOMBSTONE)
        return {
            "strategy": self.strategy,
            "capacity": self.capacity,
            "size": self.count,
            "load_factor": round(self.load_factor, 3),
            "collisions": self.collisions,
            "rehashes": self.rehashes,
            "probes": self.probes,
            "occupied_slots": occupied,
            "empty_slots": self.capacity - occupied - tombstones,
            "tombstones": tombstones,
        }


def build_hash_table(keys: Iterable[str], capacity: int = 16,
                    strategy: str = "chaining", hash_name: str = "djb2"):
    """Factory used by the tests, the indexer and the Algorithm Lab."""
    hash_func = polynomial_hash if hash_name == "polynomial" else djb2_hash
    if strategy == "chaining":
        table = HashTableChaining(capacity, hash_func)
    else:
        table = HashTableOpenAddressing(capacity, hash_func)
    for key in keys:
        table.put(str(key), str(key))
    return table


def timed_lookup(table, key: str) -> dict:
    """Single lookup with timing - the 'hash search' row on the dashboard."""
    start = time.perf_counter()
    value = table.get(key)
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": f"Hash Search ({table.strategy})",
        "found": value is not None or table.contains(key),
        "value": value,
        "comparisons": 1,
        "time_ms": elapsed,
        "details": {"hash_value": table.hash_func(str(key)),
                    "bucket": table.hash_func(str(key)) % table.capacity},
    }
