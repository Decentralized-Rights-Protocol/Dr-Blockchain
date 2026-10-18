#!/usr/bin/env python3
"""Start a disposable single-validator DRP node, check RPC, restart it, and check height persists.

Uses a fresh temporary home and test keyring. Node output is kept in that temporary
directory and is not printed because initialization output can include a test mnemonic.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

CHAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.environ.get("BIN", os.path.join(CHAIN_DIR, "build", "drpd"))
RPC = "http://127.0.0.1:26657"


def rpc(path):
    with urllib.request.urlopen(RPC + path, timeout=2) as response:
        return json.load(response) if path != "/health" else response.status


def wait_for_height(minimum, process, deadline_seconds=90):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"drpd exited early with code {process.returncode}")
        try:
            status = rpc("/status")["result"]
            height = int(status["sync_info"]["latest_block_height"])
            if height >= minimum and rpc("/health") == 200:
                return status, height
        except (OSError, KeyError, ValueError):
            pass
        time.sleep(1)
    raise TimeoutError(f"block height did not reach {minimum}")


def start(env, log_path):
    log = open(log_path, "ab")
    return subprocess.Popen(
        [BIN, "start", "--home", env["HOME_DIR"], "--minimum-gas-prices", "0udrp"],
        stdout=log,
        stderr=subprocess.STDOUT,
    )


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main():
    tmp = tempfile.mkdtemp(prefix="drp-localnet-")
    home = os.path.join(tmp, "home")
    env = dict(os.environ, HOME_DIR=home, BIN=BIN, CHAIN_ID="drp-ci-1")
    init_log = os.path.join(tmp, "init.log")
    node_log = os.path.join(tmp, "node.log")
    process = None
    try:
        script = os.path.join(CHAIN_DIR, "scripts", "localnet.sh")
        with open(init_log, "wb") as log:
            # Run every setup step except the final foreground start.
            setup = open(script, encoding="utf-8").read().rsplit('echo "==> Starting node"', 1)[0]
            subprocess.run(["bash", "-c", setup], env=env, check=True, stdout=log, stderr=subprocess.STDOUT)
        subprocess.run([BIN, "validate-genesis", "--home", home], check=True)

        process = start(env, node_log)
        status, first_height = wait_for_height(2, process)
        print(f"network={status['node_info']['network']} height={first_height} health=ok")
        stop(process)

        process = start(env, node_log)
        _, restarted_height = wait_for_height(first_height + 1, process)
        print(f"restart_height={restarted_height} (previous={first_height})")
        return 0
    except Exception as exc:  # noqa: BLE001 - report the failed stage in CI
        print(f"localnet validation failed: {exc}", file=sys.stderr)
        for path in (node_log,):
            if os.path.exists(path):
                lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
                print("\n".join(line for line in lines[-80:] if "mnemonic" not in line.lower()), file=sys.stderr)
        return 1
    finally:
        if process and process.poll() is None:
            stop(process)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
