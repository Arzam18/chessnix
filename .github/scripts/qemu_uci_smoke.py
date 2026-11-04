#!/usr/bin/env python3
"""Run a UCI handshake and a real depth-2 search on an AArch64 binary via QEMU."""

from __future__ import annotations

import os
import select
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <aarch64-engine>", file=sys.stderr)
        return 2

    binary = str(Path(sys.argv[1]).resolve())
    if not Path(binary).is_file():
        print(f"Engine binary not found: {binary}", file=sys.stderr)
        return 2

    print(f"Testing: {binary}", flush=True)
    process = subprocess.Popen(
        ["qemu-aarch64", "-cpu", "max", binary],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    assert process.stdin is not None
    assert process.stdout is not None

    pending = bytearray()

    def send(command: str) -> None:
        process.stdin.write((command + "\n").encode("ascii"))
        process.stdin.flush()

    def read_line(deadline: float) -> str:
        while True:
            newline = pending.find(b"\n")
            if newline >= 0:
                line = bytes(pending[:newline])
                del pending[: newline + 1]
                return line.decode("utf-8", errors="replace").rstrip("\r")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for UCI output")

            ready, _, _ = select.select([process.stdout], [], [], remaining)
            if not ready:
                raise TimeoutError("Timed out waiting for UCI output")

            chunk = os.read(process.stdout.fileno(), 4096)
            if not chunk:
                raise RuntimeError(f"Engine exited unexpectedly (status {process.poll()})")
            pending.extend(chunk)

    def expect(fragment: str, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while True:
            line = read_line(deadline)
            print(line, flush=True)
            if fragment in line:
                return

    try:
        send("uci")
        expect("uciok", 10)

        send("isready")
        expect("readyok", 10)

        send("position startpos")
        send("go depth 2")
        expect("bestmove ", 30)
        # Let the controller thread finish its join and clear the busy flag.
        time.sleep(0.15)

        send("quit")
        process.wait(timeout=10)
        if process.returncode != 0:
            raise RuntimeError(f"Engine returned exit status {process.returncode}")

        print("PASS: UCI handshake and depth-2 search completed", flush=True)
        return 0
    except Exception as exc:  # Keep CI failures explicit and terminate the child.
        print(f"FAIL: {exc}", file=sys.stderr, flush=True)
        process.kill()
        process.wait(timeout=5)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
