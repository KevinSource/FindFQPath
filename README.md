# FindFQPath

[![PyPI](https://img.shields.io/pypi/v/findfqpath)](https://pypi.org/project/findfqpath/)
[![Python](https://img.shields.io/pypi/pyversions/findfqpath)](https://pypi.org/project/findfqpath/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Find the fully qualified path of the most recent installed copy of a file, such as a browser executable, even when updates keep moving it to a new versioned folder.

Many tools need the full path to an executable. Selenium's `binary_location` is a common example. Programs like Opera install each update into a new folder, so a hard-coded path breaks every time the program updates. `find_fq_path` searches for the file once, remembers where it was, and returns that path on later calls in well under a second. When the saved path goes missing or gets older than you allow, it searches again and picks the newest copy.

Works on Windows, macOS and Linux.

## Install

```
pip install findfqpath
```

## Usage

```python
from findfqpath import find_fq_path

opera_path = find_fq_path("opera.exe", num_days_valid=1)
```

With Selenium:

```python
from selenium import webdriver
from findfqpath import find_fq_path

options = webdriver.ChromeOptions()
options.binary_location = find_fq_path("opera.exe", num_days_valid=1)
```

### Parameters

| Parameter | Description |
|---|---|
| `find_file` | Name of the file to find. Use the name for the OS: `opera.exe` on Windows, `opera` on Linux, `Opera` on macOS (the program inside `Opera.app`). |
| `num_days_valid` | Search again if the saved path is older than this many days. `0` always searches. |
| `scope` | `"Shared"` (default) saves the path in your user cache folder so every script that uses `"Shared"` reuses it. `"Local"` saves it in the calling script's folder, so each script keeps its own. |

Returns the full path as a string, or `None` if the file can't be found.

## How it works

1. **Saved path:** if the path saved for this file still exists and is newer than `num_days_valid` days, it's returned straight away.
2. **Re-search:** if the saved path is missing or too old, the search starts two folders above where the file was last found, then moves up one folder at a time. A new version installed next to the old one is usually found quickly.
3. **First search:** for a file it hasn't seen before, it checks:
   - your `PATH` (macOS and Linux only);
   - the usual install folders: `Program Files`, `Program Files (x86)` and `AppData\Local\Programs` on Windows; `/Applications` and Homebrew on macOS; `/usr/bin`, `/opt`, `/snap/bin` and `~/.local/bin` on Linux;
   - the whole drive, as a last resort.
4. If several copies are found, the most recently modified one wins.

The first search for a file can take a while if it has to scan the whole drive. Later calls for the same file are fast.

The shared cache is stored in the per-user cache folder from [platformdirs](https://pypi.org/project/platformdirs/), for example `%LOCALAPPDATA%\findfqpath\Cache` on Windows or `~/.cache/findfqpath` on Linux.

## License

MIT
