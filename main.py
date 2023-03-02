#!/usr/bin/env python3
"""DiscoLisko - Sound Reactive Lights with Python and Philips Hue"""
import sys
from time import sleep
from xml.dom.minidom import CDATASection
import numpy as np
import sounddevice as sd
from hue_api import HueApi, exceptions as huex

BRIDGE_IP_ADDRESS = "192.168.1.4"


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

    def callback(
        indata: np.ndarray,
        _frames: int,
        _time: CDATASection,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            print(status)

        avg_volume = rms(indata)
        # print(f"Average volume: {avg_volume}")

        # Volume thresholds have to be adjusted depending on the environment
        # and the microphone used
        match avg_volume:
            case avg_volume if avg_volume > 0.1:
                for light in lights:
                    light.set_brightness(255)
            case avg_volume if avg_volume > 0.05:
                for light in lights:
                    light.set_brightness(128)
            case _:
                for light in lights:
                    light.set_brightness(0)

    stream = sd.InputStream(channels=1, callback=callback)

    try:
        print("Press Ctrl+C to stop the recording")
        stream.start()
        while True:
            pass
    except KeyboardInterrupt:
        print("Interrupted by user")
        stream.abort()
        for light in lights:
            light.set_off()


if __name__ == "__main__":
    main()
