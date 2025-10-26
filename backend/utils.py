import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(log_dir="logs", log_file="app.log"):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Create rotating file handler: rotate at 250 KB, keep unlimited backups
    handler = RotatingFileHandler(
        log_path,
        maxBytes=250 * 1024,  # 250 KB
        backupCount=0,        # 0 means keep ALL old files (no deletion)
        encoding="utf-8"
    )

    # Format for log entries
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s — %(name)s — %(message)s")
    handler.setFormatter(formatter)

    # Attach handler to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    # Optional: also stream to console
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    logging.info(f"✅ Logging initialized — writing to {log_path}")

