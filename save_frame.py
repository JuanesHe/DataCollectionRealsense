import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np
import pyrealsense2 as rs
import Jetson.GPIO as GPIO
TRIGGER_PIN = 40

def discover_devices(ctx: rs.context) -> list[tuple[str, str]]:
    selected_devices = []
    for device in ctx.query_devices():
        serial = device.get_info(rs.camera_info.serial_number)
        name = device.get_info(rs.camera_info.name)
        print(f"Serial Number: {serial}, Name: {name}")
        selected_devices.append((serial, name))
    return selected_devices

class Trigger:
    def __init__(self, pin: int) -> None:
        self.gpio = GPIO
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.IN)
        self.fired_last = False

    def fired(self) -> bool:
        if self.gpio.input(self.pin) != self.gpio.HIGH:
            self.fired_last = False
            return False
        if self.fired_last:
           return False
        self.fired_last = True
        return True

    def close(self) -> None:
        self.gpio.cleanup(self.pin)

def open_pipelines(
    context: rs.context, devices: list[tuple[str, str]]) -> dict[str, rs.pipeline]:
    pipelines = {}
    for serial, name in devices:
        config = rs.config()
        config.enable_device(serial)
        config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

        pipeline = rs.pipeline(context)
        try:
            pipeline.start(config)
        except RuntimeError as error:
            print(f"{serial} ({name}) failed to start: {error}")
            continue
        pipelines[serial] = pipeline
        print(f"{serial} ({name}) streaming")
    return pipelines


def save_frame(serial: str, frames: rs.composite_frame, directory: Path) -> bool:
    color_frame = frames.get_color_frame()
    depth_frame = frames.get_depth_frame()

    stamp = datetime.now().strftime("%M%S_%f")[:-3]
    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())
    cv2.imwrite(str(directory / f"{stamp}_depth.png"), depth_image)
    cv2.imwrite(str(directory / f"{stamp}_color.png"), color_image)
    return True

def capture_loop(pipelines: dict[str, rs.pipeline], trigger, directory: Path) -> None:
    saved = 0
    while True:
        latest = {}
        for serial, pipeline in pipelines.items():
            frames = pipeline.wait_for_frames()
            latest[serial] = frames

        if trigger.fired():
            for serial, frames in latest.items():
                if save_frame(serial, frames, directory):
                    saved += 1
            print(f"captured — {saved} files total")

        if getattr(trigger, "should_quit", False):
            break

def start_camera() -> None:
    context = rs.context()
    devices = discover_devices(context)
    if not devices:
        raise RuntimeError("No device found")

    directory = Path("frames").resolve()
    directory.mkdir(parents=True, exist_ok=True)

    trigger = Trigger(TRIGGER_PIN)
    pipelines = open_pipelines(context, devices)
    try:
        capture_loop(pipelines, trigger, directory)
    except KeyboardInterrupt:
        print("stopping")
    finally:
        for pipeline in pipelines.values():
            pipeline.stop()
        trigger.close()


def main() -> int:
    try:
        start_camera()
    except (RuntimeError, ValueError) as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())