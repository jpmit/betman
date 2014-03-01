import wx
import os

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, size=(800, 600), title="Match GUI")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        
        return True

class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE,
                 name="MyFrame"):
        super(MyFrame, self).__init__(parent, id, title,
                                      pos, size, style, name)
        # Attributes
        self.panel = BoxSizerPanel(self)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 0.2, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetInitialSize()
        #self.panel.SetBackgroundColour(wx.BLACK)

        # Logo
        path = os.path.abspath("./logo.png")
        icon = wx.Icon(path, wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon)

class BoxSizerPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(BoxSizerPanel, self).__init__(parent, *args, **kwargs)

        # Attributes
        self._field1 = wx.TextCtrl(self)
        self._field2 = wx.TextCtrl(self)

        # Layout
        self._DoLayout()

    def _DoLayout(self):
        """Layout the controls"""
        vsizer = wx.BoxSizer(wx.VERTICAL)
        field1_sz = wx.BoxSizer(wx.HORIZONTAL)
        field2_sz = wx.BoxSizer(wx.HORIZONTAL)

        # Make the labels
        field1_lbl = wx.StaticText(self, label="Field 1:")
        field2_lbl = wx.StaticText(self, label="Field 2:")

        # 1) HORIZONTAL BOXSIZERS
        field1_sz.Add(field1_lbl, 0,
                      wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        field1_sz.Add(self._field1, 1, wx.EXPAND)

        field2_sz.Add(field2_lbl, 0,
                      wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 40)
        field2_sz.Add(self._field2, 1, wx.EXPAND)

        # 2) VERTICAL BOXSIZER
        vsizer.AddStretchSpacer()
        BOTH_SIDES = wx.EXPAND|wx.LEFT|wx.RIGHT
        vsizer.Add(field1_sz, 0, BOTH_SIDES|wx.TOP, 50)
        vsizer.AddSpacer(15)
        vsizer.Add(field2_sz, 0, BOTH_SIDES|wx.BOTTOM, 50)
        vsizer.AddStretchSpacer()

        # Finally assign the main outer sizer to the panel
        self.SetSizer(vsizer)

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()

## class MainWindow(wx.Frame):
##     def __init__(self, parent):
##         self.app = wx.App(False)
##         wx.Frame.__init__(self, parent, size=(800,600))
##         self.draw_ui()

##     def main_loop(self):
##         self.Show()
##         self.app.MainLoop()

##     def draw_ui(self):
##         """Draw welcome screen with events listed down side."""

##         from betman.matchmarkets.matchconst import EVENTMAP
##         # BDAQ event names
##         enames = EVENTMAP.keys()
##         enames.sort()

##         # need a panel apparently(?)
##         pnl = wx.ScrolledWindow(self)
##         for (i, name) in enumerate(enames):
##             ebtn = wx.Button(pnl, label = name, pos = (20, 30*(2*i + 1)))

## frame = MainWindow(None)
## frame.main_loop()

