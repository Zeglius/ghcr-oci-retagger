#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.*"
# dependencies = []
# ///

import subprocess
import sys
from os import getenv
from typing import NamedTuple, NoReturn, Self, Set


class RetagMappingEntry(NamedTuple):
    src: str
    dst: str

    def __str__(self) -> str:
        return f"{self.src} => {self.dst}"

    @classmethod
    def from_mapping(cls, mapping: str) -> list[Self]:
        res: list[Self] = []
        lines = mapping.lower().splitlines()

        # Remove comments
        lines = list(map(lambda line: line.split("#")[0].strip(), lines))
        # Filter out empty lines
        lines = list(filter(None, lines))

        res = sum([cls.from_line(x) for x in lines], [])
        return res

    @classmethod
    def from_line(cls, line: str) -> list[Self]:
        mapping: Set[RetagMappingEntry] = set()

        _p = line.split("=>")
        src, dst = (_p[0].strip(), _p[1].strip())
        del _p

        def add_to_mapping(src: str, dst: str):
            mapping.add(
                RetagMappingEntry(
                    (getenv("SRC_PREFIX") or getenv("PREFIX") or "").strip()
                    + src.strip(),
                    (getenv("DST_PREFIX") or getenv("PREFIX") or "").strip()
                    + dst.strip(),
                )
            )

        # Check if we have a sha digest in dst, if so, error out
        if "@sha" in dst:
            raise RuntimeError("destination tag must not be a sha digest")

        # Iterate across tags in dst (separated by commas)
        dst_name = dst.split(":", 1)[0]
        dst_tags = [x.strip() for x in dst.split(":", 1)[1].split(",")]
        for dst in [f"{dst_name}:{x}" for x in dst_tags]:
            add_to_mapping(src, dst)

        return [cls(src, dst) for src, dst in mapping]


def is_dry() -> bool:
    return getenv("DRY_RUN") == "1" or getenv("CI") != "true"


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

    print(" ".join(["Running command:", *cmd]), flush=True)

    res = is_dry() or subprocess.run(cmd, text=True).returncode == 0

    return res


summary_log = open(getenv("GITHUB_STEP_SUMMARY", "/dev/null"), "a")


def main():
    img_mappings = RetagMappingEntry.from_mapping(getenv("TAG_MAPPINGS", ""))

    if len(img_mappings) < 1:
        raise RuntimeError("Not even a single entry could be parsed from TAG_MAPPINGS")

    # Write header for github step log
    print("# Retagging summary", file=summary_log)

    # Retag and print to github log if we are in CI
    for src, dst in img_mappings:
        if not all((src, dst)):
            die(f"src and dst are empty: src='{src}' dst='{dst}'")

        if not skopeo_retag(src, dst):
            die(f"Error while retaging '{src}' to '{dst}'")

        print("```", file=summary_log)
        print(f"{src} => {dst}", file=summary_log)
        print("```", file=summary_log)


if __name__ == "__main__":
    # if "-h" or "--help" in sys.argv:
    #     _help()
    main()
    summary_log.close()
