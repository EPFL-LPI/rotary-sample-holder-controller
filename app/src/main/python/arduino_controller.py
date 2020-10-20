#!/usr/bin/env python
# coding: utf-8

# # Arduino Controller
# Communicates with an arduino using the standard `run[ cmd, *args ]` format, expecting a JSON response with keys `status` and `command`, and possibly `response` and/or `id`.

# ## API
# Parameters `port`, `baud`, and `timeout` ensure they are not being changed while the port is open, and raise a `RuntimeError` if it is.
# 
# **is_connected():** Returns if the port is open.
# 
# **connect():** Opens the port.
# 
# **disconnect():** Closes the port.
# 
# **run( name, \*args):** Runs the `name` command with passed arguments.
#     `run[ name, \*args ]`
#     
# **read_response():** Reads the port, and converts the JSON response to a Python object.

# In[17]:


import serial
import json
import logging


# In[49]:


class ArduinoController:
    """
    Represents an arduino controller using the standard 
        run[ cmd, *args ] format, expecting a JSON response with 
        keys 'status' and 'command', and possibly 'response' and/or 'id'.
    """
    
    def __init__( 
        self, 
        port, 
        baud = 9600, 
        timeout = 2, 
        read_attempts = 3,  
        termination_char = None
    ):
        """
        :param port: The communication port.
        :param baud: The baud rate. [Default: 9600]
        :param timeout: The communication timeout in seconds. [Default: 2]
        :param read_attempts: The number of times to attempts 
            reading data before timing out. [Default: 3]
        :param termination_char: Character to append to all written strings.
            [Default: None]
        """
        self.__port = port
        self.__baud = baud
        self.__timeout = timeout
        self.__inst = serial.Serial()
        
        self.debug = False
        self.read_attempts = read_attempts
        self.termination_char = termination_char
        
        
    def __del__( self ):
        """
        Ensures the communication port is closed before deletion.
        """
        if self.__inst is not None and self.__inst.is_open:
            self.__inst.close()
            
        self.__inst = None
        
        
    def __getattr__( self, name ):
        """
        Passes arbitrary run[] commands to the arduino.
        
        :param name: The name of the command to run.
        :returns: A function that accepts arbitrary parameters 
            and runs self.run( name, *args ).
        """
        def call( *args ):
            return self.run( name, *args )
            
        return call
        
        
    @property
    def port( self ):
        return self.__port
    
    @port.setter
    def port( self, port ):
        """
        :raises RuntimeError: If the port is open.
        """
        if self.is_connected():
            raise RuntimeError( "Can not change port while connected" )
            
        self.__port = port
        self.__inst.port = port
        
        
    @property
    def baud( self ):
        return self.__baud
    
    @baud.setter
    def baud( self, baud ):
        """
        :raises RuntimeError: If the port is open.
        """
        if self.is_connected():
            raise RuntimeError( "Can not change baud while connected" )
            
        self.__baud = baud
        self.__inst.baudrate = baud
        
        
    @property
    def timeout( self ):
        return self.__baud
    
    @timeout.setter
    def timeout( self, timeout ):
        """
        :raises RuntimeError: If the port is open. 
        """
        if self.is_connected():
            raise RuntimeError( "Can not change timeout while connected" )
            
        self.__timeout = timeout
        self.__inst.timeout( timeout )
        
    @property    
    def connected( self ):
        """
        :returns: True is the port is open, otherwise False.
        """
        return self.__inst.is_open
    
    
    def connect( self ):
        """
        Opens the port for communication with the set parameters.
        
        :raises RuntimeError: If the port is already open.
        """
        if self.__inst.is_open:
            raise RuntimeError( 'Already connected' )
            
        self.__inst.baudrate = self.__baud
        self.__inst.port = self.__port
        self.__inst.timeout = self.__timeout
        self.__inst.open()
        
        
    def disconnect( self ):
        self.__inst.close()
    
    
    def run( self, name, *args ):
        """
        Runs a command and listens for response, returning approriate values.
        
        :param name: The command to run
        :returns: If one of 'response' or 'id' keys are avaialble 
            returns the associated value. If both are available 
            returns a dictionary. None if neither are available.
        :raises RuntimeError: If the command has an error status.
        """
        cmd = 'run[ {}'.format( name )
        for arg in args:
            cmd += ', {}'.format( arg )
        cmd += ' ]'
        
        if self.termination_char is not None:
            cmd += self.termination_char
            
        self.__inst.write( bytes( cmd, 'utf-8' ) )
        resp = self.read_response()
        
        if resp[ 'status' ] == 'error':
            # command failed
            raise RuntimeError( 'Command failed: {}'.format( resp[ 'command'] ) )
    
        keys = resp.keys()
        if ( 'response' in keys ) and ( 'id' in keys ):
            return {
                'response': resp[ 'response' ],
                'id': resp[ 'id' ]
            }
        
        elif 'response' in keys:
            return resp[ 'response' ]
        
        elif 'id' in keys:
            return resp[ 'id' ]
        
        else:
            return None
        
    
    def read_response( self ):
        """
        Reads the JSON response from the arduino.
        
        :returns: The JSON object loaded into a Python object.
        :raises RuntimeError: If the data read times out
        """
        resp = b''
        curr = None
        resp_len = len ( resp )
        attempts = 0
        
        while curr != b'}' and attempts < self.read_attempts:
            # read until end of json
            curr = self.__inst.read()
            resp += curr
            
            # check if data read in
            if len( resp ) == resp_len:
                # no data read in
                attempts += 1
                
            resp_len = len ( resp )
            
        if attempts == self.read_attempts:
            # data read timed out
            raise RuntimeError( 'Data read timed out with response: {}'.format( resp ) )
            
        return json.loads( resp )


# # Work

# In[50]:


# ac = ArduinoController( 'COM4', termination_char = '\n' )


# In[51]:


# ac.connect()


# In[66]:


# ac.get_spr()


# In[47]:


# ac.disconnect()


# In[53]:


# ac.echo( 'hi' )


# In[ ]:




