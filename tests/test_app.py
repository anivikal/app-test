import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import create_server


class TaskAppTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, method="GET", body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data is not None else {},
        )
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        with response:
            content = response.read()
            if not content:
                payload = None
            elif "application/json" in response.headers.get("Content-Type", ""):
                payload = json.loads(content)
            else:
                payload = content
            return response.status, payload, response.headers

    def test_homepage_and_health(self):
        status, _, headers = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        status, payload, _ = self.request("/health")
        self.assertEqual((status, payload), (200, {"status": "ok"}))

    def test_task_lifecycle(self):
        status, created, _ = self.request("/api/tasks", "POST", {"title": "  Write tests  "})
        self.assertEqual(status, 201)
        task = created["task"]
        self.assertEqual(task, {"id": 1, "title": "Write tests", "done": False})

        status, updated, _ = self.request(
            f"/api/tasks/{task['id']}", "PATCH", {"done": True, "title": "Ship tests"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["task"], {"id": 1, "title": "Ship tests", "done": True})

        status, listing, _ = self.request("/api/tasks")
        self.assertEqual((status, listing["tasks"]), (200, [updated["task"]]))
        status, deleted, _ = self.request(f"/api/tasks/{task['id']}", "DELETE")
        self.assertEqual((status, deleted["task"]), (200, updated["task"]))
        self.assertEqual(self.request("/api/tasks")[1]["tasks"], [])

    def test_invalid_requests_are_reported(self):
        status, payload, _ = self.request("/api/tasks", "POST", {"title": "  "})
        self.assertEqual(status, 400)
        self.assertIn("title", payload["error"])
        status, payload, _ = self.request("/api/tasks/99", "PATCH", {"done": True})
        self.assertEqual((status, payload["error"]), (404, "Task not found"))


if __name__ == "__main__":
    unittest.main()
