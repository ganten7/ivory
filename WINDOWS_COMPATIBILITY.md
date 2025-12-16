# Windows Compatibility Notes

## Process Forking (os.fork())

### Issue
On Windows, the `os.fork()` function does not exist. Attempting to call `os.fork()` on Windows results in:
```
AttributeError: module 'os' has no attribute 'fork'
```

### Solution
Always check for the existence of `fork()` before calling it:

```python
if hasattr(os, 'fork'):
    if os.fork() > 0:
        # Parent process - exit immediately
        sys.exit(0)
    # Child process continues
    # Redirect stdout/stderr to /dev/null (Unix only)
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
else:
    # Windows: fork() doesn't exist, so we can't detach from terminal
    # On Windows, the app will run in the terminal window
    # This is acceptable behavior for Windows users
    pass
```

### Why This Matters
- **Unix/Linux/macOS**: `os.fork()` exists and allows the process to detach from the terminal, enabling the app to run independently
- **Windows**: `os.fork()` doesn't exist. The app will run in the terminal window, which is acceptable for Windows users

### Location
This check is implemented in `ivory_v2.py` around lines 2039-2053.

### Future Considerations
- If Windows-specific process detachment is needed in the future, consider using:
  - `subprocess.Popen` with `CREATE_NEW_PROCESS_GROUP` flag
  - `multiprocessing` module (cross-platform)
  - Windows-specific APIs via `ctypes` or `win32api`

### Testing
To test Windows compatibility:
1. Simulate Windows environment: `delattr(os, 'fork')` if it exists
2. Verify the code path skips forking without errors
3. Restore fork if needed: `os.fork = original_fork`

