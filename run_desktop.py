"""Backward-compatible command shim; the workstation is a native Qt app."""
from ui_qt.main import main

if __name__ == "__main__":
    raise SystemExit(main())
