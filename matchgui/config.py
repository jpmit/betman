import os
import pickle

class GlobalConfig(object):
    """Global app config

    The main app loads this at startup.  Note we only read and save
    the global config file at startup and shutdown respectively.  We
    are using Python's pickle module to store the config file at the
    moment, though the wx.Config functionality may be worth another
    look at some point (or, given the simple nature of the
    configuration data, a plain text file with rows key=value may be
    better than pickling).
    """
    
    # allowed options that are True/False (drawn as checkboxes).  Each
    # tuple stores shortname, full text, default value.

    # BFLogin - option not yet implemented
    # EngineStart - start the timer (ticks) from startup
    # ManyMarkets - controls whether we kill strategies for a
    # particular market after navigating away from that market.
    # (currently set to False, and not yet implemented)

    BINARIES = [('BFLogin', 'Login to BF at startup', True),
                ('EngineStart', 'Start engine at startup', False),
                ('ManyMarkets', 'Keep trading on markets', True),
                ('PracticeMode', 'Practice Mode (no orders)', False)]

    def __init__(self, cfg):
        """Read configuration file and set my state.

        cfg - name of config file.

        """

        # name of cfg file
        self.cfgname = cfg
        
        self.SetConfigFromFile()

    def SetConfigFromFile(self):
        """Called at startup only."""

        # dict with name as key [txt, val] as arg
        data = {}
        if os.path.isfile(self.cfgname):
            f = open(self.cfgname, 'rb')
            data = pickle.load(f)
            f.close()

        # go through each option in turn
        for opt in self.BINARIES:
            name, txt, default = opt
            if name in data:
                val = data[name][1]
            else:
                val = default
            self.SetOptionByName(name, val)

    def SaveCurrentConfigToFile(self):
        """Called at exit of application only."""
        
        data = {}
        for opt in self.BINARIES:
            name, txt, default = opt
            data[name] = [txt, self.GetOptionByName(name)]

        # write data to pickle
        f = open(self.cfgname, 'wb')
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        f.close()

    def SetOptionByName(self, name, val):
        """Set option and save new configuration file."""
        
        setattr(self, name, val)

    def GetOptionByName(self, name):
        return getattr(self, name)

    def SetOptionByTxt(self, txtval, val):
        """Set option with text 'txt' to value 'val'."""

        # need to map txt string e.g. 'Login to BF at startup' to name
        # e.g. 'BFLogin'.
        for opt in self.BINARIES:
            name, txt, default = opt
            if txt == txtval:
                self.SetOptionByName(name, val)
