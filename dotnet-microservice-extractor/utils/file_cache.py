import os
import aiofiles

class FileCache:
    def __init__(self):
        self._cache = {}

    async def get_file_content(self, file_path: str) -> str:
        if file_path in self._cache:
            return self._cache[file_path]
        if os.path.exists(file_path):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            self._cache[file_path] = content
            return content
        raise FileNotFoundError(f"File not found: {file_path}")

    async def update_file(self, file_path: str, new_content: str):
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(new_content)
        self._cache[file_path] = new_content

    def clear_cache(self):
        self._cache.clear()