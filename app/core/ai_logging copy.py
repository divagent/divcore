import logging
import json
import time
import uuid

logger = logging.getLogger("rag")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def log_event(event: str, **kwargs):
    payload = {
        "event": event,
        **kwargs,
    }
    logger.info(json.dumps(payload))


# import logging

# def setup_logger():
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
#         datefmt="%Y-%m-%d %H:%M:%S",
#     )
