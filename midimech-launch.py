#!/usr/bin/env python3
"""
midimech launcher — starts the virtual MIDI cable (C native) and midimech.

The MIDI cable (midimech-vport) runs as a separate process for zero-overhead
MIDI forwarding, equivalent to loopMIDI on Windows.
"""

import subprocess
import sys
import os
import time


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.normpath(os.path.join(script_dir, "..", "bin"))

    # Start the native MIDI virtual cable
    vport_bin = os.path.join(bin_dir, "midimech-vport")
    if not os.path.exists(vport_bin):
        # Fallback for development
        vport_bin = os.path.join(script_dir, "midimech-vport")

    vport_proc = subprocess.Popen([vport_bin])

    # Give the virtual port a moment to register with ALSA
    time.sleep(0.3)

    # Find and launch midimech
    midimech_py = os.path.join(script_dir, "midimech.py")
    if not os.path.exists(midimech_py):
        midimech_py = os.path.join(script_dir, "..", "share", "midimech", "midimech.py")

    print("[launcher] Starting midimech...")
    proc = subprocess.Popen(
        [sys.executable, midimech_py],
        cwd=os.path.dirname(os.path.abspath(midimech_py)),
    )

    # Wait for midimech to exit
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()

    # Clean up the virtual port
    vport_proc.terminate()
    vport_proc.wait()

    print("[launcher] midimech exited, cleaning up")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main() or 0)
