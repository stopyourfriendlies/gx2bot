import logging

LOGGING_FORMATTER = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")


def new_logger(name: str, level: int, mode: str = "w") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.FileHandler(filename=f"{name}.log", encoding="utf-8", mode=mode)
    logger.addHandler(handler)
    return logger
