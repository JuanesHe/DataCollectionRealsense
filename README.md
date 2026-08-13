# DataCollectionRealsense

Record depth and color streams from two Intel RealSense cameras into one BAG file per camera.

## Requirements

- Python 3.10 or newer
- Two connected RealSense cameras
- The Intel RealSense SDK and Python package:

```bash
pip install pyrealsense2
```

## Record

Run the recorder from the repository root:

```bash
python3 record_realsense.py
```

The program checks for at least two cameras, binds each pipeline to its serial number, and writes files under a timestamped directory such as `recordings/20260813_143000/`. Press `Ctrl+C` to stop and finalize the BAG files safely.

To make a short test recording without using `Ctrl+C`:

```bash
python3 record_realsense.py --duration 10 --output-dir ./data
```

The default streams are depth at `848x480` and color at `1280x720`, both at 30 FPS. Change the stream settings in `record_realsense.py` if your camera model does not support them.

The pipelines start one after another as quickly as the SDK allows. This records both cameras concurrently, but it is not a hardware-synchronized capture. For frame-level synchronization, connect the cameras using the hardware sync pins and configure the appropriate master/slave settings for your camera models.

## File formats

This recorder produces files per camera using two common extensions:

- `.db3` (default): SQLite-backed RealSense recording used by the RealSense SDK and `pyrealsense2`. Filenames follow the pattern `camera_{index}_{serial}.db3` (for example `camera_1_239722070007.db3`). Advantages: preserves device timestamps and richer device-specific metadata, supports transactional writes and fast random access, and is the preferred format for RealSense-native tooling.
- `.bag`: ROS/ROS2 bag format (topic/message model). Filenames would typically be `camera_{index}_{serial}.bag`. Advantages: native ROS tooling and replay, good for heterogeneous ROS messages and pipelines.

Notes:
- The script currently writes `.db3` files by default because the RealSense SDK expects DB3 recordings for full metadata fidelity. If your downstream pipeline requires ROS bags, record in the format your tools expect or convert carefully in post (conversion may lose device-specific metadata).
- For reliable cross-camera synchronization, prefer hardware sync (master/slave) regardless of output format. If hardware sync isn't available, align by device timestamps recorded in `.db3` or by ROS header timestamps in `.bag` after ensuring a common clock.

If you want the recorder to optionally write `.bag` files (or both formats) automatically, I can add a `--format db3|bag|both` option to `record_realsense.py` and preserve device timestamps in the recordings.
