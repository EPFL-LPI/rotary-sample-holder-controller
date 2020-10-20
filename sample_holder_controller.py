#!/usr/bin/env python
# coding: utf-8

# # Sample Holder Controller
# Controls an automated sample holder controlled by an arduino.

# ## API
# 
# Utilizes an Arduino Controller for communication. Commands that differ form the standard arduino commands are listed here.
# 
# **connect():** Connects with the controller and attempts to read the steps per revolution. If the steps per revolution is not read, the default value is used.
# 
# **is_enabled():** Returns a boolean of whether the program is connected to the controller.
# 
# **step( num ):** Moves the number of sample steps provided. The motor steps to move per sample step is calculated from the steps per revolution and the number of samples spaces the holder has.
# 
# **goto( num ):** Moves to the specified sample.

# In[1]:


# import sys
# sys.path.insert( 0, '../base-classes/arduino-controller' )


# In[1]:


import time
import math
import json
import arduino_controller as arduino

# from importlib import reload


# In[3]:


# reload( arduino )


# In[8]:


class SampleHolderController( arduino.ArduinoController ):
    """
    Represents an automated sample holder controlled by an Arduino
    """
    
    def __init__( self, port, samples = 10, spr = 200, baud = 9600, timeout = 10 ):
        """
        :param port: The port for communication.
        :param samples: The number of samples spaces in the holder. [Default: 10]
        :param spr: The steps per revolution of the motor to use as default.
            Upon connection an attempt will be made to query the arduino for this value
            which will be used if obtained. [Default: 200]
        :param baud: The baud rate for communication. [Default 9600]
        :param timeout: Communication timeout in seconds. [Default: 10]
        """
        arduino.ArduinoController.__init__( 
            self, 
            port = port, 
            baud = baud, 
            timeout = timeout,
            termination_char = '\n'
        )
        self.samples = samples
        self.position = None # current motor position
        
        self.SPR = None
        self.DEFAULT_SPR = spr # steps per revolution       
            

    @property 
    def sample( self ):
        """
        Gets the sample number from the position
        """
        if self.position is None:
            return None
        
        s_width = self.SPR/ self.samples
        offset = s_width/ 2
        sample = ( self.position + offset )/ s_width
        return math.floor( sample  )
        
        
    def connect( self ):
        """
        Connects to the controller.
        Attempts to obtain the steps per revolution from the controller,
            falls back to using the default value.
        
        :raises: RuntimeError if steps per revolution could not be obtained
        """
        super().connect()
        time.sleep( 3 ) # delay to establish connection, in seconds
        
        try:
            self.SPR = self.get_spr()
            
        except:
            # could not connect
            self.SPR = self.DEFAULT_SPR
            raise RuntimeError( 
                'Could not get steps per rotation. Using default value of {} instead.'.format( self.DEFAULT_SPR ) 
            ) 
   
    
    def enable( self ):
        self.run( 'enable' )
        self.position = self.run( 'get_pos' )
        
        
    def home( self ):
        self.run( 'home' )
        self.position = 0

        
    def is_enabled( self ):
        """
        Returns whether the motor is enabled or not.
        
        :returns: True or False
        """
        resp = self.run( 'is_enabled' )
        return True if ( resp == '1' ) else False
        
        
    def move( self, steps ):
        """
        Change relative motor position.
        
        :param num: The number of steps to take.
        :raises: RuntimeError if the motor is not enabled.
        """
        if not self.is_enabled():
            raise RuntimeError( 'Motor is not enabled.' )
            
        self.run( 'move', steps )
        
        # update motor position
        self.position = ( self.position + steps )% self.SPR
    
        
    def step( self, num = 1):
        """
        Change relative sample position.
        
        :param num: The number of samples to move. [Default: 1]
        """
        steps = num*( self.SPR/ self.samples )
        self.move( steps )
        
    
    def goto( self, num = 0 ):
        """
        Goes to a specific sample.
        
        :param num: The sample number to go to. [Default: 0]
        :raises: ValueError if an invalid sample number is given.
        """
        if ( num < 0 ) or ( num > self.samples ):
            # invalid sample number
            raise ValueError( 'Invalid sample number. Must be in range [0, {}].'.format( self.samples ) )

        # move as few steps as possible
        steps = ( num - self.sample )% self.samples
        if ( steps > self.samples/ 2 ):
            # move in opposite direction
            steps -= self.samples
            
        self.step( steps )
    
        
    def offset( self, num ):
        """
        Shifts the realtive position. Used to trim the home position.
        
        :param num: The amount of steps to offset.
        """
        pos = self.position
        self.move( num )
        super().run( 'offset', -num ) # compensate for movement
        
        # reset position
        self.position = pos


# # Work

# In[9]:


# sh = SampleHolderController( 'COM4' )


# In[11]:


# sh.connect()


# In[20]:


# sh.disconnect()


# In[12]:


# sh.enable()


# In[16]:


# sh.goto( 5 )


# In[19]:


# sh.move( 5 )
# sh.sample


# In[69]:


# sh.sample


# In[ ]:




