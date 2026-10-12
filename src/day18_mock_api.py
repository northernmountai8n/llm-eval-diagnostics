"""Local demo API for Day 18. It does not run a language model."""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Semaphore


_seen_fail_once: set[str] = set()
_seen_lock = Lock()
_service_slots = Semaphore(4)  # Simulate a server that handles at most four requests at once.


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1_000_000:
                raise ValueError("request size must be between 1 and 1000000 bytes")
            request = json.loads(self.rfile.read(size))
            messages = request["messages"]
            question = next(
                item["content"] for item in reversed(messages) if item["role"] == "user"
            )
            if not isinstance(question, str):
                raise ValueError("user content must be text")
        except (KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return

        if question.startswith("FAIL_ALWAYS:"):
            self.send_error(503, "simulated persistent failure")
            return

        if question.startswith("FAIL_ONCE:"):
            with _seen_lock:
                first_request = question not in _seen_fail_once
                _seen_fail_once.add(question)
            if first_request:
                self.send_error(503, "simulated temporary failure")
                return
            question = question.rsplit(":", 1)[-1]

        with _service_slots:
            time.sleep(1)  # Simulate waiting for a model response.
        body = json.dumps(
            {
                "id": "day18-mock",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": f"模拟回复：{question}"},
                        "finish_reason": "stop",
                    }
                ],
            },
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the local Day 18 mock API")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Day 18 mock API: http://127.0.0.1:{args.port}/v1/chat/completions", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
