import asyncio


class ProviderManager:
    def __init__(self, provider):
        self._current = provider
        self._active: dict[object, int] = {}
        self._retired: set[object] = set()
        self._lock = asyncio.Lock()

    async def generate(self, snapshot: dict):
        async with self._lock:
            provider = self._current
            self._active[provider] = self._active.get(provider, 0) + 1
        try:
            return await provider.generate(snapshot)
        finally:
            close_provider = None
            async with self._lock:
                self._active[provider] -= 1
                if self._active[provider] == 0:
                    del self._active[provider]
                    if provider in self._retired:
                        self._retired.remove(provider)
                        close_provider = provider
            if close_provider is not None:
                await close_provider.close()

    async def replace(self, provider):
        async with self._lock:
            previous = self._current
            self._current = provider
            if self._active.get(previous, 0):
                self._retired.add(previous)
                previous = None
        if previous is not None:
            await previous.close()

    async def close(self):
        async with self._lock:
            providers = {self._current, *self._retired, *self._active}
            self._retired.clear()
            self._active.clear()
        await asyncio.gather(*(provider.close() for provider in providers))
