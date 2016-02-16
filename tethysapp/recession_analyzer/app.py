from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.stores import PersistentStore

class RecessionAnalyzer(TethysAppBase):
    """
    Tethys app class for Recession Analyzer.
    """

    name = 'Recession Analyzer'
    index = 'recession_analyzer:home'
    icon = 'recession_analyzer/images/icon.gif'
    package = 'recession_analyzer'
    root_url = 'recession-analyzer'
    color = '#e67e22'
    description = 'Place a brief description of your app here.'
    enable_feedback = False
    feedback_emails = []

        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='recession-analyzer',
                           controller='recession_analyzer.controllers.home'),
        )

        return url_maps

        return url_maps
        
    def persistent_stores(self):
        """
        Add one or more persistent stores
        """
        stores = (PersistentStore(name='stream_gage_db',
                                  initializer='recession_analyzer.init_stores.init_stream_gage_db',
                                  spatial=True
                ),
        )

        return stores        