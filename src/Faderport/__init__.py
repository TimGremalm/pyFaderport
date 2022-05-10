import threading
from time import sleep
import re
import mido  # https://github.com/mido/mido, also run pip3 install python-rtmidi --install-option="--no-jack"
import paho.mqtt.client as mqtt
from Faderport.constants import *
from Faderport.structure import FaderportControls


class Faderport(threading.Thread):
    def __init__(self, port_user: str = "", print_midi: bool = False, test_mode: bool = False):
        """
        Init a Faderport object and prepare MIDI-connections.
        :type test_mode: Test-mode write control-values back so buttons light up.
        :type print_midi: Shows MIDI-messages in the console.
        :type port_user: Set MIDI IO-port for Faderport8 Port User.
                         Port is found via a regex search of available ports.
                         Usually: PreSonus FP8:PreSonus FP8 MIDI 1 16:0
        """
        # Flags
        self.print_midi = print_midi
        self.test_mode = test_mode

        # Find port names
        self._ports_midi = mido.get_ioport_names()
        self.port_user = self._find_port(port_user, "PreSonus.*FP8")

        # Instantiate variables
        self.midi_user = None
        self.mqtt_client = None
        self.controls = None
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.quit = False

    def midi_parse(self, msg):
        if msg.type == 'control_change':
            midi_id = msg.control
        elif msg.type == 'note_on' or msg.type == 'note_off':
            midi_id = msg.note
        elif msg.type == 'polytouch':
            midi_id = msg.note
        elif msg.type == 'pitchwheel':
            midi_id = 'pitchwheel'
        else:
            return
        # Callback if MIDI message in self.controls.topics_out
        if msg.channel in self.controls.topics_out:
            if midi_id in self.controls.topics_out[msg.channel]:
                if msg.type in self.controls.topics_out[msg.channel][midi_id]:
                    control_object = self.controls.topics_out[msg.channel][midi_id][msg.type][0]
                    callback = self.controls.topics_out[msg.channel][midi_id][msg.type][1]
                    callback(control_object, msg)

    def run(self):
        self.midi_user = mido.open_ioport(self.port_user)
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self._mqtt_on_connected
        self.mqtt_client.on_message = self._mqtt_on_message
        self.mqtt_client.connect(host="127.0.0.1")
        self.mqtt_client.loop_start()
        self.controls = FaderportControls(faderport=self)
        while True:
            if self.quit:
                self.mqtt_client.loop_stop()
                return
            msg = self.midi_user.receive(False)
            if msg:
                if self.test_mode:
                    if msg.type == 'note_on':
                        if msg.velocity == 0:
                            self.send_note_on(channel=msg.channel, note=msg.note, velocity=0)
                        else:
                            self.send_note_on(channel=msg.channel, note=msg.note, velocity=2)
                    if msg.type == 'note_off':
                        self.send_note_on(channel=msg.channel, note=msg.note, velocity=0)
                    if msg.type == 'control_change':
                        if msg.value == 127:
                            self.send_control_change(channel=msg.channel, control=msg.control, value=2)
                        else:
                            self.send_control_change(channel=msg.channel, control=msg.control, value=0)
                if self.print_midi:
                    print(f"User {msg}")
                self.midi_parse(msg)
            sleep(0.001)

    @staticmethod
    def _mqtt_on_connected(client, userdata, flags, rc):
        print(f"MQTT Connected with result code {rc}")
        client.subscribe("faderport/#")

    def _mqtt_on_message(self, client, userdata, msg):
        # print(f"MQTT {msg.topic} {msg.payload}")
        topics = msg.topic.split("/")
        # Ex. topic faderport/left_play/event/down
        if len(topics) >= 3:
            # Set topics_in[btn.name]["set_light"] = set_light_callback
            if topics[1] in self.controls.topics_in:
                if topics[2] in self.controls.topics_in[topics[1]]:
                    control_object = self.controls.topics_in[topics[1]][topics[2]][0]
                    callback = self.controls.topics_in[topics[1]][topics[2]][1]
                    callback(topics, control_object, msg)

    def __repr__(self):
        out = f"Faderport"
        out += f"\n\t{self.midi_user}"
        return out

    def send_control_change(self, channel: int, control: int, value: int):
        """
        Send a Control-Change message to the Faderport.
        :param channel: int channel number 0-127
        :param control: int Control 0-127
        :param value: int Value 0-127
        """
        m = mido.Message('control_change', channel=channel, control=control, value=value)
        self.midi_user.send(m)

    def send_note_on(self, channel: int, note: int, velocity: int):
        """
        Send a Note-On message to the Faderport.
        :param channel: int channel number 0-127
        :param note: int Note 0-127
        :param velocity: int Velocity 0-127
        """
        m = mido.Message('note_on', channel=channel, note=note, velocity=velocity)
        self.midi_user.send(m)

    def send_note_off(self, channel: int, note: int, velocity: int):
        """
        Send a Note-Off message to the Faderport.
        :param channel: int channel number 0-127
        :param note: int Note 0-127
        :param velocity: int Velocity 0-127
        """
        m = mido.Message('note_off', channel=channel, note=note, velocity=velocity)
        self.midi_user.send(m)

    def send_pitch_wheel(self, channel: int, pitch_value: int):
        """
        Send a Pitch-Wheel message to the Faderport.
        :param channel: int channel number 0-127
        :param pitch_value: int Note 0-127
        """
        m = mido.Message('pitchwheel', channel=channel, pitch=pitch_value)
        self.midi_user.send(m)

    def send_faderport_sysex(self, d: list):
        """
        Send a sysex-message to the Faderport.
        :param d: list of bytes to send. No value can be larger than 127 due to the MIDI-standard.
        """
        m = mido.Message('sysex')
        # Prefix Manufacturer and Product ID before the message. Mido will prefix sysex-command (240) and suffix (247).
        m.data = SYSEX_PREFIX_FADERPORT + d
        self.midi_user.send(m)

    def _find_port(self, port_name: str, fallback: str) -> str:
        if port_name:
            port_name_to_search = port_name
        else:
            port_name_to_search = fallback
        if not port_name_to_search.startswith(".*"):
            port_name_to_search = ".*" + port_name_to_search
        if not port_name_to_search.endswith(".*"):
            port_name_to_search += ".*"
        r = re.compile(port_name_to_search, re.IGNORECASE)
        port_matches = list(filter(r.match, self._ports_midi))
        found_port = next(iter(port_matches), None)
        if found_port:
            return found_port
        else:
            raise Exception(f"Couldn't find {port_name} in listed IO-ports {self._ports_midi}.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--printmidi', '-p',
                        action='store_true',
                        help="Shows MIDI-messages in the console.")
    parser.add_argument('--midiportuser', "--user",
                        type=str, default="",
                        help="Set MIDI IO-port for Faderport Port User. "
                             "Default: PreSonus FP8:PreSonus FP8 MIDI 1 16:0")
    parser.add_argument('--shell', '-s',
                        action='store_true',
                        help='Start an interactive ipython shell where you can interact with the Faderport 8.')
    parser.add_argument('--test', '-t',
                        action='store_true',
                        help='Test-mode write control-values back so buttons light up.')
    parser.add_argument('--printports', '-l',
                        action='store_true',
                        help='Lists available MIDI IO ports.')
    args = parser.parse_args()

    print("Faderport 8")
    if args.printports:
        print("MIDI IO ports:")
        io_ports = mido.get_ioport_names()
        for port in io_ports:
            print(f"\t{port}")
        print("exit...")
    else:
        faderport = Faderport(print_midi=args.printmidi,
                              port_user=args.midiportuser,
                              test_mode=args.test)
        faderport.start()
        if args.shell:
            from pysh.shell import Pysh  # https://github.com/TimGremalm/pysh

            banner = ['Faderport8 Shell',
                      'You may leave this shell by typing `exit`, `q` or pressing Ctrl+D',
                      'faderport is the main object.']
            Pysh(dict_to_include={'faderport': faderport},
                 prompt="Faderport$ ",
                 banner=banner)
        else:
            run = True
            while run:
                try:
                    sleep(0.1)
                except KeyboardInterrupt:
                    run = False
                    print("KeyboardInterrupt, exit...")
        faderport.quit = True
