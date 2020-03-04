class Plex(object):
    def __init__(self, plex):
        self.plex = plex

    def get_watched_episodes(self, section_name):
        watched_episodes = set(self.plex.library.section(section_name).searchEpisodes(unwatched=False))
        return watched_episodes
