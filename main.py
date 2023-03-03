#!/usr/bin/env python3
"""DiscoLisko - Sound Reactive Lights with Python and Philips Hue"""
from queue import LifoQueue
import sys
from time import sleep
from xml.dom.minidom import CDATASection
import numpy as np
import sounddevice as sd
from hue_api import HueApi, exceptions as huex

BRIDGE_IP_ADDRESS = "192.168.0.176"


def attempt_connection(api: HueApi):
    """Prompts the user to initialize connection by pressing the button"""
    try:
        api.load_existing()
        return
    except huex.UninitializedException:
        print("Not initialized, attempting to create a new connection")

    try:
        print("Please press the button on the Hue Bridge...")
        sleep(5)
        api.create_new_user(BRIDGE_IP_ADDRESS)
    except huex.ButtonNotPressedException:
        print("Button not pressed, exiting...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
        sys.exit(1)


def rms(data: np.ndarray) -> float:
    """Calculate the root mean square of the data"""
    return np.sqrt(np.mean(np.square(data), axis=0))


def main():
    """Main function"""
    api = HueApi()

    print("Connecting to Hue Bridge...")
    attempt_connection(api)
    print("Connected to Hue Bridge")
    lights = api.fetch_lights()

    for light in lights:
        light.set_on()

    # Use a LIFO queue to store the last 100 volume values
    running_window: LifoQueue[int] = LifoQueue(maxsize=100)

    def callback(
        indata: np.ndarray,
        _frames: int,
        _time: CDATASection,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            print(status)

        data_channel_avg = rms(indata)
        if running_window.full():
            running_window.get()
        data_avg = np.average(data_channel_avg, axis=0)
        running_window.put(data_avg)

    stream = sd.InputStream(channels=2, callback=callback)

    try:
        print("Press Ctrl+C to stop the recording")
        stream.start()
        while True:
            # Update the lights every 100ms
            sleep(0.1)

            # Volume thresholds have to be adjusted depending on the environment
            # and the microphone used
            avg_volume = np.average(running_window.queue)
            print(f"Average volume: {avg_volume}")
            match (avg_volume):
                case avg_volume if avg_volume > 0.4:
                    for light in lights:
                        light.set_brightness(255)
                        light.set_color(3, 128)
                case avg_volume if avg_volume > 0.3:
                    for light in lights:
                        light.set_brightness(196)
                        light.set_color(3, 128)
                case avg_volume if avg_volume > 0.2:
                    for light in lights:
                        light.set_brightness(164)
                        light.set_color(3, 128)
                case avg_volume if avg_volume > 0.1:
                    for light in lights:
                        light.set_brightness(128)
                        light.set_color(3, 128)
                case _:
                    for light in lights:
                        light.set_brightness(0)
    except KeyboardInterrupt:
        print("Interrupted by user")
        stream.abort()
        for light in lights:
            light.set_off()


if __name__ == "__main__":
    main()
