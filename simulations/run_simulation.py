import subprocess
import sys
import os
import threading
import time
import signal

_SIM_DIR = os.path.dirname(os.path.abspath(__file__))

_MOCKS = [
    ("mock_sensor_node", "mock_sensor_node.py",  "IMU, environment, air      "),
    ("mock_power_node",  "mock_power_node.py",   "battery draining slowly    "),
    ("mock_gps_lidar",   "mock_gps_lidar.py",    "GPS fix + LiDAR sweep      "),
    ("mock_led_node",    "mock_led_node.py",      "LED command monitor        "),
]

_BANNER = """
╔══════════════════════════════════════════════════════╗
║         VirtualHelmet Simulation Running             ║
║         Broker: 127.0.0.1:1883                       ║
╠══════════════════════════════════════════════════════╣
║  [OK] mock_sensor_node  — IMU, environment, air      ║
║  [OK] mock_power_node   — battery draining slowly    ║
║  [OK] mock_gps_lidar    — GPS fix + LiDAR sweep      ║
║  [OK] mock_led_node     — LED command monitor        ║
╠══════════════════════════════════════════════════════╣
║  To start HUD:                                       ║
║    py -3 brain/hud/main.py                           ║
║  To start orchestrator:                              ║
║    py -3 brain/orchestrator/main.py                  ║
╠══════════════════════════════════════════════════════╣
║  Test commands (run in another terminal):            ║
║    mosquitto_pub -t helmet/voice/commands            ║
║      -m '{"command":"battery"}'                      ║
║    mosquitto_pub -t helmet/voice/commands            ║
║      -m '{"command":"lights_on"}'                    ║
║    mosquitto_pub -t helmet/hud/overlay               ║
║      -m '{"theme":"night_mode"}'                     ║
╚══════════════════════════════════════════════════════╝
""".strip()


def stream_output(proc: subprocess.Popen, label: str):
    for line in iter(proc.stdout.readline, b""):
        text = line.decode(errors="replace").rstrip()
        if text:
            print(f"[{label}] {text}", flush=True)


def main():
    procs = []

    for label, script, _ in _MOCKS:
        script_path = os.path.join(_SIM_DIR, script)
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        procs.append((label, proc))
        t = threading.Thread(target=stream_output, args=(proc, label), daemon=True)
        t.start()

    # Give processes a moment to connect before printing the banner
    time.sleep(1.5)
    print(_BANNER)
    print(flush=True)

    def shutdown(signum=None, frame=None):
        print("\n[run_simulation] Shutting down mock nodes...", flush=True)
        for label, proc in procs:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                print(f"[run_simulation] Stopped {label}", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        time.sleep(5)
        for label, proc in procs:
            if proc.poll() is not None:
                print(
                    f"[run_simulation] WARNING: {label} exited unexpectedly "
                    f"(returncode={proc.returncode})",
                    flush=True,
                )


if __name__ == "__main__":
    main()
