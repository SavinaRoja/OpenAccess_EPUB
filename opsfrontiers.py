"""
This module defines an OPS content generator class for Frontiers. It inherits
from the OPSGenerator base class in opsgenerator.py
"""

import opsgenerator


class OPSFrontiers(opsgenerator.OPSGenerator):
    """
    This provides the full feature set to create OPS content for an ePub file
    from a Frontiers journal article.
    """
    def __init__(self, article):
        opsgenerator.OPSGenerator.__init__(self)

    def announce(self):
        """
        Announces the class initiation
        """
        print('Initiating OPSFrontiers')
