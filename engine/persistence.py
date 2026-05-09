import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

STATE_FILE = "storage/state.json"

def save_state(state: Dict[str, Any]):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4, default=str)
    logger.debug("State saved.")

def load_state() -> Optional[Dict[str, Any]]:
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading state: {e}")
        return None
