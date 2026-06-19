"""Briefcase entry point for Android."""
import sys
import traceback

try:
    from .app import main
    app = main()
    app.main_loop()
except Exception:
    try:
        from android import log
        log.e("ReticulumMesh", f"Fatal startup error:\n{traceback.format_exc()}")
    except ImportError:
        pass
    try:
        with open("/data/data/com.narl3y.reticulummesh/files/crash.log", "w") as f:
            traceback.print_exc(file=f)
    except Exception:
        pass
    raise
