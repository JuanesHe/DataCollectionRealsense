"""Record depth and color streams from two RealSense cameras into DB3 files."""

import argparse
import time
from datetime import datetime
from pathlib import Path

import pyrealsense2 as rs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record depth and color streams from RealSense cameras."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("recordings"),
        help="Directory for recording sessions (default: recordings).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Stop after this many seconds; otherwise record until Ctrl+C.",
    )
    parser.add_argument(
        "--camera-count",
        type=int,
        default=2,
        help="Number of cameras to record (default: 2).",
    )
    return parser.parse_args()


def discover_devices(ctx: rs.context, camera_count: int) -> list[tuple[str, str]]:
    devices = ctx.query_devices()
    if len(devices) < camera_count:
        raise RuntimeError(
            f"Found {len(devices)} camera(s); at least {camera_count} are required."
        )

    selected = []
    for index, device in enumerate(devices[:camera_count], start=1):
        serial = device.get_info(rs.camera_info.serial_number)
        name = device.get_info(rs.camera_info.name)
        print(f"Camera {index}: {name} (serial {serial})")
        selected.append((serial, name))
    return selected


def record_cameras(output_dir: Path, duration: float | None, camera_count: int) -> None:
    if camera_count < 1:
        raise ValueError("camera-count must be at least 1")
    if duration is not None and duration <= 0:
        raise ValueError("duration must be greater than zero")

    ctx = rs.context()
    devices = discover_devices(ctx, camera_count)
    session_dir = output_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir.mkdir(parents=True, exist_ok=False)

    pipelines: list[rs.pipeline] = []
    configs: list[rs.config] = []
    try:
        for index, (serial, _) in enumerate(devices, start=1):
            config = rs.config()
            config.enable_device(serial)
            config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
            db_path = session_dir / f"camera_{index}_{serial}.db3"
            config.enable_record_to_file(str(db_path))

            pipelines.append(rs.pipeline(ctx))
            configs.append(config)
            print(f"Camera {index} will record to {db_path}")

        for pipeline, config in zip(pipelines, configs):
            pipeline.start(config)

        print("Recording started. Press Ctrl+C to stop.")
        started_at = time.monotonic()
        while duration is None or time.monotonic() - started_at < duration:
            for pipeline in pipelines:
                pipeline.poll_for_frames()
            time.sleep(0.001)
    finally:
        for pipeline in pipelines:
            try:
                pipeline.stop()
            except RuntimeError:
                pass
        print(f"Recording files saved in {session_dir}")


def main() -> int:
    args = parse_args()
    try:
        record_cameras(args.output_dir, args.duration, args.camera_count)
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}")
        return 1
    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())