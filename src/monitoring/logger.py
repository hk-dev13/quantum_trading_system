import json
import datetime

LOG_FILE = 'data/run_log.jsonl'

def log_event(event_type, data):
    """Log events to JSONL log file."""
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
