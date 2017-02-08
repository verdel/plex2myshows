class Plex(object):
    def __init__(self, plex):
        self.plex = plex

    def _get_all_episodes(self, section_name):
        all_episodes = set(self.plex.library.section(section_name).searchEpisodes())
        return all_episodes

    def _get_unwatched_episodes(self, section_name):
        unwatched_episodes = set(self.plex.library.section(section_name).searchEpisodes(unwatched=True))
        return unwatched_episodes

    def get_watched_episodes(self, section_name):
        all_episodes = self._get_all_episodes(section_name)
        all_episodes_id = set([item.ratingKey for item in all_episodes])
        unwatched_episodes = self._get_unwatched_episodes(section_name)
        unwatched_episodes_id = set([item.ratingKey for item in unwatched_episodes])
        watched_episodes_id = all_episodes_id.difference(unwatched_episodes_id)
        watched_episodes = [item for item in all_episodes if item.ratingKey in watched_episodes_id]
        return watched_episodes
