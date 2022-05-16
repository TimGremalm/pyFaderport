from Faderport.helper_functions import try_parse_int
from Faderport.constants import *


class Button:
    def __init__(self, name: str, faderport,
                 midi_type: MIDIType, midi_id: int,
                 luminance_type: LightTypes,
                 channel: int = 0):
        self.name = name
        self.faderport = faderport
        self.midi_id = midi_id
        self.channel = channel
        self.midi_type = midi_type
        self.luminance_type = luminance_type
        self.light = None

    def set_light(self, color):
        """
        Set light on button.
        :param color: int color palette,
                      str "Red,Green,Blue" (ex. "255,127,0") can only be used if button-luminance_type is RGB or
                      textual representation according to luminance_type (ex. 'LitBlink').
        """
        if self.light == color:
            # print(f"Color {color} is already set for {self.name}.")
            return

        color_argument = color
        color_to_set = None
        color_to_set_rgb = None
        if type(color_argument) is int:
            color_to_set = color
        elif str(type(color_argument)) == str(ColorsSingle):
            color_to_set = color_argument.value
        elif type(color_argument) is bytes or type(color_argument) is str:
            # Convert bytes to str
            if type(color_argument) is bytes:
                color_argument = color_argument.decode()
            # Parse color argument
            if try_parse_int(color_argument) is not None:
                # It's an integer
                color_to_set = int(color_argument)
            elif self.luminance_type.value <= 4:
                # Single colors, check if it's a named enum
                if color_argument in ColorsSingle.__members__:
                    color_to_set = ColorsSingle[color_argument].value
                else:
                    raise Exception(f"Can't find color {color_argument} in enum LightColorSingle.")
            elif self.luminance_type == LightTypes.RGB:
                # RGB colors, check if it's 3 integers comma-separated
                rgb = color_argument.split(",")
                if len(rgb) == 3:
                    red = try_parse_int(rgb[0])
                    green = try_parse_int(rgb[1])
                    blue = try_parse_int(rgb[2])
                    if red is not None and green is not None and blue is not None:
                        color_to_set_rgb = (red, green, blue)
                    else:
                        raise Exception(f"Couldn't parse RGB from color {color_argument}.")
                else:
                    raise Exception(f"Couldn't parse RGB from color {color_argument}, "
                                    f"it should be comma,separated like R,G,B.")
            else:
                raise Exception(f"Couldn't parse color argument {color_argument}.")
        else:
            raise Exception(f"Color argument {color_argument} is not valid for button_set_color().")
        # print(type(color))
        # print(f"color_to_set {color_to_set}, color_to_set_rgb {color_to_set_rgb}")

        # Validate ranges
        if self.luminance_type.value <= 4:
            # Single colors
            if color_to_set < 0:
                raise Exception(f"Color {color_to_set} for Single can't be negative.")
            if color_to_set >= len(ColorsSingle.__members__):
                raise Exception(f"Color {color_to_set} can't be more than max of LightColorSingle.")
        elif self.luminance_type == LightTypes.RGB:
            # RGB colors
            if color_to_set is not None:
                if color_to_set < 0:
                    raise Exception(f"Brightness {color_to_set} for RGB can't be negative.")
                if color_to_set >= len(ColorsSingle.__members__):
                    raise Exception(f"Brightness {color_to_set} can't be more than max of ColorsSingle.")
            elif color_to_set_rgb is not None:
                if color_to_set_rgb[0] < 0:
                    raise Exception(f"Color {color_to_set_rgb} red for RGB can't be negative.")
                if color_to_set_rgb[0] > 255:
                    raise Exception(f"Color {color_to_set_rgb} red for RGB can't be more than 255.")
                if color_to_set_rgb[1] < 0:
                    raise Exception(f"Color {color_to_set_rgb} green for RGB can't be negative.")
                if color_to_set_rgb[1] > 255:
                    raise Exception(f"Color {color_to_set_rgb} green for RGB can't be more than 255.")
                if color_to_set_rgb[2] < 0:
                    raise Exception(f"Color {color_to_set_rgb} blue for RGB can't be negative.")
                if color_to_set_rgb[2] > 255:
                    raise Exception(f"Color {color_to_set_rgb} blue for RGB can't be more than 255.")
            else:
                raise Exception(f"A color must be set {color_argument}.")

        if color_to_set is not None:
            if self.midi_type == MIDIType.ControlChange:
                self.faderport.send_control_change(channel=self.channel, control=self.midi_id, value=color_to_set)
            else:
                self.faderport.send_note_on(channel=self.channel, note=self.midi_id, velocity=color_to_set)
        else:
            # Convert to 7-bit color
            self.faderport.send_note_on(channel=self.channel+1, note=self.midi_id, velocity=color_to_set_rgb[0] >> 1)
            self.faderport.send_note_on(channel=self.channel+2, note=self.midi_id, velocity=color_to_set_rgb[1] >> 1)
            self.faderport.send_note_on(channel=self.channel+3, note=self.midi_id, velocity=color_to_set_rgb[2] >> 1)

        self.light = color

    def __repr__(self):
        out = f"Button(name='{self.name}', " \
              f"faderport=<self.faderport>, " \
              f"midi_type={self.midi_type}, channel={self.channel}, midi_id={self.midi_id}, " \
              f"luminance_type={self.luminance_type}"
        out += f")"
        return out


class PitchWheel:
    def __init__(self, name: str, faderport,
                 channel: int, touch_id: int):
        self.name = name
        self.faderport = faderport
        self.pitchwheel_channel = channel
        self.pitchwheel_midi_id = "pitchwheel"
        self.touch_midi_id = touch_id
        self.touch_midi_type = MIDIType.Note
        self.touch_channel = 0
        self.pitch = None

    def set_pitch(self, pitch):
        """
        Set pitch on slider.
        :param pitch: int pitch value.
        """
        pitch_argument = pitch
        pitch_to_set = None
        if type(pitch_argument) is int:
            pitch_to_set = pitch_argument
        elif type(pitch_argument) is bytes or type(pitch_argument) is str:
            # Convert bytes to str
            if type(pitch_argument) is bytes:
                pitch_argument = pitch_argument.decode()
            if try_parse_int(pitch_argument) is not None:
                pitch_to_set = int(pitch_argument)
            else:
                raise Exception(f"Pitch argument {pitch_argument} can't be parsed as integer.")
        else:
            raise Exception(f"Pitch argument {pitch_argument} is not valid for set_pitch().")
        # Validate ranges
        if pitch_to_set < -8192 or pitch_to_set > 8191:
            raise Exception(f"Pitch {pitch_to_set} must be in range of -8192 to 8191.")
        if self.pitch == pitch_to_set:
            print(f"Pitch {pitch_to_set} is already set for {self.name}.")
            return
        self.faderport.send_pitch_wheel(channel=self.pitchwheel_channel, pitch_value=pitch_to_set)
        self.pitch = pitch_to_set

    def __repr__(self):
        out = f"PitchWheel(name='{self.name}', " \
              f"faderport=<self.faderport>, " \
              f"channel={self.pitchwheel_channel}"
        out += f")"
        return out


class Knob:
    def __init__(self, name: str, faderport, midi_touch: int, midi_rotate: int):
        self.name = name
        self.faderport = faderport
        self.midi_touch = midi_touch
        self.midi_rotate = midi_rotate
        self.midi_channel = 0

    def __repr__(self):
        out = f"Know(name='{self.name}', " \
              f"faderport=<self.faderport>"
        out += f", midi_touch={self.midi_touch}, midi_rotate={self.midi_rotate}"
        out += f")"
        return out


class FaderportControls:
    def __init__(self, faderport):
        self.faderport = faderport
        self.topics_in = {}
        self.topics_out = {}
        # self.add_control_button(btn=Button(name="left_tap_tempo", faderport=faderport,
        #                                    midi_type=MIDIType.ControlChange,
        #                                    midi_id=3, luminance_type=LightTypes.Yellow))
        # Left Knob
        self.add_control_knob(knob=Knob(name="left_knob", faderport=faderport,
                                        midi_touch=32, midi_rotate=16))
        # Left buttons
        self.add_control_button(btn=Button(name="left_arm", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=0, luminance_type=LightTypes.Red))
        self.add_control_button(btn=Button(name="left_solo_clear", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=1, luminance_type=LightTypes.Yellow))
        self.add_control_button(btn=Button(name="left_mute_clear", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=2, luminance_type=LightTypes.Red))
        self.add_control_button(btn=Button(name="left_bypass", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=3, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="left_macro", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=4, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="left_link", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=5, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="left_shift", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=70, luminance_type=LightTypes.Yellow))
        # Right buttons
        self.add_control_button(btn=Button(name="right_track", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=40, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_edit_plugins", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=43, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_sends", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=41, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_pan", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=42, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_audio", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=62, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_vi", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=63, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_bus", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=64, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_vca", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=65, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_all", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=66, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_shift", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=6, luminance_type=LightTypes.Yellow))
        # Navigate Knob
        self.add_control_knob(knob=Knob(name="navigate_knob", faderport=faderport,
                                        midi_touch=83, midi_rotate=60))
        # Navigate buttons
        self.add_control_button(btn=Button(name="navigate_latch", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=78, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_trim", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=76, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_off", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=79, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_touch", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=77, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_write", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=75, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_read", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=74, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_prev", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=46, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_next", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=47, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_channel", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=54, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_zoom", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=55, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_scroll", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=56, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_bank", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=57, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_master", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=58, luminance_type=LightTypes.Yellow))
        self.add_control_button(btn=Button(name="navigate_click", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=59, luminance_type=LightTypes.Red))
        self.add_control_button(btn=Button(name="navigate_section", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=60, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="navigate_marker", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=61, luminance_type=LightTypes.Green))
        # Navigate buttons
        self.add_control_button(btn=Button(name="transport_loop", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=86, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="transport_rewind", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=91, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="transport_fast_forward", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=92, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="transport_stop", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=93, luminance_type=LightTypes.Yellow))
        self.add_control_button(btn=Button(name="transport_play_pause", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=94, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="transport_record", faderport=faderport,
                                           midi_type=MIDIType.Note,
                                           midi_id=95, luminance_type=LightTypes.Red))
        # 8 columns with sliders and buttons
        for i in range(8):
            col = i + 1
            self.add_control_button(btn=Button(name=f"col{col}_select", faderport=faderport,
                                               midi_type=MIDIType.Note,
                                               midi_id=24+i, luminance_type=LightTypes.RGB))
            self.add_control_button(btn=Button(name=f"col{col}_mute", faderport=faderport,
                                               midi_type=MIDIType.Note,
                                               midi_id=16+i, luminance_type=LightTypes.Red))
            self.add_control_button(btn=Button(name=f"col{col}_solo", faderport=faderport,
                                               midi_type=MIDIType.Note,
                                               midi_id=8+i, luminance_type=LightTypes.Yellow))
            self.add_control_pitch_wheel(pitchwheel=PitchWheel(name=f"col{col}_slider", faderport=faderport,
                                                               channel=i, touch_id=104+i))

    def callback_button_event(self, control_object, msg):
        if msg.type == "control_change":
            if msg.value > 0:
                payload = f"{msg.value}"
                topic = f"faderport/{control_object.name}/event/down"
            else:
                payload = f"{msg.value}"
                topic = f"faderport/{control_object.name}/event/up"
        elif msg.type == "note_on":
            payload = f"{msg.velocity}"
            if msg.velocity == 0:
                topic = f"faderport/{control_object.name}/event/up"
            else:
                topic = f"faderport/{control_object.name}/event/down"
        elif msg.type == "note_off":
            payload = f"{msg.velocity}"
            topic = f"faderport/{control_object.name}/event/up"
        else:
            return
        self.faderport.mqtt_client.publish(topic=topic, payload=payload)

    def callback_button_set_light(self, topics, control_object, msg):
        # print(f"callback_display for {control_object.name} msg {topics} {msg.payload}")
        try:
            if topics[2] == "set_light":
                control_object.set_light(msg.payload)
            else:
                print(f"callback_button_set_light() Couldn't parse topic {topics[2]}.")
                return
        except Exception as ex:
            self.faderport.mqtt_client.publish(topic=f"{topics[0]}/{topics[1]}/error", payload=str(ex))

    def add_control_button(self, btn: Button):
        if btn.name in self.topics_in:
            raise Exception(f"Control {btn.name} already exist in topics_in.")
        self.topics_in[btn.name] = {}
        self.topics_in[btn.name]["set_light"] = (btn, self.callback_button_set_light)

        # Set topics_out[channel][midi_id][type] = (button_object, button_callback)
        if btn.channel not in self.topics_out:
            self.topics_out[btn.channel] = {}
        if btn.midi_id not in self.topics_out[btn.channel]:
            self.topics_out[btn.channel][btn.midi_id] = {}
        if btn.midi_type == MIDIType.ControlChange:
            self.topics_out[btn.channel][btn.midi_id]['control_change'] = (btn, self.callback_button_event)
        elif btn.midi_type == MIDIType.Note:
            self.topics_out[btn.channel][btn.midi_id]['note_on'] = (btn, self.callback_button_event)
            self.topics_out[btn.channel][btn.midi_id]['note_off'] = (btn, self.callback_button_event)

        # Set object
        setattr(self, btn.name, btn)

    def callback_pitch_wheel_event(self, control_object, msg):
        if msg.type == "note_on":
            payload = f"{msg.velocity}"
            if msg.velocity == 0:
                topic = f"faderport/{control_object.name}/event/release"
            else:
                topic = f"faderport/{control_object.name}/event/touch"
        elif msg.type == "note_off":
            payload = f"{msg.velocity}"
            topic = f"faderport/{control_object.name}/event/release"
        elif msg.type == "pitchwheel":
            payload = f"{msg.pitch}"
            topic = f"faderport/{control_object.name}/event/pitch"
            control_object.pitch = msg.pitch
        else:
            return
        self.faderport.mqtt_client.publish(topic=topic, payload=payload)

    def callback_pitch_wheel_set_pitch(self, topics, control_object, msg):
        # print(f"callback_pitch_wheel_set_pitch for {control_object.name} msg {topics} {msg.payload}")
        try:
            if topics[2] == "set_pitch":
                control_object.set_pitch(msg.payload)
            else:
                print(f"callback_pitch_wheel_set_pitch() Couldn't parse topic {topics[2]}.")
                return
        except Exception as ex:
            self.faderport.mqtt_client.publish(topic=f"{topics[0]}/{topics[1]}/error", payload=str(ex))

    def add_control_pitch_wheel(self, pitchwheel: PitchWheel):
        if pitchwheel.name in self.topics_in:
            raise Exception(f"Control {pitchwheel.name} already exist in topics_in.")
        self.topics_in[pitchwheel.name] = {}
        self.topics_in[pitchwheel.name]["set_pitch"] = (pitchwheel, self.callback_pitch_wheel_set_pitch)

        # Set topics_out[channel][midi_id][type] = (button_object, button_callback)
        if pitchwheel.pitchwheel_channel not in self.topics_out:
            self.topics_out[pitchwheel.pitchwheel_channel] = {}
        if pitchwheel.touch_channel not in self.topics_out:
            self.topics_out[pitchwheel.touch_channel] = {}

        if pitchwheel.touch_midi_id not in self.topics_out[pitchwheel.touch_channel]:
            self.topics_out[pitchwheel.touch_channel][pitchwheel.touch_midi_id] = {}
        if pitchwheel.pitchwheel_midi_id not in self.topics_out[pitchwheel.pitchwheel_channel]:
            self.topics_out[pitchwheel.pitchwheel_channel][pitchwheel.pitchwheel_midi_id] = {}

        self.topics_out[pitchwheel.touch_channel][pitchwheel.touch_midi_id]['note_on'] = (pitchwheel, self.callback_pitch_wheel_event)
        self.topics_out[pitchwheel.touch_channel][pitchwheel.touch_midi_id]['note_off'] = (pitchwheel, self.callback_pitch_wheel_event)
        self.topics_out[pitchwheel.pitchwheel_channel][pitchwheel.pitchwheel_midi_id]['pitchwheel'] = (pitchwheel, self.callback_pitch_wheel_event)

        # Set object
        setattr(self, pitchwheel.name, pitchwheel)

    def callback_knob_event(self, control_object, msg):
        if msg.type == "control_change":
            if msg.value > 0 and msg.value < 64:
                payload = f"{msg.value}"
                topic = f"faderport/{control_object.name}/event/rotate"
            else:
                payload = f"{(msg.value-64) * -1}"
                topic = f"faderport/{control_object.name}/event/rotate"
        elif msg.type == "note_on":
            if msg.velocity == 0:
                payload = f"{msg.velocity}"
                topic = f"faderport/{control_object.name}/event/up"
            else:
                payload = f"{msg.velocity}"
                topic = f"faderport/{control_object.name}/event/down"
        else:
            return
        self.faderport.mqtt_client.publish(topic=topic, payload=payload)

    def add_control_knob(self, knob: Knob):
        # Set topics_out[channel][midi_id][type] = (knob_object, knob_callback)
        if knob.midi_channel not in self.topics_out:
            self.topics_out[knob.midi_channel] = {}
        if knob.midi_touch not in self.topics_out[knob.midi_channel]:
            self.topics_out[knob.midi_channel][knob.midi_touch] = {}
        if knob.midi_rotate not in self.topics_out[knob.midi_channel]:
            self.topics_out[knob.midi_channel][knob.midi_rotate] = {}
        self.topics_out[knob.midi_channel][knob.midi_touch]['note_on'] = (knob, self.callback_knob_event)
        self.topics_out[knob.midi_channel][knob.midi_touch]['note_off'] = (knob, self.callback_knob_event)
        self.topics_out[knob.midi_channel][knob.midi_rotate]['control_change'] = (knob, self.callback_knob_event)
        # Set object
        setattr(self, knob.name, knob)


if __name__ == '__main__':
    a = Button(name="button_a", midi_type=MIDIType.Note, channel=0, midi_id=46, luminance_type=LightTypes.RedYellow)
    print(repr(a))
