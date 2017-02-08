import graypy
import logging


class Graylog(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.my_logger = logging.getLogger('plex2myshows')
        self.my_logger.setLevel(logging.ERROR)

        self.grayloghandler = graypy.GELFHandler(self.host, self.port)
        self.my_logger.addHandler(self.grayloghandler)
        self.my_adapter = logging.LoggerAdapter(self.my_logger,
                                                {'tag': 'plex2myshows'})

    def log(self, msg):
        self.my_adapter.error(msg)
