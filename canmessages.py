#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  canmessages.py
#
#  Copyright 2020 Jens Rapp <tecdroid@tecdroid>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import can
import json
import ctypes


class CanControlException(Exception):
    '''
    just a stupid exception 
    '''
    def __init__(self,message):
        super().__init__(message)
    
class CanControl (can.Listener):
    '''
    the can controller
    '''
    def __init__(self, appender, parser, canbus='can0'):
        '''
        creates a can interface... or dummy interface
        '''
        super().__init__()
        self.appender = appender
        self.parser = parser
        self.canbus = canbus
        self.bus = None

        
        try :
            # create bus
            if (self.canbus != 'dummy'):
                self.bus = can.interface.Bus(bustype='socketcan_native', channel=self.canbus, bitrate=250000)
            else:
                self.bus = can.interface.Bus()

            # add listener
            listeners = [self]
            self.notifier = can.Notifier(self.bus, listeners)

            self.appender.log('canbus connected on {}'.format(self.canbus))

        except Exception as e:
            self.appender.log('could not connect canbus {}: {}'.format(self.canbus, str(e)), 'warning')

    def is_connected(self):
        '''
        returns true if connected to a real bus
        '''
        return self.bus != None

    def send_message(self,message):
        '''
         send a message to the world
         :param msgid the message to send
         :param data the data array
         :param extended tells if it is an extended message 
        '''
        self.appender.log('sending message {}'.format(str(message)),'debug')
        if self.is_connected() :
            self.bus.send(message)

    def on_message_received(self, msg):
        '''
        handles a received message
        :param msg the message to handle
        '''
        parsed = self.parser.parse_message(msg)
        self.appender.log('Received Message : {}'.format(msg),'debug')
        self.appender.log('Received Message : {}'.format(parsed),'info')


class MessageParser ():
    '''
    this creates a can message from orders
    '''
    def __init__(self, controlfile='canorders.json'):
        '''
        read the controlfile if exists
        '''
        self.controlfile = controlfile
        self.data = {}
        try:
            with open(self.controlfile) as fp:
                self.data = json.load(fp)
        except:
            pass

    def list_messages(self,parameters=[]): 
        '''
        print a list of all known messages
        '''
        ret = ''
        if len(parameters) != 0:
            for order in parameters:
                if order in self.data:
                    item = dict(self.data[order])
                    ret += json.dumps(item)
                    ret += '\n'
                else:
                    raise CanControlException('Order {} not existent!'.format(order))
        else:
            for order in self.data.keys():
                ret += '  order {}\n'.format(order)
        
        return ret

    def add_messagetype(self, parameters=[]):
        '''
        appends a new order to controller
        '''
        name = parameters.pop(0)
        id = int (parameters.pop(0))
        order = {'_id' : id}
        params = {}
        for param in parameters:
            pname,ptype = param.split(':') 
            params.update({pname:ptype})
        
        order.update({'parameters':params})
        self.data.update({name:order})
        
        with open(self.controlfile, 'w') as fp:
            json.dump(self.data, fp, indent=2)
    
    def parse_message(self, message:can.Message):
        '''
        parses a can message and receives it's input
        '''
        id = message.arbitration_id
        data = message.data
        output = ''
        
        # if message known, parse it
        for key in self.data.keys():
            mtype = self.data[key]
            if mtype['_id'] == id:
                output += '  - id: {}'.format(id)
                parameters = mtype['parameters']
                pos = 0
                for par in parameters.keys():
                    ptype = parameters[par]
                    val = 0
                    if ptype == 'i8':
                        val = int.from_bytes(data[:1], byteorder='big', signed=True)
                        data[0] = []
                    elif ptype == 'i16':
                        val = int.from_bytes(data[0:2], byteorder='big', signed=True)
                        data[0:2] = []
                    elif ptype == 'i32':
                        val = int.from_bytes(data[0:4], byteorder='big', signed=True)
                        data[0:4] = []
                    else:
                        val = chr(data[0])
                        data[0] = []
                    
                    output += '  - {} : {}'.format(par,val)
                return output
                
        # in case message unknown
        return str(message)
            
    def create_message(self, text=[]):
        '''
        create a can message from text imput
        :param text is the input as array
        '''
        
        oname = text.pop(0)
        
        if not oname in self.data:
            raise CanControlException('Order {} not existent!'.format(oname))
        
        order = self.data[oname]
        
        oid = order['_id']
        parameters =  order['parameters']
        pkeys = list(parameters.keys())
        if len(parameters) != len(text):
            raise CanControlException('Wrong parameter count. Having {} but expecting {}'.format(len(text),len(parameters)))
        
        data = bytearray()
        try:
            for index,val in enumerate(parameters.values()):
                par = text[index]
                i = int(par)
                bi = 0
                if val == 'i8':
                    bi = i.to_bytes(length=1, byteorder='big', signed=True)
                if val == 'i16':
                    bi = i.to_bytes(length=2, byteorder='big', signed=True)
                if val == 'i32':
                    bi = i.to_bytes(length=4, byteorder='big', signed=True)
                if val == 'c':
                    bi = par.encode('utf-8')
                data.extend(bi)
                pass
        except Exception as e:
            raise CanControlException('Parameter {}: {}'.format(pkeys[index],str(e)))
            
        if len(data) > 8:
            raise CanControlException('Message data set too long: {}'.format(data))
            
        return can.Message(arbitration_id=oid, is_extended_id=False, data=data)

def main(args):
    print('wrong file. please try another')
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
