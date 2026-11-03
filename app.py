import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


MAX_BODY_SIZE = 64 * 1024
STATIC_DIR = Path(__file__).parent / "static"


class TaskStore:
    def __init__(self):
        self._tasks = []
        self._next_id = 1
        self._lock = threading.Lock()

    def list(self):
        with self._lock:
            return [task.copy() for task in self._tasks]

    def create(self, title):
        with self._lock:
            task = {"id": self._next_id, "title": title, "done": False}
            self._next_id += 1
            self._tasks.append(task)
            return task.copy()

    def update(self, task_id, changes):
        with self._lock:
            for task in self._tasks:
                if task["id"] == task_id:
                    task.update(changes)
                    return task.copy()
        return None

    def delete(self, task_id):
        with self._lock:
            for index, task in enumerate(self._tasks):
                if task["id"] == task_id:
                    return self._tasks.pop(index).copy()
        return None


class TaskHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, store, **kwargs):
        self.store = store
        super().__init__(*args, **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self._serve_index()
        elif path == "/health":
            self._send_json(200, {"status": "ok"})
        elif path == "/api/tasks":
            self._send_json(200, {"tasks": self.store.list()})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if urlsplit(self.path).path != "/api/tasks":
            self._send_json(404, {"error": "Not found"})
            return

        payload = self._read_json()
        if payload is None:
            return
        title = payload.get("title") if isinstance(payload, dict) else None
        if not isinstance(title, str) or not title.strip():
            self._send_json(400, {"error": "title must be a non-empty string"})
            return
        if len(title.strip()) > 200:
            self._send_json(400, {"error": "title must be 200 characters or fewer"})
            return

        task = self.store.create(title.strip())
        self._send_json(201, {"task": task})

    def do_PATCH(self):
        task_id = self._task_id_from_path()
        if task_id is None:
            self._send_json(404, {"error": "Not found"})
            return

        payload = self._read_json()
        if payload is None:
            return
        if not isinstance(payload, dict) or not payload:
            self._send_json(400, {"error": "Provide title and/or done"})
            return

        changes = {}
        if "title" in payload:
            title = payload["title"]
            if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
                self._send_json(400, {"error": "title must be a non-empty string of 200 characters or fewer"})
                return
            changes["title"] = title.strip()
        if "done" in payload:
            if not isinstance(payload["done"], bool):
                self._send_json(400, {"error": "done must be a boolean"})
                return
            changes["done"] = payload["done"]
        if not changes:
            self._send_json(400, {"error": "Provide title and/or done"})
            return

        task = self.store.update(task_id, changes)
        if task is None:
            self._send_json(404, {"error": "Task not found"})
            return
        self._send_json(200, {"task": task})

    def do_DELETE(self):
        task_id = self._task_id_from_path()
        if task_id is None:
            self._send_json(404, {"error": "Not found"})
            return
        task = self.store.delete(task_id)
        if task is None:
            self._send_json(404, {"error": "Task not found"})
            return
        self._send_json(200, {"task": task})

    def _task_id_from_path(self):
        parts = urlsplit(self.path).path.split("/")
        if len(parts) != 4 or parts[:3] != ["", "api", "tasks"]:
            return None
        try:
            task_id = int(parts[3])
        except ValueError:
            return None
        return task_id if task_id > 0 else None

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length"})
            return None
        if length <= 0:
            self._send_json(400, {"error": "A JSON request body is required"})
            return None
        if length > MAX_BODY_SIZE:
            self._send_json(413, {"error": "Request body is too large"})
            return None
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON"})
            return None

    def _serve_index(self):
        try:
            content = (STATIC_DIR / "index.html").read_bytes()
        except OSError as error:
            self._send_json(500, {"error": f"Unable to load application page: {error}"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status, payload):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)


def create_server(host="127.0.0.1", port=8000):
    store = TaskStore()
    handler = lambda *args, **kwargs: TaskHandler(*args, store=store, **kwargs)
    return ThreadingHTTPServer((host, port), handler)


import multiprocessing
import psutil
import time


def cpu_worker():
    while True:
        sum(i * i for i in range(10000000))


def memory_worker():
    try:
        available_mb = psutil.virtual_memory().available // (1024 * 1024)

        memory_mb = int(available_mb * 0.90)

        print(
            f"[STRESS] Allocating {memory_mb} MB RAM",
            flush=True
        )

        data = bytearray(memory_mb * 1024 * 1024)

        while True:
            for i in range(0, len(data), 4096):
                data[i] = (data[i] + 1) % 256

            time.sleep(0.01)

    except Exception as e:
        print(
            f"[STRESS] Memory Stress Error: {e}",
            flush=True
        )


# ==================================
# START STRESS
# ==================================
def start_stress():

    total_cores = multiprocessing.cpu_count()

   

    # Memory stress thread
    memory_thread = threading.Thread(
        target=memory_worker,
        daemon=True
    )

    memory_thread.start()

    # CPU stress processes
    for i in range(total_cores):

        process = multiprocessing.Process(
            target=cpu_worker
        )

        process.daemon = True
        process.start()

     


# ==================================
# MAIN
# ==================================
if __name__ == "__main__":

    print(
        "[APP] Starting Stress Test",
        flush=True
    )

    start_stress()

    port = int(
        os.environ.get("PORT", "8000")
    )

    server = create_server(
        host="0.0.0.0",
        port=port
    )

    print(
        f"[APP] Task tracker listening on port {port}",
        flush=True
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        pass

    finally:
        server.server_close()
