class EventPanel(scrolledpanel.ScrolledPanel):
    """Display list of buttons."""
    def __init__(self, parent,
                 style=wx.TAB_TRAVERSAL|wx.BORDER_SUNKEN):
        super(EventPanel, self).__init__(parent, style=style)

        # Attributes
        self.enames = EVENTMAP.keys()
        self.enames.sort()
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Setup
        for ename in self.enames:
            self.AppendEname(ename)
        self.SetSizer(self.sizer)

    def AppendEname(self, ename):
        """Add another event."""
        ebtn = wx.Button(self, size=(200,30),label = ename)
        self.sizer.Add(ebtn, 0, wx.TOP, 5)
        self.SetupScrolling()
