import wx
import pythonGUI as gui

#app = wx.App(redirect=True)
app = wx.App()
frame = gui.MyFrame("TestGUI")
frame.Show()
app.MainLoop()


