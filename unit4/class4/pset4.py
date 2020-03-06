# pset4.py

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome
from kivy.core.window import Window

import numpy as np

# part 1: create Arpeggiator
class Arpeggiator(object):
    def __init__(self, sched, synth, channel=0, program=(0, 40), callback=None, loop=False):
        super(Arpeggiator, self).__init__()

        self.playing = False

        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        self.loop = loop

        self.playing = False

        self.cmd = None

        self.pitches = []
        self.notes = []
        self.length = 480
        self.articulation = 1
        self.direction = "up"

        self.index = 0

    # start the arpeggiator
    def start(self):
        if self.playing:
            return

        print(self.pitches)
        # exit()

        self.playing = True
        self.synth.program(self.channel, self.program[0], self.program[1])

        # start from the beginning
        self.index = 0

        # post the first note on the next quarter-note:
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, self.length)
        self.cmd = self.sched.post_at_tick(self._noteon, next_beat)

    
    # stop the arpeggiator
    def stop(self):
        if not self.playing:
            return

        self.playing = False
        self.sched.cancel(self.cmd)
        self.cmd = None

    # pitches is a list of MIDI pitch values. For example [60 64 67 72]
    def set_pitches(self, pitches):
        print("new pitches", pitches)
        self.pitches = pitches
        # up by default
        self.notes = pitches
        if self.direction == "down":
            self.notes = pitches[::-1] 
        if self.direction == "updown":
            self.notes = pitches + pitches[::-1]

    # length is related to speed of the notes. For example 240 represents 1/8th notes.
    # articulation is a ratio that defines how quickly the note off should follow the note on. 
    # For example, a value of 1 is a full-length note (legato) where the note off will 
    # occur <length> ticks after the note-on. A value of 0.5 will make the note shorter, 
    # where the note off will occur <length>/2 ticks after the note-on.
    def set_rhythm(self, length, articulation):
        #total length is the speed times articulation?
        print("new rhythm", length)
        self.length = length * articulation
        # print("self.length", self.length)

    # dir is either 'up', 'down', or 'updown'
    def set_direction(self, direction):
        print("new direction", direction)
        self.direction = direction

        self.notes = self.pitches
        if direction == "down":
            self.notes = self.pitches[::-1] 
        if direction == "updown":
            self.notes = self.pitches + self.pitches[::-1]

    def _noteon(self, tick):
        if (self.loop and self.index) >= len(self.notes):
            self.index = 0

        if self.index < len(self.notes):
            pitch = self.notes[self.index]
            vel = 100
            self.synth.noteon(self.channel, pitch, vel)

            # post the note off (full duration, legato):
            off_tick = tick + self.length
            self.sched.post_at_tick(self._noteoff, off_tick, pitch)

            # schedule the next noteon for next rhythmic subdivision:
            next_beat = tick + self.length
            self.cmd = self.sched.post_at_tick(self._noteon, next_beat)
        else:
            self.playing = False
            self.index = 0



        self.index += 1

    def _noteoff(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)
        # self.index = 0

# part 1: test your Arpeggiator here
class MainWidget1(BaseWidget) :
    def __init__(self):
        super(MainWidget1, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)

        # create the arpeggiator:
        self.arpeg = Arpeggiator(self.sched, self.synth, channel = 1, program = (0,0) )

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'm':
            self.metro.toggle()

        if keycode[1] == 'a':
            if self.arpeg.playing:
                self.arpeg.stop()
            else:
                self.arpeg.start()
        pitches = lookup(keycode[1], 'qwe', ((60, 64, 67, 72), (55, 59, 62, 65, 67, 71), (60, 65, 69)))
        if pitches:
            self.arpeg.set_pitches(pitches)

        rhythm = lookup(keycode[1], 'uiop', ((120, 1), (160, 1), (240, 0.75), (480, 0.25)))
        if rhythm:
            self.arpeg.set_rhythm(*rhythm)

        direction = lookup(keycode[1], '123', ('up', 'down', 'updown'))
        if direction:
            self.arpeg.set_direction(direction)


    def on_update(self) :
        self.audio.on_update()
        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'tempo:%d\n' % self.tempo_map.get_tempo()
        self.label.text += 'm: toggle Metronome\n'
        self.label.text += 'a: toggle Arpeggiator\n'
        self.label.text += 'q w e: Changes pitches\n'
        self.label.text += 'u i o p: Change Rhythm\n'
        self.label.text += '1 2 3: Change Direction\n'


# Part 2
class MainWidget2(BaseWidget) :
    def __init__(self):
        super(MainWidget2, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)

        # create the arpeggiator:
        self.arpeg = Arpeggiator(self.sched, self.synth, channel = 1, program = (0,0), loop=True)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

        # set pitches and lengths

        # this is an evil diminished chord
        self.pitches = (48, 51, 54, 57)
        self.arpeg.set_pitches(self.pitches)

    def on_touch_down(self, touch):
        p = touch.pos
        self.arpeg.start()

    def on_touch_up(self, touch):
        self.arpeg.stop()

    def on_touch_move(self, touch):
        p = touch.pos

        # update pitches
        scaling = (touch.pos[0] - Window.width/2) / 50
        new_pitches = tuple([int(scaling+i) for i in self.pitches])
        self.arpeg.set_pitches(new_pitches)

        # update speed - range
        self.arpeg.set_rhythm(p[1], 0.7)

    def on_update(self) :
        self.audio.on_update()
        self.label.text = self.sched.now_str() + '\n'


# Parts 3 and 4
class MainWidget3(BaseWidget) :
    def __init__(self):
        super(MainWidget3, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        pass

    def on_key_up(self, keycode):
        pass

    def on_touch_down(self, touch):
        pass

    def on_touch_up(self, touch):
        pass

    def on_touch_move(self, touch):
        pass

    def on_update(self) :
        self.audio.on_update()
        self.label.text = self.sched.now_str() + '\n'


if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(eval('MainWidget' + sys.argv[1]))
