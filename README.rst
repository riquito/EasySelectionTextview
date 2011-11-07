EasySelectionTextview, easy interaction with GTK+ Textview selections
=====================================================================

This library simplify the interaction with GTK+ Textview selections providing a richer number of signals.

To use it you just need to inherit one class: it will give you access to these signals

* selection-toggle => textview,(bool)hasSelection
* selection-change => textview,startIter,endIter,direction (0 unmoved, 1 left to right, -1 right to left)
* selection-start  => textview,startIter,endIter
* selection-end    => textview,startIter,endIter

**selection-toggle** is nothing new: it just notifies whether text has become selected or unselected. It could be fired multiple times during a selection (consider a selection via mouse moving in one direction first and then coming back).

**selection-start** and **selection-end** are emitted once during a selection, which means at mouse press and release (if selections are involved) or each time the selection is modified using the keyboard.

**selection-change** fires at each visible change when dragging a selection with the mouse, without waiting for the release of the button, or each time the selection is modified with a keystroke.
It is guaranteed to be emitted between ``selection-start`` and ``selection-end`` signals.

startIter and endIter are GtkTextIter or None.

A **selecting()** method is inherited too: it returns a boolean telling if there is a selection in progress. It could turn to be useful if you need to monitor such a thing.

A simple yet complete example: ::

    try: from gi.repository import Gtk as gtk
    except ImportError:  import gtk
    from easy_selection_textview import EasySelectionTextview
    
    class TestTextview(EasySelectionTextview):
        def __init__(self):
            super(TestTextview,self).__init__()
            self.connect('selection-change',self.on_selection_changed)
        
        def on_selection_changed(self,textview,startIter,endIter,direction):
            print('Selection has changed!')
            if startIter:
                print('now is %s\n' % textview.get_buffer().get_text(startIter,endIter,False))
    
    dialog = gtk.Dialog()
    dialog.vbox.pack_start(TestTextview(),True,True,0)
    dialog.show_all()
    dialog.run()


You can also just run the .py file, it will start a more interesting test program monitoring changes to the selection.

It supports both GTK+ 2.x and 3.x (needing either pygtk or pygobject), and python 2.5 or superior.

EasySelectionTextview is licensed under GPLv3.

Unless cool ideas come to mind, the library is considered to be feature complete, so it will only receive bugfixes (hopefully zero).

Copyright © 2011 Riccardo Attilio Galli <riccardo@sideralis.org> [http://www.sideralis.org]
