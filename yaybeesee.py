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
import logging, os, json, locale, random
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
        
        self.area.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color('#808080'))
        
        self.key = None
        self.key_info = None
        self.pixbuf = None
        
        # Create the toolbar.
        tbox = sugar.activity.activity.ActivityToolbox(self)
        self.set_toolbox(tbox)
        
        fullscreenbtn = sugar.graphics.toolbutton.ToolButton('view-fullscreen')
        fullscreenbtn.set_tooltip(_("Fullscreen"))
        fullscreenbtn.connect('clicked', self.fullscreen_cb)

        activity_toolbar = tbox.get_activity_toolbar()
        share_idx = activity_toolbar.get_item_index(activity_toolbar.share) 
        activity_toolbar.insert(fullscreenbtn, share_idx)

        # Load the image index for the current locale.
        bundle = sugar.activity.activity.get_bundle_path()
        code = locale.getlocale(locale.LC_ALL)[0]
        fd = open(bundle + '/images/INDEX.'+code, 'r')
        self.index = json.read(fd.read())

        # This has to happen last, because it calls the read_file method when restoring from the Journal.
        self.set_canvas(self.area)
        self.show_all()
        
        # Hide the sharing button from the activity toolbar since we don't support it (yet). 
        activity_toolbar.share.props.visible = False
        
        # Set up key events.
        self.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.connect('key-press-event', self.key_press_cb)

        # Set up the 'Ken Burns' timer.
        self.reset_zoom()
        #gobject.idle_add(self.idle_cb)

    def fullscreen_cb(self, widget):
        self.fullscreen()

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

        self.reset_zoom()

        self.area.queue_draw()
        
        return True

    def reset_zoom(self):
        self.zoom = 1.0
        self.px = 0.0
        self.py = 0.0
        self.vx = random.random() * 0.02 - 0.01
        self.vy = random.random() * 0.02 - 0.01
        
    def idle_cb(self):
        self.zoom += 0.001
        self.px += self.vx
        self.py += self.vy

        self.area.queue_draw()
 
        return True
    
    def expose_cb(self, widget, event):
        cr = widget.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        cr.clip()
        
        bounds = widget.get_allocation()
        
        if self.key_info:
            # Draw the background image.
            cr.save()
            
            # Scale the image such that it fills the screen while preserving the aspect ratio.
            # Using 'min' here shows the entire image, 'max' fills the screen.
            # It might be nice to be able to choose 'fill' or 'fit' mode per-image.
            ratio = max(
                float(bounds.width) / float(self.pixbuf.get_width()),
                float(bounds.height) / float(self.pixbuf.get_height()))

            cr.translate(
                (bounds.width - self.pixbuf.get_width()*ratio) / 2,
                (bounds.height - self.pixbuf.get_height()*ratio) / 2)
            
            cr.scale(ratio, ratio)
            
            # Apply 'Ken Burns' effect.
            cr.translate(self.px, self.py)
            cr.scale(self.zoom, self.zoom)

            cr.set_source_pixbuf(self.pixbuf, 0, 0)
            cr.paint()
            
            cr.restore()
            
            # Draw the letter.
            if self.key.upper() != self.key.lower():
                text = self.key.upper() + self.key.lower()
            else:
                text = self.key
            
            color = self.key_info['color']
            cr.set_source_rgb(color[0]/255.0, color[1]/255.0, color[2]/255.0)
            
            cr.set_font_size(500)
            x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
            
            cr.move_to(bounds.width - width - 30 - x_bearing, 30 - y_bearing)
            cr.show_text(text)

            # Draw the attribution.
            text = _('Source: "%(description)s" by %(author)s') % self.key_info
            
            cr.set_font_size(20)
            
            x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]

            cr.set_source_rgba(0.3, 0.3, 0.3, 0.7)
            cr.rectangle(10, bounds.height - 60 + y_bearing, width+20, height+20)
            cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, 0.7)
            cr.stroke()
            
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.move_to(20, bounds.height - 50)
            cr.show_text(text)

        else:

            # Draw help text.
            text = _('Welcome! Press any letter or number.')
            
            cr.set_source_rgb(0.5, 0.5, 0.5)
            
            cr.set_font_size(20)
            x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
            
            cr.move_to(bounds.width - width/2 - 300, bounds.height - 300)
            cr.show_text(text)
            
