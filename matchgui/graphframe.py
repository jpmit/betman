import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import wx

class GraphFrame(wx.Frame):
    def __init__(self, key):
        wx.Frame.__init__(self, None, title=key)

        # store key, this is used so that we can track when the frame
        # is killed
        self.key = key
        
        self.panel = CanvasPanel(self)

class CanvasPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

    def draw(self):
        t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2 * np.pi * t)
        self.axes.plot(t, s)

    def OnUpdatePrices(self, gmodel):
        print "I'm redrawing the panel!!!"

        npoints = len(gmodel.bdaqback)
        xpoints = np.arange(npoints)
        self.axes.plot(xpoints, np.array(gmodel.bdaqback))
        self.axes.plot(xpoints, np.array(gmodel.bdaqlay))
        self.axes.plot(xpoints, np.array(gmodel.bfback))
        self.axes.plot(xpoints, np.array(gmodel.bflay))
        # this should help to update without needing to resize the
        # canvas?
        self.figure.canvas.draw()
        pass
