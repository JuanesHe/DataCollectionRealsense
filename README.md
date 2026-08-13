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
