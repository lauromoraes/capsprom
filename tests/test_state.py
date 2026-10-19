import json
from pathlib import Path

from capsprom.state import write_json_atomic


def test_write_json_atomic_replaces_previous_state(tmp_path: Path):
    target = tmp_path / "nested" / "state.json"
    target.parent.mkdir()
    target.write_text('{"old": true}\n')

    write_json_atomic(target, {"complete": 3})

    assert json.loads(target.read_text()) == {"complete": 3}
    assert not list(target.parent.glob("*.tmp"))
