import logging

logger = logging.getLogger(__name__)

def keyevent(*keys):
    return " && ".join([f"input keyevent {key}" for key in keys])

def send_keys(key: list):
    return f"input text {key}"

def tap(*coords: list[tuple]):
    return " && ".join([f"input tap {x} {y}" for x, y in coords])

def package(action: bool, package: str):
    if action:
        return f"monkey -p {package} 1"
    else:
        return f"am force-stop {package}"