#!/usr/bin/env python

"""
  MAVProxy instructor station, UI implemented in a child process
  Created by André Kjellstrup @ NORCE
"""

from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import multiproc
from MAVProxy.modules.lib.wx_loader import wx


class CheckInstructorItem:
    """Checklist item used for information transfer
    between threads/processes/pipes"""
    def __init__(self, name, state):
        self.name = name
        self.state = state


class InstructorUI:
    """
    a checklist UI for MAVProxy
    """
    def __init__(self, title='MAVProxy: Instructor'):
        self.title = title
        self.menu_callback = None
        self.pipe_to_gui, self.gui_pipe = multiproc.Pipe()
        self.close_event = multiproc.Event()
        self.close_event.clear()
        self.child = multiproc.Process(target=self.child_task)
        self.child.start()

    def child_task(self):
        """child process - this holds all the GUI elements"""
        mp_util.child_close_fds()
        from MAVProxy.modules.lib.wx_loader import wx

        app = wx.App(False)
        app.frame = InstructorFrame(self.gui_pipe, state=self, title=self.title)
        app.frame.Show()
        app.MainLoop()

    def close(self):
        """close the UI"""
        self.close_event.set()
        if self.is_alive():
            self.child.join(2)
            print("closed")

    def is_alive(self):
        """check if child is still going"""
        return self.child.is_alive()

    def set_check(self, name, state):
        """set a status value"""
        if self.child.is_alive():
            self.pipe_to_gui.send(CheckInstructorItem(name, state))


class InstructorFrame(wx.Frame):
    """ The main frame of the console"""

    def __init__(self, gui_pipe,  state, title):
        self.state = state
        self.gui_pipe = gui_pipe
        wx.Frame.__init__(self, None, title=title, size=(500, 650), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)

        self.createLists()
        self.panel = wx.Panel(self)
        self.nb = wx.Choicebook(self.panel, wx.ID_ANY)

        # create the tabs
        self.createWidgets()

        # assign events to the buttons on the tabs
        self.createActions()

        # add in the pipe from MAVProxy
        self.timer = wx.Timer(self)
        # self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.Bind(wx.EVT_TIMER, lambda evt, notebook=self.nb: self.on_timer(evt, notebook), self.timer)
        self.timer.Start(100)

        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.panel.SetSizer(sizer)

        self.Show(True)
        self.pending = []

    # Create the checklist items
    def createLists(self):
        """Generate the checklists. Note that:
        0,1 = off/on for auto-ticked items
        2,3 = off/on for manually ticked items"""

        self.beforeAssemblyList = {
        'Confirm batteries charged':2,
        'No physical damage to airframe':2,
        'All electronics present and connected':2,
        'Bottle loaded':2,
        'Ground station operational':2
        }

        self.beforeEngineList = {
        'Avionics Power ON':2,
        'Pixhawk Booted':0,
        'Odroid Booted':2,
        'Cameras calibrated and capturing':2,
        'GPS lock':0,
        'Airspeed check':2,
        'Barometer check':2,
        'Compass check':2,
        'Flight mode MANUAL':0,
        'Avionics Power':0,
        'Servo Power':0,
        'IMU Check':0,
        'Aircraft Params Loaded':2,
        'Waypoints Loaded':0,
        'Servo and clevis check':2,
        'Geofence loaded':2,
        'Ignition circuit and battery check':2,
        'Check stabilisation in FBWA mode':2
        }

    # create controls on form - labels, buttons, etc
    def createWidgets(self):

        # create the panels for the tabs

        PanelCommon = wx.Panel(self.nb)
        boxCommon = wx.BoxSizer(wx.VERTICAL)
        PanelCommon.SetAutoLayout(True)
        PanelCommon.SetSizer(boxCommon)
        PanelCommon.Layout()

        PanelAssembly = wx.Panel(self.nb)
        boxAssembly = wx.BoxSizer(wx.VERTICAL)
        PanelAssembly.SetAutoLayout(True)
        PanelAssembly.SetSizer(boxAssembly)
        PanelAssembly.Layout()

        PanelEngine = wx.Panel(self.nb)
        boxEngine = wx.BoxSizer(wx.VERTICAL)
        PanelEngine.SetAutoLayout(True)
        PanelEngine.SetSizer(boxEngine)
        PanelEngine.Layout()

        # add the data to the individual tabs

        'Common failures'

        self.GNSS_Loss_Button = wx.Button(PanelCommon, wx.ID_ANY, "GNSS Loss")


        self.VoltageSlider = wx.Slider(PanelCommon, wx.ID_ANY, 200, 150, 500, wx.DefaultPosition, (250, -1),
                                        wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        boxCommon.Add(self.VoltageSlider)

        disCheckbox = wx.CheckBox(PanelCommon, wx.ID_ANY, "GNSS FIX")
        disCheckbox.Enable(False)
        boxCommon.Add(disCheckbox)
        boxCommon.Add(self.GNSS_Loss_Button)

        '''before assembly checklist'''
        for key in self.beforeAssemblyList:
            if self.beforeAssemblyList[key] == 0:
                disCheckBox = wx.CheckBox(PanelAssembly, wx.ID_ANY, key)
                disCheckBox.Enable(False)
                boxAssembly.Add(disCheckBox)
            if self.beforeAssemblyList[key] == 2:
                boxAssembly.Add(wx.CheckBox(PanelAssembly, wx.ID_ANY, key))

        self.AssemblyButton = wx.Button(PanelAssembly, wx.ID_ANY, "Close final hatches")
        boxAssembly.Add(self.AssemblyButton)

        self.AssemblySlider = wx.Slider(PanelAssembly, wx.ID_ANY, 200, 150, 500, wx.DefaultPosition, (250,-1),wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        boxAssembly.Add(self.AssemblySlider)

        '''before Engine Start checklist'''
        for key in self.beforeEngineList:
            if self.beforeEngineList[key] == 0:
                disCheckBox = wx.CheckBox(PanelEngine, wx.ID_ANY, key)
                disCheckBox.Enable(False)
                boxEngine.Add(disCheckBox)
            if self.beforeEngineList[key] == 2:
                boxEngine.Add(wx.CheckBox(PanelEngine, wx.ID_ANY, key))

        self.EngineButton = wx.Button(PanelEngine, wx.ID_ANY, "Ready for Engine start")
        boxEngine.Add(self.EngineButton)

        self.ShutdownButton = wx.Button(PanelEngine, wx.ID_ANY, "Ready for Shutdown")
        boxEngine.Add(self.ShutdownButton)

        # and add in the tabs
        self.nb.AddPage(PanelCommon, "Common (Copter/Plane) Failures")
        self.nb.AddPage(PanelAssembly, "1. During Assembly")
        self.nb.AddPage(PanelEngine, "2. Before Engine Start")

    # Create the actions for the buttons
    def createActions(self):
        self.Bind(wx.EVT_BUTTON, self.on_gnss_Button, self.GNSS_Loss_Button)
        self.Bind(wx.EVT_BUTTON, self.on_Button, self.AssemblyButton)
        self.Bind(wx.EVT_BUTTON, self.on_gnss_Button, self.EngineButton)

    def on_gnss_Button(self, event):
        self.gui_pipe.send("test123")

    #do a final check of the current panel and move to the next
    def on_Button( self, event ):
        win = (event.GetEventObject()).GetParent()
        for widget in win.GetChildren():
            if type(widget) is wx.CheckBox and widget.IsChecked() == 0:
                dlg = wx.MessageDialog(win, "Not all items checked", "Error", wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                return
        # all checked, go to next panel.
        win.GetParent().AdvanceSelection()

    # Special implementation of the above function, but for the last tab
    def on_ButtonLast( self, event ):
        win = (event.GetEventObject()).GetParent()
        for widget in win.GetChildren():
            if type(widget) is wx.CheckBox and widget.IsChecked() == 0:
                dlg = wx.MessageDialog(win, "Not all items checked", "Error", wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                return
        # all checked, we're done.
        dlg = wx.MessageDialog(win, "Checklist Complete", "Done", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    # Receive messages from MAVProxy and process them
    def on_timer(self, event, notebook):
        state = self.state
        win = notebook.GetPage(notebook.GetSelection())
        if state.close_event.wait(0.001):
            self.timer.Stop()
            self.Destroy()
            return
        while state.gui_pipe.poll():
            obj = state.gui_pipe.recv()
            if isinstance(obj, CheckInstructorItem):
                # go through each item in the current tab and (un)check as needed
                # print(obj.name + ", " + str(obj.state))
                for widget in win.GetChildren():
                    if type(widget) is wx.CheckBox and widget.GetLabel() == obj.name:
                        widget.SetValue(obj.state)


if __name__ == "__main__":
    # test the console
    import time

    instructor = InstructorUI()

    # example auto-tick in second tab page
    while instructor.is_alive():
        instructor.set_check("Compass Calibrated", 1)
        time.sleep(0.5)
