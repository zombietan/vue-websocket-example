import time
import asyncio
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado.options import define, options
import os
from dotenv import load_dotenv
import tweepy
import json
from logging import getLogger
logger = getLogger(__name__)


if os.getenv("HEROKU") is None:
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    port = 8888
else:
    port = int(os.environ.get("PORT", 5000))

CONFIG = os.environ

define("port", default=port, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        favicon_path = "/static/favicon.ico"
        handlers = [
            (r"/", MainHandler),
            (r"/ws", TwitterTrendWebSocketHandler),
            (
                r"/favicon.ico",
                tornado.web.StaticFileHandler,
                {"path": favicon_path}
            ),
        ]
        settings = dict(
            cookie_secret="GENERATE_YOUR_OWN_RANDOM_VALUE_HERE",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "index.html",
            # "index_bootstrap.html",
        )


class TwitterTrendWebSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    trends_cache = []

    def get_compression_options(self):
        return {}

    def open(self):
        TwitterTrendWebSocketHandler.waiters.add(self)
        trands = json.dumps(
            TwitterTrendWebSocketHandler.trends_cache
        )
        self.write_message(trands)

    def on_close(self):
        TwitterTrendWebSocketHandler.waiters.remove(self)

    @classmethod
    def send_updates(cls, trends):
        logger.info("sending message to %d waiters", len(cls.waiters))

        for waiter in cls.waiters:
            try:
                waiter.write_message(trends)
            except:
                logger.error("Error sending message", exc_info=True)


CONSUMER_KEY = CONFIG['CONSUMER_KEY']
CONSUMER_SECRET = CONFIG['CONSUMER_SECRET']
ACCESS_TOKEN = CONFIG['ACCESS_TOKEN']
ACCESS_SECRET = CONFIG['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

regional_id = {}
for place in api.trends_available():
    if place['countryCode'] == 'JP':
        regional_id[place['name']] = place['woeid']
JP = regional_id['Japan']


def loop_in_period_interval():
    PERIOD = 30
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_timeout(time.time() + PERIOD, loop_in_period_interval)
    trends = []
    for idx, trend in enumerate(api.trends_place(JP)[0]['trends'], 1):
        value = {
            "rank": str(idx),
            "name": trend["name"],
            "volume": trend["tweet_volume"],
            "url": trend["url"]
        }
        trends.append(value)
    TwitterTrendWebSocketHandler.trends_cache = trends
    json_str = json.dumps(trends)
    TwitterTrendWebSocketHandler.send_updates(json_str)


def main():
    loop_in_period_interval()
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
