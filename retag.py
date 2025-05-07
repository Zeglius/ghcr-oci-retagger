#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.*"
# dependencies = []
# ///

import os
import subprocess
import sys
from typing import NoReturn


def _help(exit_code: int = 0) -> NoReturn:
    """Print usage of script and exit"""
    print(
        f"""Usage:
            image_refs="IMAGE1:latest IMAGE1:latest" final_tags="latest stable" ./{__file__.split("/")[-1]}"""
    )
    sys.exit(exit_code)


def die(cause: str = "Something went wrong") -> NoReturn:
    """Panic out, logging the message in github action logs"""
    print(f"::error file={__file__}::{cause}")
    sys.exit(1)


type error = str | None


def skopeo_retag(src_imgref: str, dst_imgref: str) -> bool:
    cmd_out = subprocess.run(
        executable="/usr/bin/skopeo",
        args=["copy", src_imgref, src_imgref],
        text=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.STDOUT,
    )

    return cmd_out.returncode == 0


def main():
    # Set named parameters
    imgs_to_retag: list[str] = os.getenv("image_refs", "").split(" ")
    final_tags: list[str] = os.getenv("final_tags", "").split(" ")

    # Check params
    if imgs_to_retag == []:
        die("'image_refs' env var cant be empty")
    elif final_tags == []:
        die("'final_tags' env var cant be empty")

    # For each tag in final_tags, append input_ref but with the tag to final_refs
    for _img_ref in imgs_to_retag:
        for _tag in final_tags:
            # Check tag
            if "@" in _tag:
                die(f"Invalid tag: '@' in '{_tag}'")
            elif ":" in _tag:
                die(f"Invalid tag: ':' in '{_tag}'")

            # Strip any existing tags
            _img: str = _img_ref
            _img = _img.split("@sha256:")[0]
            _img = _img.split(":")[0]
            _finalref = f"{_img}:{_tag}"

            # Check if _ref is valid
            if len([c for c in _finalref if c == ":"]) != 1:
                die(f"Invalid ref: must not contain more than one ':' : '{_finalref}'")

            # Retag image with skopeo
            skopeo_retag(_img_ref, _finalref)


if __name__ == "__main__":
    argv = sys.argv

    if "--help" or "-h" in argv:
        _help()
    main()
