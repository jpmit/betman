# apimethod.py
# James Mithen
# jamesmithen@gmail.com

"""
Base class for API methods (official SOAP APIs) and for NonApi (screen
scraping) methods for both BDAQ and BF.
"""

class ApiMethod(object):
    """Base class for all Betdaq and BF Api methods."""

    def __init__(self, apiclient):
        """Set client, either read-only or secure."""
        
        self.client = apiclient.client
        # note this will call the derived class method, assuming it
        # exists, and not the method below.
        self.create_req()

    def create_req(self):
        """Create the request object for the Api call."""
        
        pass

    def call(self):
        """Call the Api function and return the appropriate data."""
        
        pass

class NonApiMethod(object):
    """Base class for all Betdaq and BF NonApi methods."""

    def __init__(self, urlclient):
        self.client = urlclient

    def call(self):
        """Call the NonApi function and return the appropriate data."""
        
        pass

