# pset3.py

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup

from common.audio import Audio
from common.mixer import Mixer
from common.note import NoteGenerator, Envelope
from common.wavegen import WaveGenerator, SpeedModulator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line, Triangle, RoundedRectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

from kivy.app import App

from kivy.utils import get_random_color

import random
from random import randint, random
import numpy as np

from kivy.uix.image import Image, AsyncImage

class Bubble(InstructionGroup):
    def __init__(self, pos, r, color, timbre="sine", decay=1):
        super(Bubble, self).__init__()

        center_x = Window.width/2
        center_y = Window.height/2

        self.radius_anim = KFAnim((0, r), (1, 4*r), (3, 0))
        self.pos_anim    = KFAnim((0, pos[0], pos[1]), (3, Window.width, Window.height))

        self.color = Color(*color)
        self.add(self.color)
        self.timbre = timbre
        self.decay = decay

        if timbre == "square":
            self.square = Rectangle(pos=pos, size=(2*r, 2*r))
            self.add(self.square)
        elif timbre == "triangle":
            self.triangle = CEllipse(pos=pos, size=(2*r, 2*r), segments = 3)
            self.add(self.triangle)
        elif timbre == "sawtooth":
            self.sawtooth = CEllipse(pos=pos, size=(2*r, 2*r), segments = 5)
            self.add(self.sawtooth)
        else: # sine wave
            self.circle = CEllipse(cpos = pos, size = (2*r, 2*r), segments = 40)
            self.add(self.circle)

        self.time = 0
        self.on_update(0)

    def on_update(self, dt):
        # animate radius
        rad = self.radius_anim.eval(self.time)

        # changes how much time and how fast object travels based on decay
        pos = self.pos_anim.eval(self.time*(1/self.decay))

        if self.timbre == "square":
            self.square.pos = pos
            self.square.size = (2*rad, 2*rad)
        elif self.timbre == "triangle":
            self.triangle.pos = pos
            self.triangle.size = (2*rad, 2*rad)
        elif self.timbre == "sawtooth":
            self.sawtooth.pos = pos
            self.sawtooth.size = (2*rad, 2*rad)
        else:
            self.circle.csize = (2*rad, 2*rad)
            # animate position
            self.circle.cpos = pos

        # advance time
        self.time += dt
        # continue flag
        return self.radius_anim.is_active(self.time)

# part 1:
class MainWidget1(BaseWidget) :
    def __init__(self):
        super(MainWidget1, self).__init__()

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(0.2)
        self.audio.set_generator(self.mixer)

        # note parameters
        self.root_pitch = 60
        self.gain = 0.5
        self.attack = 0.01
        self.decay = 1.0
        self.timbre = 'sine'

        self.info = topleft_label()
        self.add_widget(self.info)

        self.anim_group = AnimGroup()
        self.canvas.add(self.anim_group)
        self.info = topleft_label()
        self.add_widget(self.info)

        interval_list = [0, 2, 4, 5, 7, 9, 11, 12]
        mapped_colors = [get_random_color(alpha=1.0) for i in range(8)]
        self.color_list = dict( zip( interval_list, mapped_colors))


    def on_key_down(self, keycode, modifiers):
        # trigger a note to play with keys 1-8
        pitch = lookup(keycode[1], '12345678' , (0, 2, 4, 5, 7, 9, 11, 12))
        if pitch is not None:
            pitch += self.root_pitch
            note = NoteGenerator(pitch, 0.3, self.timbre)
            env = Envelope(note, self.attack, 1, self.decay, 2)
            self.mixer.add(env)

            # add object

            # adjusted pitch position - adjustments relocate dot to a more interesting place
            interval = pitch - self.root_pitch
            pitch_pos = interval*42 + 10
            pos_coord = (50,pitch_pos)


            # the color is randomly generated.         
            bubble = Bubble(pos_coord, 20, self.color_list[interval], self.timbre, self.decay)
        
            self.canvas.add(bubble)

            self.anim_group.add(bubble)
            
        # change timbre with up/down keys
        timbre_sel = lookup(keycode[1], ('up', 'down'), (1, -1))
        if timbre_sel is not None:
            timbre_choices = ('sine', 'square', 'triangle', 'sawtooth')
            idx = (timbre_choices.index(self.timbre) + timbre_sel) % len(timbre_choices)
            self.timbre = timbre_choices[idx]

        # change note length with left/right keys
        decay_delta = lookup(keycode[1], ('left', 'right'), (-.2, .2))
        if decay_delta is not None:
            self.decay = np.clip(self.decay + decay_delta, .2, 3)


    def on_update(self):
        self.audio.on_update()

        self.info.text = 'load: %.2f\n' % self.audio.get_cpu_load()
        self.info.text += 'dur: %.2f\n' % self.decay
        self.info.text += 'timbre: %s\n' % self.timbre

        self.anim_group.on_update()


# part 2
class MainWidget2(BaseWidget) :
    def __init__(self, ):
        super(MainWidget2, self).__init__()
        self.info = topleft_label()
        self.add_widget(self.info)

        # AnimGroup handles drawing, animation, and object lifetime management
        self.objects = AnimGroup()
        self.canvas.add(self.objects)

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(0.2)
        self.audio.set_generator(self.mixer)

        # note parameters
        self.root_pitch = 60
        self.gain = 0.5
        self.attack = 0.01
        self.decay = 1.0
        self.timbre = np.random.choice(['sine', 'square', 'triangle', 'sawtooth'])

    def on_touch_down(self, touch) :
        # TODO - vary these parameters as needed or create new parameters if you wish.
        p = touch.pos
        r = 50
        c = (1,1,1)

        # TODO: pass in callback
        self.objects.add(PhysBubble(p, r, c, self.on_collide))

    def on_collide(self, bubble, vel) :
        # TODO make some music here. You can access member variables / state

        #high range
        high_intervals = [i for i in range(0, 30)]

        #low range
        low_intervals = [i for i in range(-30, 0)]

        if abs(vel[0])>80 or abs(vel[1])>80:
            intervals = high_intervals
        else:
            intervals = low_intervals

        if bubble.hit:
            pitch = np.random.choice(low_intervals) + self.root_pitch
            note = NoteGenerator(pitch, 0.3, self.timbre)
            env = Envelope(note, self.attack, 1, self.decay, 2)
            self.mixer.add(env)
            bubble.hit = False

    def on_update(self):
        self.audio.on_update()
        self.objects.on_update()

        self.info.text = str(Window.mouse_pos)
        self.info.text += '\nfps:%d' % kivyClock.get_fps()
        self.info.text += '\nbubbles:%d' % self.objects.size()


gravity = np.array((0, -1800))
damping = 0.9

class PhysBubble(InstructionGroup):
    def __init__(self, pos, r, color, bounce_callback=None):
        super(PhysBubble, self).__init__()

        self.radius = r
        self.pos = np.array(pos, dtype=np.float)
        self.vel = np.array((randint(-300, 300), 0), dtype=np.float)
        self.bounce_callback = bounce_callback

        self.color = Color(*color)
        self.add(self.color)

        self.circle = CEllipse(cpos=pos, csize=(2*r,2*r), segments = 40)
        self.add(self.circle)

        self.num_bounces = 0

        self.exist_flag = True

        self.hit = False

        self.on_update(0)

    def on_update(self, dt):
        # integrate accel to get vel
        self.vel += gravity * dt

        # integrate vel to get pos
        self.pos += self.vel * dt

        if self.num_bounces < 5:
            # collision with right side
            if self.pos[0] - self.radius < 0:
                self.vel[0] = -self.vel[0] * damping
                self.pos[0] = self.radius
                self.num_bounces += 1
                self.hit = True

            # collision with left side
            elif self.pos[0] + self.radius > Window.width:
                self.vel[0] = -self.vel[0] * damping
                self.pos[0] = Window.width - self.radius
                self.num_bounces += 1
                self.hit = True

            # collision with floor
            elif self.pos[1] - self.radius < 0:
                self.vel[1] = -self.vel[1] * damping
                self.pos[1] = self.radius
                self.num_bounces += 1
                self.hit = True
        else:
            # makes sure dot doesn't dissapear before finishing slide off screen
            if (self.pos[0] - self.radius < 0 - 2*self.radius) or (self.pos[0] + self.radius >  Window.width + 2*self.radius) or (self.pos[1] - self.radius < 0 - 2*self.radius):
                self.exist_flag = False

        # send data to listener as well
        if self.bounce_callback:
            self.bounce_callback(self, self.vel)

        self.circle.cpos = self.pos
        return self.exist_flag


class Vegetable(InstructionGroup):
    def __init__(self, pos, r, color, timbre="sine", decay=1):
        super(Vegetable, self).__init__()

        center_x = Window.width/2
        center_y = Window.height/2

        self.radius_anim = KFAnim((0, r), (.1, 2*r), (3, 0))
        self.pos_anim    = KFAnim((0, pos[0], pos[1]), (3, center_x, center_y))

        self.color = Color(*color)
        self.add(self.color)
        self.timbre = timbre
        self.decay = decay

        items = ["broccoli", "carrot", "tomato", "pizza", "greenbeans"]
        self.item_pitches = {"broccoli":70, "carrot":76, "tomato":74, "pizza":72, "greenbeans":70}

        self.selected_item = np.random.choice(items)

        # default
        self.item = Rectangle(pos=pos, size=(10*r, 10*r), source ="broccoli.png")

        if self.selected_item == "broccoli":
            self.broccoli = self.item
        elif self.selected_item == "carrot":
            self.item = Rectangle(pos=pos, size=(10*r, 10*r), source ="carrot.png")
        elif self.selected_item == "tomato":
            self.item = Rectangle(pos=pos, size=(10*r, 10*r), source ="tomato.png")
        elif self.selected_item == "pizza":
            self.item = Rectangle(pos=pos, size=(10*r, 10*r), source ="pizza.png")
        elif self.selected_item == "greenbeans":
            self.item = Rectangle(pos=pos, size=(10*r, 10*r), source ="greenbeans.png")

        
        self.add(self.item)
        
        self.time = 0
        self.on_update(0)

    def on_update(self, dt):
        # animate radius
        rad = self.radius_anim.eval(self.time)

        # changes how much time and how fast object travels based on decay
        pos = self.pos_anim.eval(self.time*(1/self.decay))

        self.item.size = (2*rad, 2*rad)
        # animate position
        self.item.pos = pos

        # advance time
        self.time += dt
        # continue flag
        return self.radius_anim.is_active(self.time)

# part 3
class MainWidget3(BaseWidget) :
    def __init__(self):
        super(MainWidget3, self).__init__()

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(0.2)
        self.audio.set_generator(self.mixer)
        Window.size = (1500, 1050)

        # note parameters
        self.root_pitch = 60
        self.gain = 0.5
        self.attack = 0.01
        self.decay = 1.0
        self.timbre = 'sine'

        #adds background of nicholas cage
        self.square = Rectangle(pos=(0,0), size=(Window.width, Window.height), source ="nick-background.png")
        self.canvas.add(self.square)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.anim_group = AnimGroup()
        self.canvas.add(self.anim_group)
        self.info = topleft_label()
        self.add_widget(self.info)

        interval_list = [0, 2, 4, 5, 7, 9, 11, 12]
        mapped_colors = [get_random_color(alpha=1.0) for i in range(8)]
        self.color_list = dict( zip( interval_list, mapped_colors))

    def on_touch_down(self, touch) :
        # 60 is the radius
        veggie = Vegetable(touch.pos, 60, (0,0), self.timbre, self.decay)

        pitch = veggie.item_pitches[veggie.selected_item]
        note = NoteGenerator(pitch, 0.3, self.timbre)
        env = Envelope(note, self.attack, 1, self.decay, 2)
        self.mixer.add(env)

        self.canvas.add(veggie)

        self.anim_group.add(veggie)

    def on_update(self):
        self.audio.on_update()
        self.anim_group.on_update()

        self.info.text = 'load: %.2f\n' % self.audio.get_cpu_load()
        self.info.text += 'dur: %.2f\n' % self.decay
        self.info.text += 'timbre: %s\n' % self.timbre

        # makes sure background resizes when window does
        # self.square = Rectangle(pos=(0,0), size=(Window.width, Window.height), source ="nick-background.png")
        # self.canvas.add(self.square)


if __name__ == "__main__":
    # to run, on the command line, type: python pset3.py <num> to choose the MainWidget version.
    run(eval('MainWidget' + sys.argv[1]))
