#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  brbcontrol.py
#  
#  author: Jens Rapp
#  
#  Copyright 2020 Jens Rapp <rapp.jens@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
import urwid
import urwid.curses_display

import json

from canmessages import *

class LogDisplay ():
    '''
    just an inteface class for a message display
    '''
    level = ['error','warning','info','debug']
    

    def __init__(self):
        '''
        simple constructor
        creates a listbox for log entries
        '''
        self.__loglevel = LogDisplay.level.index('info')
        self.__entries = []
        self.__walker = urwid.SimpleFocusListWalker(self.__entries)
        self.listbox = urwid.ListBox(self.__walker)
        self.ui = urwid.curses_display.Screen()
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
            txt = urwid.Text(message)
            self.__walker.append(txt)
            self.listbox.set_focus(self.__walker.positions(True)[0])
            
    def clear_messages(self,message=None):
        '''
        clears the message area
        '''
        self.__walker.clear()
        
        

class MainFrame (LogDisplay):
    '''
    the mainframe for my application
    '''
    palette = [
        ('body','black','light gray', 'standout'),
        ('header','light gray', 'dark red', 'standout'),
        ('editbx','light gray', 'dark blue'),
        ('footer','black','light gray', 'standout'),
        ]
    
    helptext =  'send : Send a message\n' \
            'list : List known messages\n'\
            'add  : Add a message\n'\
            'clear: Clear message screen\n'\
            'log  : Set log level\n'\
            'help : Show this help (type help [order] for more specific help)\n'\
            'quit : Exit the program\n'
            
    helporder = {
            'send' : 'Sends a message. usage: send [messagename] parameter parameter ...\nExample\n send move 400000 2000 100',
            'list' : 'Without parameter: Lists all can order names. More specific with order name as parameter.',
            'add'  : 'Adds a new message type.\n usage: add [messagename] parameter parameter ..\n' \
                    ' Parameters are defined as [name]:[type]\n  Possible types are\n'\
                    '   c for char\n   i8 for 8 bit integer\n   i16 for 16 bit integer\n   i32 for 32 bit integer\n'\
                    ' Example:\n add move destination:i32 speed:i16 acceleration:i16',
                    
            'clear' : 'No parameters neccessary. just type clear and console clears.',
            'log' : 'Sets the log level. possible parameters: error, warning, info or debug',
            'help' : 'Show help message. Type help [order] for more specific help',
            'quit' : 'Just type quit to exit',
        }
    
    frameheading = 'My CAN Control Center (type \'help\' for help, F8 or \'quit\' for exit)'

    def __init__(self, bus = 'can0'):  
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
        header = urwid.AttrWrap(urwid.Text(MainFrame.frameheading), 'header')

        self.edit= urwid.Edit(caption="Input: ", edit_text='')
        footer = urwid.AttrWrap(urwid.AttrWrap(self.edit,'editbx'), 'footer')

        self.frame = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'), header=header, footer=footer, focus_part='footer')

        self.can = CanControl(self, bus)
        self.parser = MessageParser()
        self.history = []
        self.hpos = -1
    
    def show_help(self, messages):
        '''
        display system help
        '''
        if len (messages) == 0:
            self.log(MainFrame.helptext)
        else:
            for msg in messages:
                if msg in MainFrame.helporder:
                    self.log(MainFrame.helporder[msg])
                else:
                    self.log('Sorry, no help for {}.'.format(msg),'warning')
            
        pass

    def send_message(self, tok):
        '''
        display system help
        '''
        try:
            message = self.parser.create_message(tok)
            self.can.send_message(message)
            self.log(self.parser.parse_message(message))
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
        self.loop.stop()
        
        
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
        elif key == 'esc':
            self.edit.set_edit_text('')
        elif key == 'up':
            if self.hpos+1 < len(self.history):
                self.hpos += 1
                self.edit.set_edit_text(self.history[self.hpos])
        elif key == 'down':
            if self.hpos > 0:
                self.hpos -= 1
                self.edit.set_edit_text(self.history[self.hpos])
        elif key == 'enter':
            txt = self.edit.edit_text
            self.history.insert(0,txt)
            self.hpos = -1
            self.handle_order(txt)

    
    def run(self):
        '''
        initialize the main loop
        '''
        self.loop = urwid.MainLoop(self.frame, self.palette, unhandled_input=self.handle_key, event_loop=urwid.AsyncioEventLoop())
        self.loop.run()    

        
'''
main function handler
'''
def main(args):
    bus = 'can0'

    if len(args) == 2:
        bus = args[1]

    MainFrame(bus).run()
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
