#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.*"
# dependencies = []
# ///

import subprocess
import sys
from os import getenv
from typing import NoReturn


def _help(exit_code: int = 0) -> NoReturn:
    """Print usage of script and exit"""
    _script_name = __file__.split("/")[-1]
    print(f"""Usage: TAG_MAPPINGS="IMAGE1:41 => IMAGE1:latest" ./{_script_name}""")
    sys.exit(exit_code)


def die(cause: str = "Something went wrong") -> NoReturn:
    """Panic out, logging the message in github action logs"""
    print(f"::error file={__file__}::{cause}")
    sys.exit(1)


def skopeo_retag(src_imgref: str, dst_imgref: str) -> bool:
    cmd_out = subprocess.run(
        executable="/usr/bin/skopeo",
        args=["copy", src_imgref, src_imgref],
        text=True,
    )

    return cmd_out.returncode == 0


summary_log = open(getenv("GITHUB_STEP_SUMMARY", "/dev/null"), "a")


def main():
    img_mappings: list[str] = getenv("TAG_MAPPINGS", "").lower().splitlines()

    # Strip comment lines
    img_mappings = list(map(lambda line: line.split("#")[0], img_mappings))

    # Strip lines from trailing spaces
    img_mappings = list(map(lambda line: line.strip(), img_mappings))

    # Filter out empty lines
    img_mappings = list(filter(lambda line: line != "", img_mappings))

    # Write header for github step log
    print("# Retagging summary", file=summary_log) if getenv("CI") is not None else None

    for src, dst in [
        (src.strip(), dst.strip()) for src, dst in [x.split("=>") for x in img_mappings]
    ]:
        src = getenv("PREFIX", "") + src
        dst = getenv("PREFIX", "") + dst
        if skopeo_retag(src, dst) and getenv("CI") is not None:
            print("```", file=summary_log)
            print(f"{src} => {dst}", file=summary_log)
            print("```", file=summary_log)


if __name__ == "__main__":
    # if "-h" or "--help" in sys.argv:
    #     _help()
    main()
    summary_log.close()
