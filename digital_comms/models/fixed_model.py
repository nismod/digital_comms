"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from itertools import tee
from pprint import pprint

class ICTManager(object):
    """Model controller class."""

    def __init__(self, exchanges, cabinets, distributions, premises, links):

        self._premises = [Premise(premise) for premise in premises]
        self._distributions = [Distribution(distribution) for distribution in distributions]
        self._cabinets = [Cabinets(cabinet) for cabinet in cabinets]
        self._exchanges = [Exchanges(exchange) for exchange in exchanges]

        self._links = [Links(link) for link in links]

    @property
    def links(self):
        """Returns a certain subset of links"""
        return {
            'premises':         [link for link in self._links if 
                                link.origin.startswith('premise') or
                                link.dest.startswith('premise')],
            'distributions':    [link for link in self._links if 
                                link.origin.startswith('distribution') or
                                link.dest.startswith('distribution')],
            'cabinets':         [link for link in self._links if 
                                link.origin.startswith('cabinet') or
                                link.dest.startswith('cabinet')],
            'exchanges':         [link for link in self._links if 
                                link.origin.startswith('exchange') or
                                link.dest.startswith('exchange')],
            'dist_to_prem':     [link for link in self._links if 
                                (link.origin.startswith('distribution') or
                                link.origin.startswith('premise')) and
                                (link.dest.startswith('distribution') or
                                link.dest.startswith('premise'))],
            'cab_to_dist':      [link for link in self._links if 
                                (link.origin.startswith('cabinet') or
                                link.origin.startswith('distribution')) and
                                (link.dest.startswith('cabinet') or
                                link.dest.startswith('distribution'))],
            'ex_to_cab':        [link for link in self._links if 
                                (link.origin.startswith('exchange') or
                                link.origin.startswith('cabinet')) and
                                (link.dest.startswith('exchange') or
                                link.dest.startswith('cabinet'))]
        }

    @property
    def number_of_assets(self):
        """obj: Number of assets in the model
        """
        return {
            'premises':         len(self._premises),
            'distributions':    len(self._distributions),
            'cabinets':         len(self._cabinets),
            'exchanges':        len(self._exchanges),
        }

    @property
    def number_of_links(self):
        """obj: Total number of links in the model
        """
        return {
            'premises':         len(self.links['premises']),
            'distributions':    len(self.links['distributions']),
            'cabinets':         len(self.links['cabinets']),
            'exchanges':        len(self.links['exchanges']),
            'dist_to_prem':     len(self.links['dist_to_prem']),
            'cab_to_dist':      len(self.links['cab_to_dist']),
            'ex_to_cab':        len(self.links['ex_to_cab'])
        }

    @property
    def total_link_length(self):
        """obj: Total link length in the model
        """
        return {
            'dist_to_prem':     sum(link.length for link in self.links['dist_to_prem']),
            'cab_to_dist':      sum(link.length for link in self.links['cab_to_dist']),
            'ex_to_cab':        sum(link.length for link in self.links['ex_to_cab'])
        }

    @property
    def avg_link_length(self):
        return {
            'dist_to_prem':     self.total_link_length['dist_to_prem'] / self.number_of_links['dist_to_prem'],
            'cab_to_dist':      self.total_link_length['cab_to_dist'] / self.number_of_links['cab_to_dist'],
            'ex_to_cab':        self.total_link_length['ex_to_cab'] / self.number_of_links['ex_to_cab']
        }

class Premise(object):
    """Premise"""

    def __init__(self, data):
        self.id = data["id"]
        self.fttp = data["FTTP"]
        self.gfast = data["GFast"]
        self.fttc = data["FTTC"]
        self.docsis3 = data["DOCSIS3"]
        self.adsl = data["ADSL"]

    def __repr__(self):
        return "<Premise id:{}>".format(self.id)

class Distribution(object):
    """Distribution"""

    def __init__(self, data):
        self.id = data["id"]

    def __repr__(self):
        return "<Distribution id:{}>".format(self.id)

class Cabinets(object):
    """Cabinets"""

    def __init__(self, data):
        self.id = data["id"]

    def __repr__(self):
        return "<Cabinet id:{}>".format(self.id)

class Exchanges(object):
    """Exchanges"""

    def __init__(self, data):
        self.id = data["id"]

    def __repr__(self):
        return "<Exchange id:{}>".format(self.id)

class Links(object):
    """Links"""

    def __init__(self, data):
        self.origin = data["origin"]
        self.dest = data["dest"]
        self.length = data["length"]

    def __repr__(self):
        return "<Link origin:{} dest:{} length:{}>".format(self.origin, self.dest, self.length)