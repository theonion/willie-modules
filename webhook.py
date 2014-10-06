"""A Willie module to allow Hithub webhooks"""

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Queue
import willie.module
import json


message_queue = Queue()


class GithubEventParser(object):

    def __init__(self, secret):
        self.secret = secret

    def create(self, data):
        return "create"

    def issues(self, data):
        return "issues"

    def pull_request(self, data):
        return "PR"

    def push(self, data):
        template = "{username} pushed {size} commits to {repository} ({compare_url})"
        format_data = {
            "username": data["pusher"]["name"],
            "size": len(data["commits"]),
            "repository": data["repository"]["name"],
            "compare_url": data["compare"]
        }
        return template.format(**format_data)

    def release(self, data):
        return "release"


parser = GithubEventParser("testing")


class WebhookHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        message_queue.put("Testing")
        self.wfile.write("OK")

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        content_length = int(self.headers["Content-Length"])
        event_name = self.headers["X-Github-Event"]
        json_string = self.rfile.read(content_length)
        data = json.loads(json_string)
        self.wfile.write(json.dumps({"status": "OK"}))

        if hasattr(parser, event_name):
            message = getattr(parser, event_name)(data)
            if message:
                message_queue.put(message)

        return

    def log_message(self, format, *args):
        return


def serve_forever(server):
    server.serve_forever()


def configure(config):
    config.interactive_add(
        "webbook",
        "listen_address",
        "The address to listen on",
        default="0.0.0.0:8973")


def setup(bot):
    server = HTTPServer(("", 8973), WebhookHandler)
    Process(target=serve_forever, args=(server,)).start()


@willie.module.interval(5)
def poll_queue(bot):
    while True:
        try:
            message = message_queue.get()
            bot.msg("#theonion", message)
        except Exception as e:
            print(e)
            break
