#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  canmessages.py
#  
#  

import can
import json
import ctypes

class CanControlException(Exception):
    def __init__(self,message):
        super().__init__(message)
    
class CanControl (can.Listener):
    '''
    the can controller
    '''
    def __init__(self, appender, canbus='can0'):
        '''
        creates a can interface... or dummy interface
        '''
        super().__init__()
        self.appender = appender
        self.canbus = canbus
        self.bus = None

        
        try :
            if (self.canbus != 'dummy'):
                self.bus = can.interface.Bus(bustype='socketcan', channel=self.canbus, bitrate=250000)
            else:
                self.bus = can.interface.Bus()

            listeners = [self]
            self.notifier = can.Notifier(self.bus, listeners)

            self.appender.log('canbus connected on {}'.format(self.canbus))

        except:
            self.appender.log('could not connect canbus')

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
        
        self.appender.log('sending message {}'.format(str(message)))
        if self.bus != None :
            self.bus.send(message)

    def __recv_message(self, msg):
        '''
        handles a received message
        '''
        self.appender.log('Received Message : {}'.format(msg))
    
    def on_error(self,exc):
        '''
        error handler
        '''
        self.appender.log("ERROR: {}".format(exc), 'error')
        pass

        
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

    def list_messages(self,text=[]): 
        ret = ''
        if len(text) != 0:
            for order in text:
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

    def add_messagetype(self, text=[]):
        '''
        appends a new order to controller
        '''
        name = text.pop(0)
        id = int (text.pop(0))
        order = {'_id' : id}
        params = {}
        for param in text:
            pname,ptype = param.split(':') 
            params.update({pname:ptype})
        
        order.update({'parameters':params})
        self.data.update({name:order})
        
        with open(self.controlfile, 'w') as fp:
            json.dump(self.data, fp, indent=2)
            
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
        if len(parameters) != len(text):
            raise CanControlException('Wrong parameter count. Having {} but expecting {}'.format(len(text),len(parameters)))
        
        data = []
        dp = 0
        for val in parameters.values():
            pass
        
        return can.Message(arbitration_id=oid, is_extended_id=False, data=data)

def main(args):
    print('wrong file. please try another')
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
