# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A single-module, cross-platform (Windows/macOS/Linux) Python utility (`findfqpath.py`) exposing `find_fq_path(find_file, num_days_valid, scope="Shared")`. It returns the fully qualified path of the most recently modified copy of a file (e.g. `opera.exe`) so callers don't break when an executable moves to a new versioned install folder. Results are cached in a `shelve` file. Published on PyPI as `findfqpath`. The only third-party dependency is `platformdirs`.

Packaging is in `pyproject.toml` (setuptools, single `py-modules` entry); bump `version` there for each PyPI release. There is no test suite or linter config. The untracked `venv/` is broken (built on a Python 3.6 that is no longer installed); create a fresh one.

## Running

```
pip install platformdirs
python findfqpath.py
```

Build and check the package (needs `pip install build twine`):

```
python -m build
python -m twine check dist/*
```

Running the module directly executes the `__main__` block at the bottom of the file, which looks up `opera.exe` and logs the result. Logging is enabled at DEBUG on the root logger at import time; toggle via `root_logger.disabled`.

## How the lookup works

1. **Shelf location** depends on `scope`:
   - `"Local"` → `FileShlf` next to the calling script (`sys.argv[0]`), so each script has its own cache.
   - anything else (default `"Shared"`) → `FileShlf` in `platformdirs.user_cache_dir("findfqpath")` (e.g. `%LOCALAPPDATA%\findfqpath\Cache` on Windows).
2. **Cache keys** are `<find_file>fqpath` (the path) and `<find_file>DateUpdated` (a `datetime`).
3. **Cache hit**: if the cached path still exists and was stored less than `num_days_valid` days ago, it is returned immediately. `num_days_valid=0` always forces a search.
4. **Search** (`find_under` uses `os.walk`, skips `/proc`, `/sys`, `/dev`, `/run`, doesn't follow symlinks, and matches names case-insensitively on Windows only):
   - **Stale/missing cache entry**: search from two levels above the cached path, then walk up one directory at a time until something is found or the filesystem root is reached.
   - **First lookup**: on macOS/Linux try `shutil.which` first; then search all of `default_search_dirs()` (per-OS install folders); then fall back to `filesystem_root()` (system drive or `/`). A first-time miss can therefore scan the entire drive and be slow.
5. Among all matches, the one with the newest mtime (`max(..., key=os.path.getmtime)`) is written back to the shelf and returned; `None` if nothing is found.

Callers pass the OS-specific file name (`opera.exe` on Windows, `opera` on Linux, `Opera` inside the macOS app bundle).
