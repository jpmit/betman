import numpy as np
import matplotlib
#matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import wx
import models
import const

class GraphFrame(wx.Frame):
    def __init__(self, key):
        wx.Frame.__init__(self, None, title=key)

        # store key, this is used so that we can track when the frame
        # is killed
        self.key = key
        self.panel = CanvasPanel(self)

def _normalise_color(color):
    """Convert rgb 0-255 tuple to rgb 0-1 tuple."""

    new_col = np.array(color) / 255.0
    return tuple(new_col)

class CanvasPanel(wx.Panel):
    LINEWIDTH = 3.0
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111, axisbg = 'black')
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        self.InitPlot()

    def InitPlot(self):
        """Initialise the plot by creating the line objects etc."""

        # we plot the xdata from the model, and set y data to None,
        # meaning that the ydata won't show until the line is
        # refreshed.
        npoints = models.GraphPriceModel.NPOINTS
        xdata = range(npoints)
        ydata = [None]*npoints

        # use the same colors as for the buttons in the GUI
        self.bdaqback_line, = self.axes.plot(xdata, ydata,
                                             color=_normalise_color(const.LYELLOW),
                                             linewidth=CanvasPanel.LINEWIDTH)
        self.bdaqlay_line, = self.axes.plot(xdata, ydata,
                                            color=_normalise_color(const.LGREEN),
                                            linewidth=CanvasPanel.LINEWIDTH)
        self.bfback_line, = self.axes.plot(xdata, ydata,
                                           color=_normalise_color(const.LBLUE),
                                           linewidth=CanvasPanel.LINEWIDTH)
        self.bflay_line, = self.axes.plot(xdata, ydata,
                                          color=_normalise_color(const.LPINK),
                                          linewidth=CanvasPanel.LINEWIDTH)

    def draw(self):
        t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2 * np.pi * t)
        self.axes.plot(t, s)

    def OnUpdatePrices(self, gmodel):
        print "I'm redrawing the panel!!!"

        # update the y axis data from the model
        self.bdaqback_line.set_ydata(gmodel.bdaqback)
        self.bdaqlay_line.set_ydata(gmodel.bdaqlay)
        self.bfback_line.set_ydata(gmodel.bfback)
        self.bflay_line.set_ydata(gmodel.bflay)

        # recompute the data limits
        self.axes.relim()
        # auto scale the axes
        self.axes.autoscale_view()
        
        # this should help to update without needing to resize the
        # canvas?
        self.figure.canvas.draw()

if __name__ == "__main__":
    # test app
     app = wx.App(False)
     frame = wx.Frame(None)
     frame.panel = CanvasPanel(frame)
     frame.Show(True)
     app.SetTopWindow(frame)
     app.MainLoop()
