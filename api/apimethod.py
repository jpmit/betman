# apimethod.py
# James Mithen
# jamesmithen@gmail.com

"""
Base class for API methods for both BDAQ and BF.  Not that this is for
the SOAP APIs only; they are not used for any screen scraping methods.
"""

class ApiMethod(object):
    """Base class for all Betdaq and BF Api methods."""

    def __init__(self, apiclient):
        """Set client, either read-only or secure."""
        self.client = apiclient.client

    def create_req(self):
        """Create the request object for the Api call."""
        pass

    def call(self):
        """Call the Api function and return the appropriate data."""
        pass
