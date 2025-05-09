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
    cmd = [
        "/usr/bin/skopeo",
        "copy",
        f"docker://{src_imgref}",
        f"docker://{dst_imgref}",
    ]

    print(" ".join(["Running command:", *cmd]))

    res = subprocess.run(cmd, text=True).returncode == 0

    return res


summary_log = open(getenv("GITHUB_STEP_SUMMARY", "/dev/null"), "a")


def img_iter(lines: list[str]) -> list[tuple[str, str]]:
    """
    Pass a list of lines, each line must follow the format 'src_img:src_tag => dst_img:dst_tag,dst_tag2,...'

    Return an iterator of tuple(src_img, dst_img)
    """
    pairs = [(src.strip(), dst.strip()) for src, dst in [x.split("=>") for x in lines]]

    res: list[tuple[str, str]] = []

    for src, dst in pairs:
        # Check if we have a list of tags (separated by commas)
        _dst_tag = dst.split(":", 1)[-1]
        if _dst_tag.count(",") > 0:
            # If so, iterate per each tag
            for dst in [
                f"{dst.split(':')[0]}:{tag}"
                for tag in map(str.strip, _dst_tag.split(","))
            ]:
                res.append(
                    (
                        (getenv("SRC_PREFIX") or getenv("PREFIX") or "").strip()
                        + src.strip(),
                        (getenv("DST_PREFIX") or getenv("PREFIX") or "").strip()
                        + dst.strip(),
                    )
                )

        else:
            # Otherwise, iterate normally
            del _dst_tag
            res.append(
                (
                    (getenv("SRC_PREFIX") or getenv("PREFIX") or "").strip()
                    + src.strip(),
                    (getenv("DST_PREFIX") or getenv("PREFIX") or "").strip()
                    + dst.strip(),
                )
            )

    return res


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

    # Retag and print to github log if we are in CI
    for src, dst in [(src.strip(), dst.strip()) for src, dst in img_iter(img_mappings)]:
        if all((src, dst)):
            if not skopeo_retag(src, dst):
                raise RuntimeError(f"Error while retaging '{src}' to '{dst}'")

            if getenv("CI") is not None:
                print("```", file=summary_log)
                print(f"{src} => {dst}", file=summary_log)
                print("```", file=summary_log)


if __name__ == "__main__":
    # if "-h" or "--help" in sys.argv:
    #     _help()
    main()
    summary_log.close()
