#!/usr/bin/env python
# coding: utf-8

# # GUI Interface for Sample Holder
# 
# ## Requirements
# Ensure that `import-ipynb` module is installed
# 
# ## Compiling
# 1. Ensure fbs is installed `pip install fbs`
# 2. Iniate a project `python3 -m fbs startproject`
# 3. Freeze the binary `python3 -m fbs freeze`
# 4. Create an installer `python3 -m fbs installer`
# 
# ## Converting to .py
# To save this file for use as a CLI, convert it to a .py file using `jupyter nbconvert --to python <filename>`

# In[7]:


import os
import sys
import re
import math
import serial

# PyQt
from PyQt5 import QtGui

from PyQt5.QtCore import (
    Qt,
    QCoreApplication,
    QTimer,
    QThread
)

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QButtonGroup,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QLineEdit,
    QFileDialog,
    QMessageBox
)

# controller
import import_ipynb # FREEZE
import sample_holder_controller as shc


# In[14]:


class SampleHolderInterface( QWidget ):
    
    #--- window close ---
    def closeEvent( self, event ):
        self.delete_controller()
        event.accept()
        
    
    #--- destructor ---
    def __del__( self ):
        self.delete_controller()
        
    
    #--- initializer ---
#     def __init__( self, resources, samples = 10 ): # FREEZE
    def __init__( self, samples = 10 ):
        super().__init__()
        
        #--- instance variables ---
#         image_folder = resources + '/images/' # FREEZE
        image_folder = os.getcwd() + '/images/' 
    
        self.img_redLight = QtGui.QPixmap(    image_folder + 'red-light.png'    ).scaledToHeight( 32 )        
        self.img_greenLight = QtGui.QPixmap(  image_folder + 'green-light.png'  ).scaledToHeight( 32 )
        self.img_yellowLight = QtGui.QPixmap( image_folder + 'yellow-light.png' ).scaledToHeight( 32 )
        
        self.ports  = self.getComPorts()
        self.port   = None
        self.inst   = None # the instrument
        
        self.samples = samples
        self.occupied = []
        
        #--- timers ---
        
        
        #--- init UI ---
        self.init_ui()
        self.register_connections()
        
        #--- init variables ---        
        

    def init_ui( self ):
        #--- main window ---
        self.setGeometry( 100, 100, 700, 300 )
        self.setWindowTitle( 'Sample Controller' )
        
        lo_main = QVBoxLayout()
        lo_main.addLayout( self.ui_mainToolbar() )
        lo_main.addSpacing( 35 )
        lo_main.addLayout( self.ui_settings() )
        lo_main.addSpacing( 35 )
        lo_main.addLayout( self.ui_commands() )
        lo_main.addSpacing( 35 )
        lo_main.addLayout( self.ui_advanced() )
        
        self.setLayout( lo_main )
        
        self.show()
       
    
    def ui_mainToolbar( self ):
        lo_mainToolbar = QHBoxLayout()
        
        self.ui_mainToolbar_comPorts( lo_mainToolbar )
        self.ui_mainToolbar_connect( lo_mainToolbar )
        self.ui_mainToolbar_enable( lo_mainToolbar )
        
        return lo_mainToolbar
    
    
    def ui_settings( self ):
        lo_settings = QVBoxLayout()
        
        self.ui_settings_occupied( lo_settings )
        
        return lo_settings
    
    
    def ui_commands( self ):
        lo_commands = QVBoxLayout()
          
        self.ui_commands_step( lo_commands )
        self.ui_commands_goto( lo_commands )
        
        return lo_commands
        
        
    def ui_advanced( self ):
        lo_advanced = QVBoxLayout()
        
        self.ui_advanced_move( lo_advanced )
        self.ui_advanced_offset( lo_advanced )
        self.update_advanced_ui()
        
        return lo_advanced
        
        
    def ui_mainToolbar_comPorts( self, parent ):
        self.cmb_comPort = QComboBox()
        self.update_ports_ui()
        
        lo_comPort = QFormLayout()
        lo_comPort.addRow( 'COM Port', self.cmb_comPort )
        
        parent.addLayout( lo_comPort )
        
    
    def ui_mainToolbar_connect( self, parent ):
        # connect / disconnect
        self.lbl_statusLight = QLabel()
        self.lbl_statusLight.setAlignment( Qt.AlignCenter )
        self.lbl_statusLight.setPixmap( self.img_redLight )
        
        self.lbl_status = QLabel( 'Disconnected' )
        self.btn_connect = QPushButton( 'Connect' )
    
        lo_statusView = QVBoxLayout()
        lo_statusView.addWidget( self.lbl_statusLight )
        lo_statusView.addWidget( self.lbl_status )
        lo_statusView.setAlignment( Qt.AlignHCenter )
        
        lo_status = QHBoxLayout()
        lo_status.addLayout( lo_statusView )
        lo_status.addWidget( self.btn_connect )
        lo_status.setAlignment( Qt.AlignCenter )
        lo_status.setAlignment( Qt.AlignTop )
        
        parent.addLayout( lo_status )
        
    
    def ui_mainToolbar_enable( self, parent ):
        # enable/disable
        self.lbl_enableLight = QLabel()
        self.lbl_enableLight.setAlignment( Qt.AlignCenter )
        self.lbl_enableLight.setPixmap( self.img_redLight )
        
        self.lbl_enable = QLabel( 'Disabled' )
        self.btn_enable = QPushButton( 'Enable' )
        
        lo_enableView = QVBoxLayout()
        lo_enableView.addWidget( self.lbl_enableLight )
        lo_enableView.addWidget( self.lbl_enable )
        lo_enableView.setAlignment( Qt.AlignHCenter )
        
        lo_enable = QHBoxLayout()
        lo_enable.addLayout( lo_enableView )
        lo_enable.addWidget( self.btn_enable )
        lo_enable.setAlignment( Qt.AlignCenter )
        lo_enable.setAlignment( Qt.AlignTop )
        
        parent.addLayout( lo_enable )
        
    
    def ui_settings_occupied( self, parent ):
        lbl_samples = QLabel( 'Occupied Samples:' )
        lbl_samples.setToolTip( 'Specify occupied sample positions.' )
        
        lo_samples = QHBoxLayout()
        lo_samples.setAlignment( Qt.AlignTop )
        lo_samples.addWidget( lbl_samples )
        
        self.cbgr_occupied = QButtonGroup( exclusive = False )
        for s in range( self.samples ):
            lbl_sample = QLabel( str( s ) )
            cb_sample = QCheckBox()
            self.cbgr_occupied.addButton( cb_sample, s )
            
            lo_sample = QVBoxLayout()
            lo_sample.addWidget( cb_sample )
            lo_sample.addWidget( lbl_sample )
            
            lo_samples.addLayout( lo_sample )
        
        # toggle all 
        self.cb_occupy_all = QCheckBox()
        lbl_all = QLabel( 'All' )
        
        lo_all = QVBoxLayout()
        lo_all.addWidget( self.cb_occupy_all )
        lo_all.addWidget( lbl_all )
        
        lo_samples.addLayout( lo_all )
        
        parent.addLayout( lo_samples )
        
        
    def ui_commands_step( self, parent ):       
        # current
        lbl_current_title = QLabel( 'Current: ' )
        
        sample = (
            str( self.inst.sample ) 
            if ( self.inst is not None ) 
            else 'None'
        )
        self.lbl_current = QLabel( sample )
        
        bold = QtGui.QFont()
        bold.setBold( True )
        self.lbl_current.setFont( bold )
        
        lo_current = QHBoxLayout()
        lo_current.addWidget( lbl_current_title )
        lo_current.addWidget( self.lbl_current )
        
        # move
        btn_prev = QPushButton( 'Previous' )
        btn_prev.setToolTip( 'Move to previous occupied sample.' )
        
        btn_next = QPushButton( 'Next' )
        btn_next.setToolTip( 'Move to next occupied sample.' )
        
        self.btngr_move = QButtonGroup()
        self.btngr_move.addButton( btn_prev, 0 )
        self.btngr_move.addButton( btn_next, 1)
        
        lo_move = QHBoxLayout()
        lo_move.addWidget( btn_prev )
        lo_move.addWidget( btn_next )
        
        # section
        lo_cmd_move = QHBoxLayout()
        lo_cmd_move.addLayout( lo_current )
        lo_cmd_move.addLayout( lo_move )
        
        parent.addLayout( lo_cmd_move )
        
        
        
    def ui_commands_goto( self, parent ):
        lbl_goto = QLabel( 'Go To:' )
        
        lo_goto = QHBoxLayout()
        lo_goto.addWidget( lbl_goto )
        
        self.btngr_goto = QButtonGroup()
        for s in range( self.samples ):
            btn_goto = QPushButton( str( s ) )
            btn_goto.setToolTip( 'Move to sample space {}.'.format( s ) )
            
            self.btngr_goto.addButton( btn_goto, s )
            lo_goto.addWidget( btn_goto )
            
        parent.addLayout( lo_goto )
        
        
    def ui_advanced_offset( self, parent ):
        offset_tt = 'Trim the home position of the holder.'
        
        self.btn_offset = QPushButton( 'Offset' )
        self.btn_offset.setToolTip( offset_tt )
        
        self.sb_offset = QSpinBox()
        self.sb_offset.setToolTip( offset_tt )
        
        lo_offset = QHBoxLayout()
        lo_offset.addWidget( self.sb_offset )
        lo_offset.addWidget( self.btn_offset )
        
        parent.addLayout( lo_offset )
        
        
    def ui_advanced_move( self, parent ):
        move_tt = 'Move the motor position the given number of steps.'
        if self.inst is not None:
            move_tt += ' This motor has {} steps per revolution.'.format( self.inst.SPR )
        
        self.btn_move = QPushButton( 'Move' )
        self.btn_move.setToolTip( move_tt )
        
        self.sb_move = QSpinBox()
        self.sb_move.setToolTip( move_tt )
        
        lo_move = QHBoxLayout()
        lo_move.addWidget( self.sb_move )
        lo_move.addWidget( self.btn_move )
        
        parent.addLayout( lo_move )
        
        
    #--- ui functionality ---
    
    def register_connections( self ):
        self.cmb_comPort.currentTextChanged.connect( self.change_port )
        self.btn_connect.clicked.connect( self.toggle_connect )  
        self.btn_enable.clicked.connect( self.toggle_enable )

        self.cbgr_occupied.buttonClicked.connect( self.update_occupied )
        self.cb_occupy_all.clicked.connect( self.toggle_occupied )
        
        self.btngr_move.buttonClicked.connect( self.step )
        self.btngr_goto.buttonClicked.connect( self.goto )
            
        self.btn_offset.clicked.connect( self.offset )
        self.btn_move.clicked.connect( self.move )

        
    def getComPorts( self ):
        """ (from https://stackoverflow.com/a/14224477/2961550)
        Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
        """
        if sys.platform.startswith( 'win' ):
            ports = [ 'COM%s' % (i + 1) for i in range( 256 ) ]
            
        elif sys.platform.startswith( 'linux' ) or sys.platform.startswith( 'cygwin' ):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob( '/dev/tty[A-Za-z]*' )
            
        elif sys.platform.startswith( 'darwin' ):
            ports = glob.glob( '/dev/tty.*' )
            
        else:
            raise EnvironmentError( 'Unsupported platform' )

        result = []
        for port in ports:
            try:
                s = serial.Serial( port )
                s.close()
                result.append( port )
                
            except ( OSError, serial.SerialException ):
                pass
            
        return result    
    
    #--- slot functions ---
        
    def change_port( self ):
        """
        Changes port and disconnects from current port if required
        """
        # disconnect and delete controller
        self.delete_controller()
          
        # update port
        self.update_port()
        
        
    def update_ports( self ):
        """
        Check available COMs, and update UI list
        """
        self.ports = self.getComPorts()
        self.update_ports_ui()
        
        
    def toggle_connect( self ):
        """
        Toggles connection between selected com port
        """
        # show waiting for communication
        self.lbl_status.setText( 'Waiting...' )
        self.lbl_statusLight.setPixmap( self.img_yellowLight )
        self.repaint()
        
        # create controller if doesn't already exist, connect
        if self.inst is None:
            try:
                self.inst = shc.SampleHolderController( self.port )
                self.inst.connect()
                
            except Exception as err:
                self.inst = None
                self.update_connected_ui( False )
                
                warning = QMessageBox()
                warning.setWindowTitle( 'Sample Holder Controller Error' )
                warning.setText( 'Could not connect\n{}'.format( err ) )
                warning.exec()
            
        else:
            self.delete_controller()
        
        # update ui
        if self.inst is not None:
            self.update_connected_ui( self.inst.connected )
            self.update_commands_ui()
            self.update_advanced_ui()
            
        else:
            self.update_connected_ui( False )

            
    def toggle_enable( self ):
        if not self.is_connected():
            return
        
        # show waiting for communication
        self.lbl_enable.setText( 'Waiting...' )
        self.lbl_enableLight.setPixmap( self.img_yellowLight )
        self.repaint()
        
        if self.inst.is_enabled():
            self.inst.disable()
            
        else:
            self.inst.enable()
            self.inst.home()
            self.update_commands_ui()
            
        self.update_enabled_ui( self.inst.is_enabled() )
        
    
    def update_occupied( self ):
        self.occupied = [] # clear for repopulation
        for cb_occ in self.cbgr_occupied.buttons():
            if cb_occ.isChecked():
                sample = self.cbgr_occupied.id( cb_occ )
                self.occupied.append( sample )
                
                
    def toggle_occupied( self ):
        state = self.cb_occupy_all.checkState()
        for cb_occ in self.cbgr_occupied.buttons():
            cb_occ.setCheckState( state )
            
        self.update_occupied()
        
        
    def step( self, step = 1 ):
        """
        Moves number of occupied sample positions.
        """
        if not self.is_enabled():
            return
        
        if len( self.occupied ) == 0:
            # no samples occupied
            warning = QMessageBox()
            warning.setWindowTitle( 'Sample Holder Controller Error' )
            warning.setText( 'No samples are occupied.' )
            warning.exec()
            return
        
        if type( step ) is QPushButton:
            # id 0 is previous, 1 is next
            step = -1 if ( self.btngr_move.id( step ) == 0 ) else 1
    
        try:
            curr = self.occupied.index( self.inst.sample )
            
        except ValueError:
            # current position unoccupied
            # find nearest occupied sample
            
            # create new list with current position inserted
            occ = self.occupied.copy()
            occ.append( self.inst.sample )
            occ.sort()
            
            # move to next sample in direction of step
            # decrement number of steps to account for moving onto position
            sign = 1 if ( step > 0 ) else -1 if ( step < 0 ) else 0
            curr = ( occ.index( self.inst.sample ) + sign )% len( occ )
            curr = self.occupied.index( occ[ curr ] )
            step += -sign* 1
            
        new = ( curr + step )% len( self.occupied )
        new = self.occupied[ new ]
        
        self.goto( new )
        
        
    def goto( self, pos = None ):
        """
        Moves to give sample position
        """
        if pos is None:
            pos = self.btngr_goto.checkedId()
            
        if type( pos ) is QPushButton:
            pos = self.btngr_goto.id( pos )
        
        if not self.is_enabled():
            return
        
        self.inst.goto( pos )
        self.update_commands_ui()

    
    def offset( self ):
        """
        Offsets the relative position, moving hodler and shifting home position.
        """
        if not self.is_enabled():
            return
        
        num = self.sb_offset.value()
        self.inst.offset( num )
        self.update_commands_ui()
        
        
    def move( self ):
        """
        Moves the sample holder the entered number of steps.
        """
        if not self.is_enabled():
            return
        
        num = self.sb_move.value()
        self.inst.move( num )
        self.update_commands_ui()
        
        
    #--- helper functions ---
    
    def delete_controller( self ):
        if self.inst is not None:
            self.inst.disable()
            self.inst.disconnect()
            del self.inst
            self.inst = None
            
            
    def parse_com_port( self, name ):
        pattern = "(\w+)\s*(\(\s*\w*\s*\))?"
        matches = re.match( pattern, name )
        if matches:
            name = matches.group( 1 )
            if name == 'No COM ports available...':
                return None
            else:
                return name
        else:
            return None
        
        
    def update_port( self ):
        self.port = self.cmb_comPort.currentText()
        
        
    def update_ports_ui( self ):
        self.cmb_comPort.clear()
        
        if len( self.ports ):
            self.cmb_comPort.addItems( self.ports )
            
        else:
            self.cmb_comPort.addItem( 'No COM ports available...' )
            
            
    def update_connected_ui( self, connected ):
        if connected == True:
            statusText = 'Connected'
            statusLight = self.img_greenLight
            btnText = 'Disconnect'
            
        elif connected == False:
            statusText = 'Disconnected'
            statusLight = self.img_redLight
            btnText = 'Connect'
            
        else:
            statusText = 'Error'
            statusLight = self.img_yellowLight
            btnText = 'Connect'
        
        self.lbl_status.setText( statusText )
        self.lbl_statusLight.setPixmap( statusLight )
        self.btn_connect.setText( btnText )
        
       
    def update_enabled_ui( self, enabled ):
        if enabled == True:
            enableText = 'Enable'
            enableLight = self.img_greenLight
            btnText = 'Disable'
            
        elif enabled == False:
            enableText = 'Disable'
            enableLight = self.img_redLight
            btnText = 'Enable'
            
        else:
            enableText = 'Error'
            enableLight = self.img_yellowLight
            btnText = 'Enable'
        
        self.lbl_enable.setText( enableText )
        self.lbl_enableLight.setPixmap( enableLight )
        self.btn_enable.setText( btnText )
        
        
    def update_commands_ui( self ):
        sample = (
            None if ( self.inst is None ) 
            else self.inst.sample
        )
        self.lbl_current.setText( str( sample ) )
        
        
    def update_advanced_ui( self ):
        if self.inst: 
            step_max = math.ceil( self.inst.SPR/ 2 )
            
            self.sb_offset.setMinimum( -step_max ) 
            self.sb_offset.setMaximum( step_max )
            
            self.sb_move.setMinimum( -step_max ) 
            self.sb_move.setMaximum( step_max )
            
    
    def is_connected( self ):   
        if self.inst is None:
            # not connected
            warning = QMessageBox()
            warning.setWindowTitle( 'Sample Holder Controller Error' )
            warning.setText( 'Not connected.' )
            warning.exec()
            return False
        
        # connected
        return True
        
    
    def is_enabled( self ):
        # check if connected
        if not self.is_connected():
            return None
        
        if not self.inst.is_enabled():
            warning = QMessageBox()
            warning.setWindowTitle( 'Sample Holder Controller Error' )
            warning.setText( 'Not enabled.' )
            warning.exec()
            return False
                    
        # enabled
        return True
    


# In[15]:


# FREEZE
app = QCoreApplication.instance()
if app is None:
    app = QApplication( sys.argv )
    
main_window = SampleHolderInterface( samples = 10)
sys.exit( app.exec_() )


# In[ ]:


# FREEZE
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '1')


# In[ ]:




