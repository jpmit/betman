class PopupMenuMixin(object):
    def __init__(self, event):
        super(PopupMenuMixin, self).__init__()
        # Attributes
        self._menu = None
        # Event Handlers
        self.Bind(event, self.OnContextMenu)

        def OnContextMenu(self, event):
            """Creates and shows the Menu"""
            if self._menu is not None:
                self._menu.Destroy()
            self._menu = wx.Menu()
            self.CreateContextMenu(self._menu)
            self.PopupMenu(self._menu)

        def CreateContextMenu(self, menu):
            """Override in subclass to create the menu"""
            raise NotImplementedError

class PanelWithMenu(wx.Panel, PopupMenuMixin):
def __init__(self, parent):
wx.Panel.__init__(self, parent)
PopupMenuMixin.__init__(self)
def CreateContextMenu(self, menu):
"""PopupMenuMixin Implementation"""
menu.Append(wx.ID_CUT)
menu.Append(wx.ID_COPY)
menu.Append(wx.ID_PASTE)
