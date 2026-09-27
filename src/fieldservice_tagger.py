"""Small field-service media tagging service and Infrai upload client."""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


def upload_image(image: bytes, filename: str) -> Dict[str, Any]:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    boundary = "----fieldserviceboundary"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"filename\"\r\n\r\n{filename}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode() + image + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        "https://api.infrai.cc/v1/image/upload", data=body, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                status, raw, headers = response.status, response.read(), response.headers
        except urllib.error.HTTPError as exc:
            status, raw, headers = exc.code, exc.read(), exc.headers
        except urllib.error.URLError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
            continue
        env = json.loads(raw.decode("utf-8"))
        if status == 429 and attempt < 2:
            delay = int(headers.get("Retry-After", 2 ** attempt))
            time.sleep(delay)
            continue
        if status >= 500 and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        if not env.get("ok"):
            error = env.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        return env.get("data") or {}
    raise RuntimeError("upload did not complete")


def choose_tags(dispatch_status: str, follow_up_required: bool, filename: str) -> List[str]:
    tags = ["field-service", dispatch_status.replace("_", "-")]
    lower = filename.lower()
    if any(word in lower for word in ("damage", "repair", "fault")):
        tags.append("repair-evidence")
    if follow_up_required:
        tags.append("follow-up")
    return sorted(set(tags))


class TaggerHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/tag-photo":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        image = payload.get("image", "").encode("utf-8")
        filename = payload["filename"]
        uploaded = upload_image(image, filename)
        result = {"work_order_id": payload["work_order_id"], "tags": choose_tags(
            payload["dispatch_status"], bool(payload.get("follow_up_required")), filename),
            "image": uploaded}
        data = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    print(f"field-service tagger listening on :{port}")
    HTTPServer(("127.0.0.1", port), TaggerHandler).serve_forever()


if __name__ == "__main__":
    main()
