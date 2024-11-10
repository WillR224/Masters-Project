import wx
import sys
import threading
import time
import TestFunctions as tests
from colorama import Fore, Style


class MyFrame(wx.Frame):
        
    def __init__(self, title):
    
        self.abortTest=False
    
        wx.Frame.__init__(self, None, title=title, pos=(150,150), size=(600,400))
        self.Maximize(True)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.OnClose, m_exit)
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        
        self.statusbar = self.CreateStatusBar()

        self.panel = wx.Panel(self)
        
        '''
        nb=wx.Notebook(self.panel)
        tab1=TabOne(nb)
        tab2=TabOne(nb)
        nb.AddPage(tab1, "Tab 1")
        nb.AddPage(tab2, "Tab 2")
        nbSizer = wx.BoxSizer()
        nbSizer.Add(nb, 1, wx.EXPAND)
        '''
        
        #Redirect text widgets
        dialogueBox = wx.BoxSizer(wx.HORIZONTAL)
        log = wx.TextCtrl(self.panel, wx.ID_ANY, size=(500,350),style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        sys.stdout=log
        #sys.stderr=log
        dialogueBox.Add(log, 0, wx.ALL , 5)

        #create boxes to put stuff in
        screenBox=wx.BoxSizer(wx.VERTICAL)
        mainbox=wx.BoxSizer(wx.HORIZONTAL)
        headerBox=wx.BoxSizer(wx.HORIZONTAL)
        footerBox=wx.BoxSizer(wx.HORIZONTAL)
        box = wx.BoxSizer(wx.VERTICAL)
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box3 = wx.BoxSizer(wx.HORIZONTAL)
        
                
        #internal parameters
        self.tests=["","IV","CV","InterStripCV"]
        self.devices=self.FindDevices()

        
        m_text = wx.StaticText(self.panel, -1, "Probestation GUI v0.1")
        m_text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        m_text.SetSize(m_text.GetBestSize())
        headerBox.Add(m_text, 0, wx.ALL, 10)
        
       

        #drop down box
        chooseTestBox = wx.BoxSizer(wx.HORIZONTAL)
        self.testDropdown = wx.ComboBox(self.panel,choices = self.tests) 
        self.selectTestText = wx.StaticText(self.panel, -1, "Select Test:")
        self.testDropdown.Bind(wx.EVT_COMBOBOX,self.SelectTest)
        chooseTestBox.Add(self.selectTestText, 0, wx.ALL, 10)
        chooseTestBox.Add(self.testDropdown, 0, wx.ALL, 10)

        
        #create all the devices we might need
        self.ps=KeithleyInterface(self,"Keithley 1 (HV Bias)")
        self.am=KeithleyInterface(self,"Keithley 2 (Ammeter)")
        self.LCR=LCRInterface(self, "LCR")

        
        b_readBack = wx.Button(self.panel, label="ReadBack")
        b_readBack.Bind(wx.EVT_BUTTON, self.readBack)
        headerBox.Add(b_readBack, 0, wx.ALL, 10)
        
        m_close = wx.Button(self.panel, wx.ID_CLOSE, "Close")
        m_close.Bind(wx.EVT_BUTTON, self.OnClose)
        headerBox.Add(m_close, 0, wx.ALL, 10)
        
        
        self.b_run = wx.Button(self.panel, label="Run test")
        self.b_run.Bind(wx.EVT_BUTTON, self.runTest)
        footerBox.Add(self.b_run, 0, wx.ALL, 10)
        
        self.b_abort = wx.Button(self.panel, label="ABORT")
        self.b_abort.Bind(wx.EVT_BUTTON, self.AbortRun)
        footerBox.Add(self.b_abort, 0, wx.ALL, 10)
        
        

        #titles for sections
        deviceTitle_text = wx.StaticText(self.panel, -1, "")
        deviceTitle_text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        deviceTitle_text.SetSize(deviceTitle_text.GetBestSize())        
        
        readBackTitle_text = wx.StaticText(self.panel, -1, "Read Back Value")
        readBackTitle_text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        #readBackTitle_text.SetBackgroundColour(wx.Colour(254,186,79))
        readBackTitle_text.SetSize(readBackTitle_text.GetBestSize())
   
        measurementTitle_text = wx.StaticText(self.panel, -1, "Test Parameters")
        measurementTitle_text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        measurementTitle_text.SetSize(measurementTitle_text.GetBestSize())
        
        #arrange all the boxes 
        self.generalBox=wx.BoxSizer(wx.VERTICAL)
        self.devicesBox=wx.BoxSizer(wx.VERTICAL)
        self.readBackBox=wx.BoxSizer(wx.VERTICAL)
        self.measurementBox=wx.BoxSizer(wx.VERTICAL)


        #mainbox.Add(nbSizer,0,wx.ALL,10)
        screenBox.Add(mainbox,0,wx.ALL,10)
        screenBox.Add(footerBox,0,wx.ALIGN_RIGHT,10)
        mainbox.Add(self.generalBox,0,wx.ALL,10)
        mainbox.Add(self.devicesBox,0,wx.ALL,10)
        mainbox.Add(self.readBackBox,0,wx.ALL,10)
        mainbox.Add(self.measurementBox,0,wx.ALL,10)
        self.generalBox.Add(headerBox,0,wx.ALL,10)
        self.generalBox.Add(box,0,wx.ALL,10)
        self.generalBox.Add(chooseTestBox,0,wx.ALL,10)
        self.generalBox.Add(dialogueBox,0,wx.ALL,5)
        self.devicesBox.Add(deviceTitle_text, 0, wx.ALL, 10)
        self.devicesBox.Add(self.ps.box,0,wx.ALL,10)
        self.devicesBox.Add(self.am.box,0,wx.ALL,10)
        self.devicesBox.Add(self.LCR.box,0,wx.ALL,10)
        self.readBackBox.Add(readBackTitle_text, 0, wx.ALL, 10)
        self.measurementBox.Add(measurementTitle_text, 0, wx.ALL, 10)
        
        #hide things that aren't needed at the start
        self.devicesBox.ShowItems(False)
        self.readBackBox.ShowItems(False)
        self.measurementBox.ShowItems(False)

        self.panel.SetSizer(screenBox)
        self.panel.Layout()
    

    def readBack(self,event):
        self.ps.ReadBack(event)
        self.am.ReadBack(event)
        self.LCR.ReadBack(event)
    
    def SetRange(self, event):
        print ("Entered new range:", event.GetString())

    def OnClose(self, event):
        dlg = wx.MessageDialog(self, 
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.ps.RampDown()
            self.Destroy()    
        
    def CreateDeviceParameter(self,device,parameter,description):

        label = wx.StaticText(self.panel, -1, description)
        textBox = wx.TextCtrl(self.panel, -1, "", style = wx.TE_PROCESS_ENTER | wx.TE_RICH,size=(125, -1))
        textBox.Bind(wx.EVT_TEXT_ENTER, lambda event: device.SetValue(event,parameter),textBox)
        textBox.Bind(wx.EVT_TEXT, self.textUpdated)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(label,0,wx.ALL,2)
        box.Add(textBox,0,wx.ALL,2)
        
        return label, textBox, box

    def textUpdated(self,event):
        #event.GetEventObject().SetBackgroundColour(wx.Colour(255,140,0))
        event.GetEventObject().SetBackgroundColour(wx.Colour(254,186,79))
        
    def FindDevices(self):
        print("Looking for devices:")
        return ["2410","LCR"]
        
    def SelectTest(self,event):   
        self.test=event.GetString()

        #Show boxes for devices and measurements
        if self.test != "":
            self.devicesBox.ShowItems(True)
            self.readBackBox.ShowItems(True)
            self.measurementBox.ShowItems(True)
        else:
            self.devicesBox.ShowItems(False)            
            self.readBackBox.ShowItems(False)            
            self.measurementBox.ShowItems(False)
        
        #show appropriate devices for test
        if self.test=="IV":
            self.ps.box.ShowItems(True)
            self.am.box.ShowItems(False)
            self.LCR.box.ShowItems(False)
        elif self.test=="CV":
            self.ps.box.ShowItems(True)
            self.am.box.ShowItems(False)
            self.LCR.box.ShowItems(True)
        elif self.test=="InterStripCV":
            self.ps.box.ShowItems(True)
            self.am.box.ShowItems(True)
            self.LCR.box.ShowItems(True)
        elif self.test=="":
            print("No test selected")
        
        #show appropriate parameters for test


        self.panel.Layout()

    def runTest(self,event):
        print("Running test",self.testDropdown.GetStringSelection())
        self.b_run.Disable()
        
        x = threading.Thread(target=tests.threadingTestFunction, args=(self,),daemon=True)
        x.start()
        
    def AbortRun(self,event):
        self.abortTest=True
        print("Called abort")
        
    def LoadFile(self,event):  
        with wx.FileDialog(self, "Open XYZ file", wildcard="XYZ files (*.txt)|*.txt",style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
        
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            print(pathname)
            #try:
            #    with open(pathname, 'r') as file:
            #        self.doLoadDataOrWhatever(file)
            #except IOError:
            #    wx.LogError("Cannot open file '%s'." % newfile)
        

    
# Define the tab content as classes:
class TabOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is the first tab", (20,20))    
    
    
class KeithleyInterface():

    def __init__(self,frame, name):
        self.compliance=10E-9
        self.range=100E-9
        self.device= None
        self.auto=False
        self.name=name
        self.box=wx.BoxSizer(wx.VERTICAL)
        print("Making", name," object")
        
        #title
        title = wx.StaticText(frame.panel, -1, name)
        title.SetFont(wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD))
        title.SetSize(title.GetBestSize())

        #drop down menu for device
        chooseDeviceBox = wx.BoxSizer(wx.HORIZONTAL)
        self.deviceDropdown = wx.ComboBox(frame.panel,choices = frame.devices) 
        self.deviceText = wx.StaticText(frame.panel, -1, "Select Device:")
        self.deviceDropdown.Bind(wx.EVT_COMBOBOX,self.SelectDevice)
        chooseDeviceBox.Add(self.deviceText, 0, wx.ALL, 10)
        chooseDeviceBox.Add(self.deviceDropdown, 0, wx.ALL, 10)
        
        #generic parameters
        autoLabel,autoText,autoBox=frame.CreateDeviceParameter(self,parameter="auto",description="auto")
        rangeLabel,rangeText,rangeBox=frame.CreateDeviceParameter(self,parameter="range",description="range")
        complianceLabel,complianceText,complianceBox=frame.CreateDeviceParameter(self,parameter="compliance",description="compliance")
        
        self.box.Add(title, 0, wx.ALIGN_RIGHT, 1)
        self.box.Add(chooseDeviceBox, 0, wx.ALIGN_RIGHT, 1)
        self.box.Add(autoBox, 0, wx.ALIGN_RIGHT, 1)
        self.box.Add(rangeBox, 0, wx.ALIGN_RIGHT, 1)
        self.box.Add(complianceBox, 0, wx.ALIGN_RIGHT, 1)
        self.box.ShowItems(False) 
        
    def RampDown(self):
        print("Calling ramp down on powersupply")
        return 1
      
    def SetValue(self,event,parameter):
        #here we should have a loop that checks if the parameter is one we expect, if so set it, if not throw an error
        event.GetEventObject().SetBackgroundColour(wx.GREEN)
        if (parameter=='auto'):
            self.auto=event.GetString()
        elif (parameter=='range'):
            self.range=event.GetString()    
        elif (parameter=='compliance'):
            self.compliance=event.GetString()  
        else:
            print("This isn't implemented yet, how did you manage to see this?")
            event.GetEventObject().SetBackgroundColour(wx.RED)
    
    def SelectDevice(self,event):
        self.device=event.GetString()
    
    def ReadBack(self,event):
        print("\nReading back info from:",self.name)
        print("Auto=",self.auto)
        print("Range=",self.range)
        print("Compliance=",self.compliance)
        print("Device=",self.device)
        
   
    
class LCRInterface():

    def __init__(self,frame,name):
        self.device= None
        self.amplitude=0.1 #V
        self.frequency=10 #kHz
        self.name=name
        self.box=wx.BoxSizer(wx.VERTICAL)
        print("Making LCR object")
        
        #title
        title = wx.StaticText(frame.panel, -1, name)
        title.SetFont(wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD))
        title.SetSize(title.GetBestSize())
        #find available devices and pick one
        
        #drop down menu for device
        chooseDeviceBox = wx.BoxSizer(wx.HORIZONTAL)
        self.deviceDropdown = wx.ComboBox(frame.panel,choices = frame.devices) 
        self.deviceText = wx.StaticText(frame.panel, -1, "Select Device:")
        self.deviceDropdown.Bind(wx.EVT_COMBOBOX,self.SelectDevice)
        chooseDeviceBox.Add(self.deviceText, 0, wx.ALL, 10)
        chooseDeviceBox.Add(self.deviceDropdown, 0, wx.ALL, 10)
        
        #open correction
        self.doOpenCorrectionButton = wx.Button(frame.panel, wx.ID_CLOSE, "doOC")
        self.doOpenCorrectionButton.Bind(wx.EVT_BUTTON, self.doOpenCorrection)
        
        #read values back
        self.readBackButton = wx.Button(frame.panel, wx.ID_CLOSE, "ReadBack")
        self.readBackButton.Bind(wx.EVT_BUTTON, self.ReadBack)
        
        buttonBox = wx.BoxSizer(wx.HORIZONTAL)       
        buttonBox.Add(self.doOpenCorrectionButton, 0, wx.ALL, 10)
        buttonBox.Add(self.readBackButton, 0, wx.ALL, 10)

        #Parameters requiring text input
        amplitudeLabel,self.amplitudeText,amplitudeBox=frame.CreateDeviceParameter(self,parameter="Amplitude",description="amplitude")
        
        self.box.Add(title, 0, wx.ALIGN_RIGHT, 1)
        self.box.Add(chooseDeviceBox, 0, wx.ALIGN_RIGHT, 1)
        self.box.Add(buttonBox, 0, wx.ALIGN_RIGHT, 1)
        self.box.Add(amplitudeBox, 0, wx.ALIGN_RIGHT, 1)
        self.box.ShowItems(False) 
        
    def RampDown(self):
        print("Calling ramp down on powersupply")
        return 1
      
    def SetValue(self,event,parameter):
        #here we should have a loop that checks if the parameter is one we expect, if so set it, if not throw an error
        if (parameter=='amplitude'):
            self.amplitude=event.GetString() 

    
    def doOpenCorrection(self,event):
        print("I am doing an open correction")
    
    def SelectDevice(self,event):
        self.device=event.GetString()

    def ReadBack(self,event):
        print("\nReading back info from:",self.name)
        print("Device=",self.device)
        print("Amplitude=",self.amplitude)
        print("Current frequency=",self.frequency)
        print("Name=",self.name)
        
        print("Raw value of amplitude= ",self.amplitudeText.GetValue())
            