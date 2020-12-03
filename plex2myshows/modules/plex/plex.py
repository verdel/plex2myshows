class Plex(object):
    def __init__(self, plex):
        self.plex = plex

    def get_watched_episodes(self, section_name):
        watched_episodes = []
        shows = self.plex.library.section(section_name).searchShows()
        for show in shows:
            watched_episodes.extend(show.watched())
        return watched_episodes
