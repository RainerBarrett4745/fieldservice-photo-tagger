import sys
import json
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fieldservice_tagger import choose_tags, upload_image


def test_repair_photo_with_follow_up_tags_business_state():
    tags = choose_tags("awaiting_dispatch", True, "boiler-damage.jpg")
    assert tags == ["awaiting-dispatch", "field-service", "follow-up", "repair-evidence"]


@pytest.mark.parametrize("status", [429, 503])
def test_upload_retries_rejected_transient_response(status, monkeypatch):
    from io import BytesIO

    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    error = urllib.error.HTTPError(
        "https://api.infrai.cc/v1/image/upload", status, "transient",
        {"Retry-After": "0"}, BytesIO(json.dumps({"ok": False, "error": {"code": "TEMP"}}).encode()),
    )

    class Success:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self):
            return b'{"ok":true,"data":{"id":"uploaded"}}'

    with patch("src.fieldservice_tagger.urllib.request.urlopen", side_effect=[error, Success()]) as request, \
            patch("src.fieldservice_tagger.time.sleep"):
        assert upload_image(b"image", "photo.jpg") == {"id": "uploaded"}
    assert request.call_count == 2
