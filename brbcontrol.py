#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  brbcontrol.py
#  
#  author: Jens Rapp
#  
#  
import urwid
import json

from canmessages import *

class LogDisplay ():
    '''
    just an inteface class for a message display
    '''
    level = ['error','warning','info','debug']

    def __init__(self):
        self.__logfield = None
        self.__loglevel = LogDisplay.level.index('info')
        pass
    
    def set_message_level(self, l='info'):
        '''
        sets the priority level of displayed messages
        if a message level is lower or equal to this, the message is displayed
        ''' 
        value = self.__loglevel
        if  l.isdigit():
            value = int(l)
            
        elif l in LogDisplay.level:
            value = LogDisplay.level.index(l)
            
        else:
            self.log('loglevel {} unknown.'.format(l),'error')
            return
            
        self.__loglevel = value
        self.log('loglevel {} set'.format(LogDisplay.level[value]),'info')

    def log(self, message, level='info'):
        '''
        append a message to the message window
        '''
        if self.__loglevel >= LogDisplay.level.index(level):
            txt = self.__logfield.text + message + '\n'
            self.__logfield.set_text(txt)
            
    def clear_messages(self,message=None):
        '''
        clears the message area
        '''
        self.__logfield.set_text('') 
        
    def set_logfield(self, logfield):
        '''
        sets the field we are logging into
        '''
        self.__logfield = logfield

        

class MainFrame (LogDisplay):
    palette = [
        ('body','black','light gray', 'standout'),
        ('header','light gray', 'dark red', 'standout'),
        ('editbx','light gray', 'dark blue'),
        ('footer','black','light gray', 'standout'),
        ]
        

    def __init__(self, bus = 'dummy'):  
        '''
        initialization - no parameters needed yet
        '''
        super().__init__()

        self.orders = { 'send' : self.send_message,
                   'add'  : self.add_message,
                   'list' : self.list_messages,
                   'quit' : self.quit,
                   'help' : self.show_help,
                   'log'  : self.set_verbosity,
                   'clear': self.clear_messages,
                 }
        
        # create ui
        self.edit= urwid.Edit(caption="Input: ", edit_text='')
        header = urwid.AttrWrap(urwid.Text('Barobo CAN Control Center (type \'help\' for help, F8 or \'quit\' for exit)'), 'header')
        footer = urwid.AttrWrap(urwid.AttrWrap(self.edit,'editbx'), 'footer')

        self.txt= urwid.Text("")
        listbox_content = [self.txt]
        listbox = urwid.ListBox(urwid.SimpleListWalker(listbox_content))
        self.frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header, footer=footer, focus_part='footer')

        self.set_logfield(self.txt)
        self.can = CanControl(self, bus)
        self.parser = MessageParser()
        self.history = []
        self.hpos = -1
    
    def show_help(self, messages):
        '''
        display system help
        '''
        self.log('send : Send a message')
        self.log('list : List known messages')
        self.log('add  : Add a message')
        self.log('clear: Clear message screen')
        self.log('log  : set log level')
        self.log('help : Show this help')
        self.log('quit : Exit the program')
        
        pass

    def send_message(self, tok):
        '''
        display system help
        '''
        try:
            message = self.parser.create_message(tok)
            self.can.send_message(message)
        except can.CanError as e:
            raise CanControlException(str(e))
        
    def add_message(self, tok):
        '''
        display system help
        '''
        self.parser.add_messagetype(tok)
        
    def quit(self, tok = []):
        '''
        exit
        '''
        raise urwid.ExitMainLoop()
        
    def list_messages(self, tok):
        '''
        display system help
        '''
        self.log('CAN-Messages')
        self.log(self.parser.list_messages(tok))
        self.log('Type \'list [ordername]\' for mor information') 

            
    def set_verbosity(self, messages):
        '''
        display system help
        '''
        level = self.set_message_level(messages[0])
    
    
    def handle_order(self,txt):
        '''
        reacts on order input
        '''
        if txt != '':
            self.log(txt,'debug')
            tok = txt.split(' ')
            order = tok.pop(0)

            if order in self.orders:
                try:
                    handler = self.orders[order]

                    self.log('calling handler {}'.format(handler),'debug')
                    self.log('   with parameters ({})'.format(','.join(tok)),'debug')
                        
                    handler(tok)
                    
                    self.log('done','debug')
                except CanControlException as e:
                    self.log(str(e),'error')
                
            else:
                self.log('Unknown order "{}"'.format(txt),'error')

            self.edit.set_edit_text('')
            
    
    def handle_key(self, key):
        '''
        event handler
        reacts on a key input
        '''
        if key == 'f8':
            self.quit()
        elif key == 'up':
            if self.hpos+1 < len(self.history):
                self.hpos += 1
                self.edit.set_edit_text(self.history[self.hpos])
        elif key == 'down':
            if self.hpos > 0:
                self.hpos -= 1
                self.edit.set_edit_text(self.history[self.hpos])
        elif key == 'page down':
            self.log('scrolling is not yet functional')
        elif key == 'page up':
            self.log('scrolling is not yet functional')            
        elif key == 'enter':
            txt = self.edit.edit_text
            self.history.insert(0,txt)
            self.hpos = -1
            self.handle_order(txt)

    
    def run(self):
        '''
        initialize the main loop
        '''
        loop = urwid.MainLoop(self.frame, self.palette, unhandled_input=self.handle_key)
        loop.run()    

        
'''
main function handler
'''
def main(args):
    bus = 'dummy'

    if len(args) == 2:
        bus = args[1]

    MainFrame(bus).run()
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
