import http.client
import io
import json
import threading
import unittest
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer

from honeypot import HoneypotHandler, event_record, safe_path


class HoneypotTests(unittest.TestCase):
    def test_query_string_is_not_in_logged_path(self):
        self.assertEqual(safe_path("/session?password=not-for-logs"), "/session")

    def test_event_contains_metadata_not_submitted_values(self):
        event = event_record(("127.0.0.1", 43123), "POST", "/session?token=secret", 42)
        encoded = json.dumps(event)
        self.assertEqual(event["path"], "/session")
        self.assertEqual(event["body_bytes"], 42)
        self.assertNotIn("secret", encoded)
        self.assertNotIn("password", event)

    def test_post_response_does_not_echo_or_log_body(self):
        output = io.StringIO()
        server = ThreadingHTTPServer(("127.0.0.1", 0), HoneypotHandler)
        server.daemon_threads = True
        server.portal_title = "Northstar Operations Portal"
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with redirect_stdout(output):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=2)
                body = "username=jay&password=do-not-save"
                connection.request("POST", "/session", body=body,
                                   headers={"Content-Type": "application/x-www-form-urlencoded"})
                response = connection.getresponse()
                response_body = response.read().decode("utf-8")
                connection.close()
            self.assertEqual(response.status, 401)
            self.assertNotIn("do-not-save", response_body)
            self.assertNotIn("do-not-save", output.getvalue())
            event = json.loads(output.getvalue().strip().splitlines()[-1])
            self.assertEqual(event["body_bytes"], len(body))
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
