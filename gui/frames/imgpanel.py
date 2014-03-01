import wx

class SplashPanel(wx.Panel):
    """Panel shown in main application window at startup."""
    
    def __init__(self, parent, image, *args, **kwargs):
        """
        Image is filename of image file (assumed to be a png).
        """
        
        super(SplashPanel, self).__init__(parent, *args, **kwargs)

        img = wx.Image(image, wx.BITMAP_TYPE_PNG).Scale(780, 580)
        self.sBmp = wx.StaticBitmap(self, wx.ID_ANY,
                                    wx.BitmapFromImage(img))
        sizer = wx.BoxSizer()
        sizer.Add(item=self.sBmp, proportion=1,
                  flag=wx.EXPAND | wx.ALL, border=10)
        self.SetSizerAndFit(sizer)
