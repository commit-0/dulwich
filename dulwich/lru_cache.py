"""A simple least-recently-used (LRU) cache."""
from typing import Callable, Dict, Generic, Iterable, Iterator, Optional, TypeVar
_null_key = object()
K = TypeVar('K')
V = TypeVar('V')

class _LRUNode(Generic[K, V]):
    """This maintains the linked-list which is the lru internals."""
    __slots__ = ('prev', 'next_key', 'key', 'value', 'cleanup', 'size')
    prev: Optional['_LRUNode[K, V]']
    next_key: K
    size: Optional[int]

    def __init__(self, key: K, value: V, cleanup=None) -> None:
        self.prev = None
        self.next_key = _null_key
        self.key = key
        self.value = value
        self.cleanup = cleanup
        self.size = None

    def __repr__(self) -> str:
        if self.prev is None:
            prev_key = None
        else:
            prev_key = self.prev.key
        return f'{self.__class__.__name__}({self.key!r} n:{self.next_key!r} p:{prev_key!r})'

class LRUCache(Generic[K, V]):
    """A class which manages a cache of entries, removing unused ones."""
    _least_recently_used: Optional[_LRUNode[K, V]]
    _most_recently_used: Optional[_LRUNode[K, V]]

    def __init__(self, max_cache: int=100, after_cleanup_count: Optional[int]=None) -> None:
        self._cache: Dict[K, _LRUNode[K, V]] = {}
        self._most_recently_used = None
        self._least_recently_used = None
        self._update_max_cache(max_cache, after_cleanup_count)

    def __contains__(self, key: K) -> bool:
        return key in self._cache

    def __getitem__(self, key: K) -> V:
        cache = self._cache
        node = cache[key]
        mru = self._most_recently_used
        if node is mru:
            return node.value
        node_prev = node.prev
        next_key = node.next_key
        if next_key is _null_key:
            self._least_recently_used = node_prev
        else:
            node_next = cache[next_key]
            node_next.prev = node_prev
        assert node_prev
        assert mru
        node_prev.next_key = next_key
        node.next_key = mru.key
        mru.prev = node
        self._most_recently_used = node
        node.prev = None
        return node.value

    def __len__(self) -> int:
        return len(self._cache)

    def _walk_lru(self) -> Iterator[_LRUNode[K, V]]:
        """Walk the LRU list, only meant to be used in tests."""
        pass

    def add(self, key: K, value: V, cleanup: Optional[Callable[[K, V], None]]=None) -> None:
        """Add a new value to the cache.

        Also, if the entry is ever removed from the cache, call
        cleanup(key, value).

        Args:
          key: The key to store it under
          value: The object to store
          cleanup: None or a function taking (key, value) to indicate
                        'value' should be cleaned up.
        """
        pass

    def cache_size(self) -> int:
        """Get the number of entries we will cache."""
        pass

    def keys(self) -> Iterable[K]:
        """Get the list of keys currently cached.

        Note that values returned here may not be available by the time you
        request them later. This is simply meant as a peak into the current
        state.

        Returns: An unordered list of keys that are currently cached.
        """
        pass

    def items(self) -> Dict[K, V]:
        """Get the key:value pairs as a dict."""
        pass

    def cleanup(self):
        """Clear the cache until it shrinks to the requested size.

        This does not completely wipe the cache, just makes sure it is under
        the after_cleanup_count.
        """
        pass

    def __setitem__(self, key: K, value: V) -> None:
        """Add a value to the cache, there will be no cleanup function."""
        self.add(key, value, cleanup=None)

    def _record_access(self, node: _LRUNode[K, V]) -> None:
        """Record that key was accessed."""
        pass

    def _remove_lru(self) -> None:
        """Remove one entry from the lru, and handle consequences.

        If there are no more references to the lru, then this entry should be
        removed from the cache.
        """
        pass

    def clear(self) -> None:
        """Clear out all of the cache."""
        pass

    def resize(self, max_cache: int, after_cleanup_count: Optional[int]=None) -> None:
        """Change the number of entries that will be cached."""
        pass

class LRUSizeCache(LRUCache[K, V]):
    """An LRUCache that removes things based on the size of the values.

    This differs in that it doesn't care how many actual items there are,
    it just restricts the cache to be cleaned up after so much data is stored.

    The size of items added will be computed using compute_size(value), which
    defaults to len() if not supplied.
    """
    _compute_size: Callable[[V], int]

    def __init__(self, max_size: int=1024 * 1024, after_cleanup_size: Optional[int]=None, compute_size: Optional[Callable[[V], int]]=None) -> None:
        """Create a new LRUSizeCache.

        Args:
          max_size: The max number of bytes to store before we start
            clearing out entries.
          after_cleanup_size: After cleaning up, shrink everything to this
            size.
          compute_size: A function to compute the size of the values. We
            use a function here, so that you can pass 'len' if you are just
            using simple strings, or a more complex function if you are using
            something like a list of strings, or even a custom object.
            The function should take the form "compute_size(value) => integer".
            If not supplied, it defaults to 'len()'
        """
        self._value_size = 0
        if compute_size is None:
            self._compute_size = len
        else:
            self._compute_size = compute_size
        self._update_max_size(max_size, after_cleanup_size=after_cleanup_size)
        LRUCache.__init__(self, max_cache=max(int(max_size / 512), 1))

    def add(self, key: K, value: V, cleanup: Optional[Callable[[K, V], None]]=None) -> None:
        """Add a new value to the cache.

        Also, if the entry is ever removed from the cache, call
        cleanup(key, value).

        Args:
          key: The key to store it under
          value: The object to store
          cleanup: None or a function taking (key, value) to indicate
                        'value' should be cleaned up.
        """
        pass

    def cleanup(self) -> None:
        """Clear the cache until it shrinks to the requested size.

        This does not completely wipe the cache, just makes sure it is under
        the after_cleanup_size.
        """
        pass

    def resize(self, max_size: int, after_cleanup_size: Optional[int]=None) -> None:
        """Change the number of bytes that will be cached."""
        pass