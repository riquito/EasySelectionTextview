#!/usr/bin/env python
# ~-~ encoding: utf-8 ~-~

"""
EasySelectionTextview, easy interaction with GTK+ Textview selections.
Copyright (C) 2011 Riccardo Attilio Galli <riccardo@sideralis.org> [http://www.sideralis.org]

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

__version__ = "1.0"

try:
    import gi
    from gi.repository import Gtk as gtk
    from gi.repository import GObject as gobject
except ImportError:
    import gtk,gobject

class EasySelectionTextview(gtk.TextView):
    __gsignals__ = {
        'selection-toggle' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_BOOLEAN,)),
        'selection-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_INT)),
        'selection-start' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        'selection-end' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))
    }
    
    def __init__(self,*args):
        super(EasySelectionTextview,self).__init__(*args)
        
        self.__has_selection = False
        self.__was_selected = False
        self.__selecting = False
        self.__prev_pos = 0
        self.__btn_pressed = False
        self.__prev_selection = (None,None)
        
        buffer = self.get_buffer()
        
        self.__prevStartMark = buffer.create_mark('prev_selection_start',buffer.get_start_iter(),True)
        self.__prevEndMark = buffer.create_mark('prev_selection_end',buffer.get_start_iter(),False)
        
        self.__update_prev_selection()
        
        buffer.connect('notify::has-selection',self.__on_selection_toggle)
        buffer.connect_after('notify::cursor-position',self.__on_notify_cursor_position)
        
        self.connect('button-release-event', self.__on_mouse_button_released)
        self.connect('button-press-event', self.__on_mouse_button_down)
    
    def selecting(self,value=None):
        """
        Return a boolean indicating if there is a selection in progress.
        It can set the internal flag if needed.
        """
        newValue = bool(value)
        if value != None and self.__selecting != newValue:
            self.__selecting = newValue
        return self.__selecting
    
    def __toggle_selection_start(self,isStarting=True):
        self.selecting(isStarting)
        if isStarting:
            self.emit('selection-start',*self.__get_prev_selection_bounds())
        else:
            self.emit('selection-end',*self.__get_selection_bounds())
    
    def __update_prev_selection(self):
        start,end = self.__get_selection_bounds()
        if start:
            buffer = self.get_buffer()
            buffer.move_mark(self.__prevStartMark,start)
            buffer.move_mark(self.__prevEndMark,end)
            self.__prev_selection = (self.__prevStartMark,self.__prevEndMark)
        else:
            self.__prev_selection = (None,None)
    
    def __get_prev_selection_bounds(self):
        start,end = None,None
        
        buffer = self.get_buffer()
        
        if self.__prev_selection[0]:
            start = buffer.get_iter_at_mark(self.__prevStartMark)
        
        if self.__prev_selection[1]:
            end = buffer.get_iter_at_mark(self.__prevEndMark)
        
        return (start,end)
    
    def __get_selection_bounds(self):
        try:
            start,end = self.get_buffer().get_selection_bounds()
        except ValueError as e: # get_selection_bounds() returned an empty tuple
            start,end = (None,None)
        
        return (start,end)
    
    def __on_notify_cursor_position(self,buffer,position):
        # XXX position is a GParamInt : how can I access the value ?
        
        current_pos = buffer.get_property("cursor-position")
        
        if current_pos != self.__prev_pos:
            # cmp is deprecated in python3.x, use (a > b) - (a < b) instead
            direction = (current_pos > self.__prev_pos) - (current_pos < self.__prev_pos)
            self.__prev_pos = current_pos
            
            if self.__btn_pressed:
                if self.__has_selection_changed():
                    if not self.selecting():
                        self.__toggle_selection_start(isStarting=True)
                    
                    self.__on_selection_changed(direction)
            else:
                self.__cursor_moved_via_keyboard(direction)
        else:
            if self.__has_selection_changed():
                self.__toggle_selection_start(isStarting=True)
                self.__on_selection_changed(0)
                self.__toggle_selection_start(isStarting=False)
    
    def __on_mouse_button_down(self,*args):
        # "button down" triggers before changes to the selection.
        self.__update_prev_selection()
        self.__btn_pressed = True
    
    def __has_selection_changed(self):
        changed = False
        start,end = self.__get_selection_bounds()
        prevStart,prevEnd = self.__get_prev_selection_bounds()
        
        if prevStart and start and prevStart.equal(start) and prevEnd.equal(end):
            pass # was selected before and it is now, and the selection hasn't changed
        elif not prevStart and not start:
            pass # wasn't selected before and it isn't now
        else:
            # selection has changed
            changed = True
        
        return changed
    
    def __on_mouse_button_released(self,textview,event):
        self.__btn_pressed = False
        
        if self.__has_selection_changed():
            self.__on_selection_changed()
        
        if self.selecting():
            self.__toggle_selection_start(isStarting=False)
    
    def __cursor_moved_via_keyboard(self,direction):
        
        if not self.__has_selection_changed():
            return
        
        start,end = self.__get_selection_bounds()
        
        extend_selection = False
        
        if not start or (start and len(self.get_buffer().get_text(start, end, False)) > 0):
            # when is 0 'toggle' signal is emitted, so 'changed' is yet emitted too
            self.__toggle_selection_start(isStarting=True)
            self.__on_selection_changed(direction)
            self.__toggle_selection_start(isStarting=False)
        else:
            # do nothing
            pass
    
    def __on_selection_toggle(self,buffer,*args):
        self.__has_selection = not self.__has_selection
        self.emit('selection-toggle',self.__has_selection)
    
    def __on_selection_changed(self,selectingDirection=0): # 1 right, -1 left, 0 unknown
        self.__update_prev_selection()
        try:
            buffer = self.get_buffer()
            start,end = buffer.get_selection_bounds()
            selected_text = buffer.get_text(start, end, False)
        except ValueError as e: # get_selection_bounds() returned an empty tuple
            start,end = (None,None)
        
        self.emit('selection-change',start,end,selectingDirection)
    

if __name__=='__main__':
    
    import logging
    logging.basicConfig(format='%(message)s',level=logging.INFO)
    
    class TestSelection(EasySelectionTextview):
        def __init__(self):
            super(TestSelection,self).__init__()
            self.get_buffer().set_text('abcdefg')
            
            self.connect('selection-toggle',self.on_selection_toggle)
            self.connect('selection-change',self.on_selection_change)
            self.connect('selection-start',self.on_selection_start)
            self.connect('selection-end',self.on_selection_end)
        
        def on_selection_toggle(self,textview,hasSelection):
            logging.info('selection toggle '+('on' if hasSelection else 'off'))
        
        def on_selection_change(self,textview,startIter,endIter,direction):
            msg = 'selection changed '
            if direction==1: 
                msg += '=> (left to rigt)'
            elif direction==-1:
                msg += '<= (right to left)'
            else:
                msg += '(unmoved)'
            
            logging.info(msg)
        
        def on_selection_start(self,textview,startIter,endIter):
            msg = 'selection [start] was: '
            if startIter:
                msg += "'%s'" % textview.get_buffer().get_text(startIter,endIter,False)
            else:
                msg += 'unselected'
            
            logging.info(msg)
        
        def on_selection_end(self,textview,startIter,endIter):
            msg = 'selection [end] is '
            if startIter:
                msg += "'%s'\n" % textview.get_buffer().get_text(startIter,endIter,False)
            else:
                msg += 'unselected\n'
            
            logging.info(msg)
    
    textview = TestSelection()
    textview.set_size_request(200,200)
    textview.show()
    
    dialog = gtk.Dialog()
    dialog.vbox.pack_start(textview,False,False,0)
    
    def on_button_clicked(*args):
        textview.get_buffer().insert(textview.get_buffer().get_iter_at_offset(0),'xyz')
    
    btn = gtk.Button('Prepend text')
    btn.show()
    btn.connect('clicked',on_button_clicked)
    dialog.vbox.pack_start(btn,False,False,0)
    
    dialog.show()
    dialog.run()
