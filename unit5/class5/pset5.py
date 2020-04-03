#pset5: Magic Harp

# common imports
import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run
from common.gfxutil import topleft_label, resize_topleft_label, Cursor3D, AnimGroup, KFAnim, scale_point, CEllipse
from common.synth import Synth
from common.audio import Audio
from common.leap import getLeapInfo, getLeapFrame

from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.clock import Clock as kivyClock
import numpy as np


# This class displays a single string on screen. It knows how to draw the
# string and how to bend it, and animate it
class String(InstructionGroup):
    def __init__(self, idx, x, y_top, y_bottom):
        super(String, self).__init__()

        self.x_pos = x
        self.y_top = y_top
        self.y_bottom = y_bottom
        self.mid = (y_top + y_bottom)/2

        self.line = Line(points=[x, y_top, x, self.mid, x, y_bottom])
        self.add(self.line)

        self.plucked = False
        self.grabbed = False

    # if the string is going to animate (say, when it is plucked), on_update is
    # necessary
    def on_update(self, dt):
        pass


# This class monitors the location of the hand and determines if a pluck of
# the string happened. Each PluckGesture is associated with a string (one-to-one
# correspondence). The PluckGesture also controls controls the movement of the
# String it is connected to (to show the string bending)
class PluckGesture(object):
    def __init__(self, string, idx, callback):
        super(PluckGesture, self).__init__()
        self.string = string
        self.idx = idx
        self.callback = callback

        self.pluck_thres = 30
        self.grab_thres = 10

    def set_hand_pos(self, pos):

        diff = abs(pos[0] - self.string.x_pos)

        if diff < self.pluck_thres:
            if diff < self.grab_thres and not self.string.grabbed:
                self.string.grabbed = True
        elif self.string.grabbed:
            self.callback(self.idx)
            self.string.grabbed = False

# The Harp class combines the above classes into a fully working harp. It
# instantiates the strings and pluck gestures as well as a hand cursor display
class Harp(InstructionGroup):
    def __init__(self):
        super(Harp, self).__init__()

        kMargin = Window.width * 0.05
        kCursorSize = Window.width - 2 * kMargin, Window.height - 2 * kMargin
        self.kCursorPos = kMargin, kMargin

        self.hand = Cursor3D(kCursorSize, self.kCursorPos, (.6, .6, .6))

        self.x_pos = Window.size[0]/2
        self.y_top = Window.size[1]
        self.y_bottom = 0
        self.mid = (self.y_top + self.y_bottom)/2

        self.string = Line(points=[self.x_pos, self.y_top, self.x_pos, self.mid, self.x_pos, self.y_bottom])
        self.add(self.string)

        # make string white
        self.add(Color((255,0,0)))

        self.win_size = Window.size

        self.moved_point = (0,0)


    # will get called when the window size changes.
    def on_layout(self, win_size):
        self.win_size = win_size
        self.hand.set_boundary(win_size, self.kCursorPos)

        self.remove(self.string)

        self.x_pos = win_size[0]/2
        self.y_top = win_size[1]
        self.y_bottom = 0
        self.mid = (self.y_top + self.y_bottom)/2

        self.string = Line(points=[self.x_pos, self.y_top, self.x_pos, self.mid, self.x_pos, self.y_bottom])
        self.add(self.string)

    # set the hand position as a normalized 3D vector ranging from [0,0,0] to [1,1,1]
    def set_hand_pos(self, pos):
        pass

    # callback to be called from a PluckGesture when a pluck happens
    def on_pluck(self, idx):
        #plays a note
        print('pluck:', idx)

    # this might be needed if Harp's internal objects need on_update()
    def on_update(self, pos):
        print(pos)

class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        self.label = topleft_label()
        self.add_widget(self.label)

        self.harp = Harp()
        self.canvas.add(self.harp.hand)
        self.canvas.add(self.harp)

    # will get called when the window size changes. Pass this information down
    # to Harp so that you appropriately resize it and its subcomponents.
    def on_layout(self, win_size):
        # update self.label
        resize_topleft_label(self.label)
        self.harp.on_layout(win_size)

    def on_update(self) :
        leap_frame = getLeapFrame()
        hand = leap_frame.hands[0]
        norm_pt = scale_point(hand.palm_pos, kLeapRange)

        self.harp.hand.set_pos(norm_pt)

        self.label.text = str(getLeapInfo()) + '\n'

        # inactive (not plucking is red)
        inactive_color = (0,150,0)
        # active is green
        active_color = (150,0,0)

        if norm_pt[2] >= 0.5:
            self.harp.hand.set_color(active_color)
        else:
            self.harp.hand.set_color(inactive_color)


# for use with scale_point
# x, y, and z ranges to define a 3D bounding box
kLeapRange   = ( (-250, 250), (100, 500), (-200, 250) )

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(MainWidget)
