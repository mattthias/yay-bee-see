#!/usr/bin/env python
# Copyright 2008 by Ben Whley Sittler and Wade Brainerd.  
# This file is part of YayBeeSee.
#
# YayBeeSee is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# YayBeeSee is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with YayBeeSee.  If not, see <http://www.gnu.org/licenses/>.
"""YayBeeSee - Simple letter game."""

# Import standard Python modules.
import logging, os, math, time, copy, json
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango, cairo

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

# Initialize logging.
log = logging.getLogger('YayBeeSee')
log.setLevel(logging.DEBUG)
logging.basicConfig()

class YayBeeSee(sugar.activity.activity.Activity):
    def __init__ (self, handle):
        sugar.activity.activity.Activity.__init__(self, handle)
        self.set_title(_("YayBeeSee"))
        
        # Create the drawing area.
        self.area = gtk.DrawingArea()
        self.area.connect('expose-event', self.expose_cb)
        
        self.area.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#ffffff'))
        
        self.key = None
        self.key_info = None
        self.pixbuf = None
        
        # Create the toolbar.
        tbox = sugar.activity.activity.ActivityToolbox(self)
        self.set_toolbox(tbox)
        
        # Load the image index.
        bundle = sugar.activity.activity.get_bundle_path()
        fd = open(bundle + '/images/INDEX', 'r')
        self.index = json.read(fd.read())

        # This has to happen last, because it calls the read_file method when restoring from the Journal.
        self.set_canvas(self.area)
        self.show_all()
        
        # Hide the sharing button from the activity toolbar since we don't support it (yet). 
        activity_toolbar = tbox.get_activity_toolbar()
        activity_toolbar.share.props.visible = False
        
        # Set up key events.
        self.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.connect('key-press-event', self.key_press_cb)

    def key_press_cb(self, widget, event):
        # Get the letter corresponding to the keypress.
        key = event.string.lower()
        
        # Load the picture.
        if self.index.has_key(key):
            self.key = key
            self.key_info = self.index[self.key]
            
            bundle = sugar.activity.activity.get_bundle_path()
            filename = os.path.join(bundle, self.key_info['file'])
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        
        self.area.queue_draw()
        
        return False
    
    def expose_cb(self, widget, event):
        cr = widget.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        cr.clip()
        
        bounds = widget.get_allocation()
        
        if self.key_info:
            # Draw the background image.
            cr.save()
            
            # Scale the image such that its larger access fills the screen,
            # while preserving the aspect ratio, 
            ratio = min(
                float(bounds.width) / float(self.pixbuf.get_width()),
                float(bounds.height) / float(self.pixbuf.get_height()))

            cr.translate(
                (bounds.width - self.pixbuf.get_width()*ratio) / 2,
                (bounds.height - self.pixbuf.get_height()*ratio) / 2)
            
            cr.scale(ratio, ratio)
            
            cr.set_source_pixbuf(self.pixbuf, 0, 0)
            cr.paint()
            
            cr.restore()
            
            # Draw the letter.
            text = self.key.upper() + self.key.lower()
            
            color = self.key_info['color']
            cr.set_source_rgb(color[0]/255.0, color[1]/255.0, color[2]/255.0)
            
            cr.set_font_size(300)
            x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
            
            cr.move_to(bounds.width - width/2 - 300, bounds.height - 300)
            cr.show_text(text)
            
