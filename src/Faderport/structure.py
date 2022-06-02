from Faderport.helper_functions import try_parse_int
from Faderport.constants import *


class Button:
    def __init__(self, name: str, cb_set_light,
                 midi_type: MIDIType, midi_id: int,
                 luminance_type: LightTypes,
                 channel: int = 0):
        self.name = name
        self.callback_set_light = cb_set_light
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
        # Parse argument
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

        # Send command
        if color_to_set is not None:
            self.callback_set_light(self, color_to_set)
        else:
            self.callback_set_light(self, color_to_set_rgb)
        # Update state
        self.light = color

    def __repr__(self):
        out = f"Button(name='{self.name}', " \
              f"midi_type={self.midi_type}, channel={self.channel}, midi_id={self.midi_id}, " \
              f"luminance_type={self.luminance_type}"
        out += f")"
        return out


class PitchWheel:
    def __init__(self, name: str, cb_pitchwheel_set_pitch,
                 channel: int, touch_id: int):
        self.name = name
        self.callback_pitchwheel_set_pitch = cb_pitchwheel_set_pitch
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
        # Parse argument
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
        # Send command
        self.callback_pitchwheel_set_pitch(channel=self.pitchwheel_channel, pitch_value=pitch_to_set)
        # Update state
        self.pitch = pitch_to_set

    def __repr__(self):
        out = f"PitchWheel(name='{self.name}', " \
              f"channel={self.pitchwheel_channel}"
        out += f")"
        return out


class Knob:
    def __init__(self, name: str, midi_touch: int, midi_rotate: int):
        self.name = name
        self.midi_touch = midi_touch
        self.midi_rotate = midi_rotate
        self.midi_channel = 0

    def __repr__(self):
        out = f"Knob(name='{self.name}'"
        out += f", midi_touch={self.midi_touch}, midi_rotate={self.midi_rotate}"
        out += f")"
        return out


class FaderportControls:
    def __init__(self):
        self.mqtt_prefix = "faderport"
        self.mqtt_topics_in = {}
        self.mqtt_topics_out = {}
        self.midi_triggers = {}
        self.elements = []
        # Left Knob
        self.add_control_knob(knob=Knob(name="left_knob", midi_touch=32, midi_rotate=16))
        # Left buttons
        self.add_control_button(btn=Button(name="left_arm", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=0, luminance_type=LightTypes.Red))
        self.add_control_button(btn=Button(name="left_solo_clear", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=1, luminance_type=LightTypes.Yellow))
        self.add_control_button(btn=Button(name="left_mute_clear", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=2, luminance_type=LightTypes.Red))
        self.add_control_button(btn=Button(name="left_bypass", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=3, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="left_macro", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=4, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="left_link", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=5, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="left_shift", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=70, luminance_type=LightTypes.Yellow))
        # Right buttons
        self.add_control_button(btn=Button(name="right_track", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=40, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_edit_plugins", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=43, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_sends", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=41, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_pan", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=42, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="right_audio", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=62, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_vi", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=63, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_bus", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=64, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_vca", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=65, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_all", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=66, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="right_shift", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=6, luminance_type=LightTypes.Yellow))
        # Navigate Knob
        self.add_control_knob(knob=Knob(name="navigate_knob", midi_touch=83, midi_rotate=60))
        # Navigate buttons
        self.add_control_button(btn=Button(name="navigate_latch", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=78, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_trim", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=76, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_off", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=79, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_touch", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=77, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_write", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=75, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_read", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=74, luminance_type=LightTypes.RGB))
        self.add_control_button(btn=Button(name="navigate_prev", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=46, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_next", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=47, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_channel", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=54, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_zoom", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=55, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_scroll", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=56, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_bank", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=57, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="navigate_master", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=58, luminance_type=LightTypes.Yellow))
        self.add_control_button(btn=Button(name="navigate_click", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=59, luminance_type=LightTypes.Red))
        self.add_control_button(btn=Button(name="navigate_section", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=60, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="navigate_marker", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=61, luminance_type=LightTypes.Green))
        # Navigate buttons
        self.add_control_button(btn=Button(name="transport_loop", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=86, luminance_type=LightTypes.Blue))
        self.add_control_button(btn=Button(name="transport_rewind", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=91, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="transport_fast_forward", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=92, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="transport_stop", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=93, luminance_type=LightTypes.Yellow))
        self.add_control_button(btn=Button(name="transport_play_pause", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=94, luminance_type=LightTypes.Green))
        self.add_control_button(btn=Button(name="transport_record", cb_set_light=self.callback_unset,
                                           midi_type=MIDIType.Note,
                                           midi_id=95, luminance_type=LightTypes.Red))
        # 8 columns with sliders and buttons
        for i in range(8):
            col = i + 1
            self.add_control_button(btn=Button(name=f"col{col}_select", cb_set_light=self.callback_unset,
                                               midi_type=MIDIType.Note,
                                               midi_id=24+i, luminance_type=LightTypes.RGB))
            self.add_control_button(btn=Button(name=f"col{col}_mute", cb_set_light=self.callback_unset,
                                               midi_type=MIDIType.Note,
                                               midi_id=16+i, luminance_type=LightTypes.Red))
            self.add_control_button(btn=Button(name=f"col{col}_solo", cb_set_light=self.callback_unset,
                                               midi_type=MIDIType.Note,
                                               midi_id=8+i, luminance_type=LightTypes.Yellow))
            self.add_control_pitch_wheel(pitchwheel=PitchWheel(name=f"col{col}_slider",
                                                               cb_pitchwheel_set_pitch=self.callback_unset,
                                                               channel=i, touch_id=104+i))

    def callback_unset(*args, **kwargs):
        raise Exception(f"Callback is not set for {args} {kwargs}.")

    def add_control_button(self, btn: Button):
        # Topics In
        if btn.name in self.mqtt_topics_in:
            raise Exception(f"Control {btn.name} already exist in mqtt_topics_in.")
        self.mqtt_topics_in[btn.name] = {}
        self.mqtt_topics_in[btn.name]["set_light"] = (btn, self.callback_unset)
        # Topics Out
        self.mqtt_topics_out[btn.name] = {}
        self.mqtt_topics_out[btn.name]["event/down"] = (btn, self.callback_unset)
        self.mqtt_topics_out[btn.name]["event/up"] = (btn, self.callback_unset)
        # MIDI Triggers
        # Set midi_triggers[channel][midi_id][type] = (button_object, button_callback)
        if btn.channel not in self.midi_triggers:
            self.midi_triggers[btn.channel] = {}
        if btn.midi_id not in self.midi_triggers[btn.channel]:
            self.midi_triggers[btn.channel][btn.midi_id] = {}
        if btn.midi_type == MIDIType.ControlChange:
            self.midi_triggers[btn.channel][btn.midi_id]['control_change'] = (btn, self.callback_unset)
        elif btn.midi_type == MIDIType.Note:
            self.midi_triggers[btn.channel][btn.midi_id]['note_on'] = (btn, self.callback_unset)
            self.midi_triggers[btn.channel][btn.midi_id]['note_off'] = (btn, self.callback_unset)
        # Set object
        setattr(self, btn.name, btn)
        self.elements.append(btn)

    def add_control_pitch_wheel(self, pitchwheel: PitchWheel):
        # Topics In
        if pitchwheel.name in self.mqtt_topics_in:
            raise Exception(f"Control {pitchwheel.name} already exist in mqtt_topics_in.")
        self.mqtt_topics_in[pitchwheel.name] = {}
        self.mqtt_topics_in[pitchwheel.name]["set_pitch"] = (pitchwheel, self.callback_unset)
        # Topics Out
        self.mqtt_topics_out[pitchwheel.name] = {}
        self.mqtt_topics_out[pitchwheel.name]["event/touch"] = (pitchwheel, self.callback_unset)
        self.mqtt_topics_out[pitchwheel.name]["event/release"] = (pitchwheel, self.callback_unset)
        self.mqtt_topics_out[pitchwheel.name]["event/pitch"] = (pitchwheel, self.callback_unset)
        # MIDI Triggers
        # Set midi_triggers[channel][midi_id][type] = (button_object, button_callback)
        if pitchwheel.pitchwheel_channel not in self.midi_triggers:
            self.midi_triggers[pitchwheel.pitchwheel_channel] = {}
        if pitchwheel.touch_channel not in self.midi_triggers:
            self.midi_triggers[pitchwheel.touch_channel] = {}

        if pitchwheel.touch_midi_id not in self.midi_triggers[pitchwheel.touch_channel]:
            self.midi_triggers[pitchwheel.touch_channel][pitchwheel.touch_midi_id] = {}
        if pitchwheel.pitchwheel_midi_id not in self.midi_triggers[pitchwheel.pitchwheel_channel]:
            self.midi_triggers[pitchwheel.pitchwheel_channel][pitchwheel.pitchwheel_midi_id] = {}

        self.midi_triggers[pitchwheel.touch_channel][pitchwheel.touch_midi_id]['note_on'] = (pitchwheel, self.callback_unset)
        self.midi_triggers[pitchwheel.touch_channel][pitchwheel.touch_midi_id]['note_off'] = (pitchwheel, self.callback_unset)
        self.midi_triggers[pitchwheel.pitchwheel_channel][pitchwheel.pitchwheel_midi_id]['pitchwheel'] = (pitchwheel, self.callback_unset)
        # Set object
        setattr(self, pitchwheel.name, pitchwheel)
        self.elements.append(pitchwheel)

    def add_control_knob(self, knob: Knob):
        # Topics Out
        self.mqtt_topics_out[knob.name] = {}
        self.mqtt_topics_out[knob.name]["event/down"] = (knob, self.callback_unset)
        self.mqtt_topics_out[knob.name]["event/up"] = (knob, self.callback_unset)
        self.mqtt_topics_out[knob.name]["event/rotate"] = (knob, self.callback_unset)
        # MIDI Triggers
        # Set midi_triggers[channel][midi_id][type] = (knob_object, knob_callback)
        if knob.midi_channel not in self.midi_triggers:
            self.midi_triggers[knob.midi_channel] = {}
        if knob.midi_touch not in self.midi_triggers[knob.midi_channel]:
            self.midi_triggers[knob.midi_channel][knob.midi_touch] = {}
        if knob.midi_rotate not in self.midi_triggers[knob.midi_channel]:
            self.midi_triggers[knob.midi_channel][knob.midi_rotate] = {}
        self.midi_triggers[knob.midi_channel][knob.midi_touch]['note_on'] = (knob, self.callback_unset)
        self.midi_triggers[knob.midi_channel][knob.midi_touch]['note_off'] = (knob, self.callback_unset)
        self.midi_triggers[knob.midi_channel][knob.midi_rotate]['control_change'] = (knob, self.callback_unset)
        # Set object
        setattr(self, knob.name, knob)
        self.elements.append(knob)


class FaderportControlsMidi2MQTT(FaderportControls):
    def __init__(self, faderport):
        super(FaderportControlsMidi2MQTT, self).__init__()
        self.faderport = faderport
        self.mqtt_client = self.faderport.mqtt_client

        # Set callbacks for all elements
        for element in self.elements:
            if type(element) is Button:
                # Sender
                element.callback_set_light = self.callback_button_set_light
                # Topics In
                self.mqtt_topics_in[element.name]["set_light"] = (element, self.callback_button_set_light_parse_mqtt)
                # MIDI Triggers
                if element.midi_type == MIDIType.ControlChange:
                    self.midi_triggers[element.channel][element.midi_id]['control_change'] = (element, self.callback_button_event_parse_midi)
                elif element.midi_type == MIDIType.Note:
                    self.midi_triggers[element.channel][element.midi_id]['note_on'] = (element, self.callback_button_event_parse_midi)
                    self.midi_triggers[element.channel][element.midi_id]['note_off'] = (element, self.callback_button_event_parse_midi)
            elif type(element) is PitchWheel:
                # Sender
                element.callback_pitchwheel_set_pitch = self.callback_pitch_wheel_set_pitch
                # Topics In
                self.mqtt_topics_in[element.name]["set_pitch"] = (element, self.callback_pitch_wheel_set_pitch_parse_mqtt)
                # MIDI Triggers
                self.midi_triggers[element.touch_channel][element.touch_midi_id]['note_on'] = (element, self.callback_pitch_wheel_event_parse_midi)
                self.midi_triggers[element.touch_channel][element.touch_midi_id]['note_off'] = (element, self.callback_pitch_wheel_event_parse_midi)
                self.midi_triggers[element.pitchwheel_channel][element.pitchwheel_midi_id]['pitchwheel'] = (element, self.callback_pitch_wheel_event_parse_midi)
            elif type(element) is Knob:
                # MIDI Triggers
                self.midi_triggers[element.midi_channel][element.midi_touch]['note_on'] = (element, self.callback_knob_event_parse_midi)
                self.midi_triggers[element.midi_channel][element.midi_touch]['note_off'] = (element, self.callback_knob_event_parse_midi)
                self.midi_triggers[element.midi_channel][element.midi_rotate]['control_change'] = (element, self.callback_knob_event_parse_midi)

    def callback_button_set_light(self, button: Button, color_to_set):
        self.faderport.button_set_color(button, color_to_set)

    def callback_button_event_parse_midi(self, control_object, msg):
        if msg.type == "control_change":
            if msg.value > 0:
                payload = f"{msg.value}"
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/down"
            else:
                payload = f"{msg.value}"
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/up"
        elif msg.type == "note_on":
            payload = f"{msg.velocity}"
            if msg.velocity == 0:
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/up"
            else:
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/down"
        elif msg.type == "note_off":
            payload = f"{msg.velocity}"
            topic = f"{self.mqtt_prefix}/{control_object.name}/event/up"
        else:
            return
        self.mqtt_client.publish(topic=topic, payload=payload)

    def callback_button_set_light_parse_mqtt(self, topics, control_object, msg):
        # print(f"callback_display for {control_object.name} msg {topics} {msg.payload}")
        try:
            if topics[2] == "set_light":
                control_object.set_light(msg.payload)
            else:
                print(f"callback_button_set_light() Couldn't parse topic {topics[2]}.")
                return
        except Exception as ex:
            self.mqtt_client.publish(topic=f"{topics[0]}/{topics[1]}/error", payload=str(ex))

    def callback_pitch_wheel_set_pitch(self, channel: int, pitch_value: int):
        self.faderport.send_pitch_wheel(channel, pitch_value)

    def callback_pitch_wheel_event_parse_midi(self, control_object, msg):
        if msg.type == "note_on":
            payload = f"{msg.velocity}"
            if msg.velocity == 0:
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/release"
            else:
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/touch"
        elif msg.type == "note_off":
            payload = f"{msg.velocity}"
            topic = f"{self.mqtt_prefix}/{control_object.name}/event/release"
        elif msg.type == "pitchwheel":
            payload = f"{msg.pitch}"
            topic = f"{self.mqtt_prefix}/{control_object.name}/event/pitch"
            control_object.pitch = msg.pitch
        else:
            return
        self.mqtt_client.publish(topic=topic, payload=payload)

    def callback_pitch_wheel_set_pitch_parse_mqtt(self, topics, control_object, msg):
        # print(f"callback_pitch_wheel_set_pitch for {control_object.name} msg {topics} {msg.payload}")
        try:
            if topics[2] == "set_pitch":
                control_object.set_pitch(msg.payload)
            else:
                print(f"callback_pitch_wheel_set_pitch() Couldn't parse topic {topics[2]}.")
                return
        except Exception as ex:
            self.mqtt_client.publish(topic=f"{topics[0]}/{topics[1]}/error", payload=str(ex))

    def callback_knob_event_parse_midi(self, control_object, msg):
        if msg.type == "control_change":
            if msg.value > 0 and msg.value < 64:
                payload = f"{msg.value}"
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/rotate"
            else:
                payload = f"{(msg.value-64) * -1}"
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/rotate"
        elif msg.type == "note_on":
            if msg.velocity == 0:
                payload = f"{msg.velocity}"
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/up"
            else:
                payload = f"{msg.velocity}"
                topic = f"{self.mqtt_prefix}/{control_object.name}/event/down"
        else:
            return
        self.mqtt_client.publish(topic=topic, payload=payload)


if __name__ == '__main__':
    a = Button(name="button_a", midi_type=MIDIType.Note, channel=0, midi_id=46, luminance_type=LightTypes.RedYellow)
    print(repr(a))
