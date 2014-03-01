class Automation(object):

    def __init__(self, name):
        """Should be called by sub class."""

        self._name = name

    def update(self, stratgroup):
        """Add or remove strategies from strat, which is the global strategy
        group.

        We may want to do quite a bit of work here.  For example, our
        our automation could be for market making on horse races
        during the 10 minutes, for the favourite only.  This function
        is responsible for adding/removing strategies from stratgroup
        in accordance with this policy.
        """
        
        pass

    def get_name(self):
        return self._name
