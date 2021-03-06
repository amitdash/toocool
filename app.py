#!/usr/bin/env python
import os
import re
import here
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import redis.client
from tornado.options import define, options
from tornado_utils.routes import route
import handlers
import settings


define("debug", default=False, help="run in debug mode", type=bool)
define("database_name", default=settings.DATABASE_NAME, help="db name")
define("port", default=8000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self, database_name=None):
        _ui_modules = __import__('ui_modules', globals(), locals(), ['ui_modules'], -1)
        ui_modules_map = {}
        for name in [x for x in dir(_ui_modules) if re.findall('[A-Z]\w+', x)]:
            thing = getattr(_ui_modules, name)
            try:
                if issubclass(thing, tornado.web.UIModule):
                    ui_modules_map[name] = thing
            except TypeError:  # pragma: no cover
                # most likely a builtin class or something
                pass

        routed_handlers = route.get_routes()
        app_settings = dict(
            title=settings.PROJECT_TITLE,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret=settings.COOKIE_SECRET,
            debug=options.debug,
            email_backend=options.debug and \
                 'tornado_utils.send_mail.backends.console.EmailBackend' \
              or 'tornado_utils.send_mail.backends.pickle.EmailBackend',
            admin_emails=settings.ADMIN_EMAILS,
            ui_modules=ui_modules_map,
            twitter_consumer_key=settings.TWITTER_CONSUMER_KEY,
            twitter_consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        )
        if 1 or not options.debug:
            routed_handlers.append(
              tornado.web.url('/.*?', handlers.PageNotFoundHandler,
                            name='page_not_found')
            )
        super(Application, self).__init__(routed_handlers, **app_settings)

        self.redis = redis.client.Redis(settings.REDIS_HOST,
                                        settings.REDIS_PORT)

        from models import connection
        self.db = connection[database_name or settings.DATABASE_NAME]



def main():  # pragma: no cover
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    print "Starting tornado on port", options.port
    http_server.listen(options.port)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":  # pragma: no cover
    main()
