#!/usr/bin/env python3
"""
Convert a Minecraft .schematic (gzipped NBT) file to JSON.

Usage:
    python schematic_to_json.py input.schematic [output.json]

If output is omitted, it will use the same name with .json extension.
"""

import argparse
import gzip
import json
import pathlib
import struct
import sys

# NBT tag type constants
TAG_End        = 0
TAG_Byte       = 1
TAG_Short      = 2
TAG_Int        = 3
TAG_Long       = 4
TAG_Float      = 5
TAG_Double     = 6
TAG_Byte_Array = 7
TAG_String     = 8
TAG_List       = 9
TAG_Compound   = 10
TAG_Int_Array  = 11
TAG_Long_Array = 12


# --- Low-level helpers -------------------------------------------------------

def _read_exact(f, n):
    data = f.read(n)
    if len(data) != n:
        raise EOFError("Unexpected end of NBT data")
    return data


def _read_byte(f):
    b = _read_exact(f, 1)
    return b[0]


def _read_short(f):
    return struct.unpack(">h", _read_exact(f, 2))[0]


def _read_ushort(f):
    return struct.unpack(">H", _read_exact(f, 2))[0]


def _read_int(f):
    return struct.unpack(">i", _read_exact(f, 4))[0]


def _read_long(f):
    return struct.unpack(">q", _read_exact(f, 8))[0]


def _read_float(f):
    return struct.unpack(">f", _read_exact(f, 4))[0]


def _read_double(f):
    return struct.unpack(">d", _read_exact(f, 8))[0]


def _read_string(f):
    length = _read_ushort(f)
    if length == 0:
        return ""
    return _read_exact(f, length).decode("utf-8")


# --- NBT tag reading ---------------------------------------------------------

def _read_tag_payload(f, tag_type):
    """Read the payload for a tag of the given type (no name included)."""
    if tag_type == TAG_End:
        return None

    if tag_type == TAG_Byte:
        return struct.unpack(">b", _read_exact(f, 1))[0]

    if tag_type == TAG_Short:
        return _read_short(f)

    if tag_type == TAG_Int:
        return _read_int(f)

    if tag_type == TAG_Long:
        return _read_long(f)

    if tag_type == TAG_Float:
        return _read_float(f)

    if tag_type == TAG_Double:
        return _read_double(f)

    if tag_type == TAG_Byte_Array:
        length = _read_int(f)
        # JSON can't store raw bytes, so we convert to list of integers (0–255)
        return list(_read_exact(f, length))

    if tag_type == TAG_String:
        return _read_string(f)

    if tag_type == TAG_List:
        child_type = _read_byte(f)
        length = _read_int(f)
        return [_read_tag_payload(f, child_type) for _ in range(length)]

    if tag_type == TAG_Compound:
        obj = {}
        while True:
            t = _read_byte(f)
            if t == TAG_End:
                break
            name = _read_string(f)
            payload = _read_tag_payload(f, t)
            obj[name] = payload
        return obj

    if tag_type == TAG_Int_Array:
        length = _read_int(f)
        return [_read_int(f) for _ in range(length)]

    if tag_type == TAG_Long_Array:
        length = _read_int(f)
        return [_read_long(f) for _ in range(length)]

    raise ValueError("Unknown NBT tag type: {}".format(tag_type))


def _read_named_tag(f):
    """
    Read a single named NBT tag.
    Returns: (name, payload, tag_type)
    """
    tag_type = _read_byte(f)
    if tag_type == TAG_End:
        return None, None, TAG_End
    name = _read_string(f)
    payload = _read_tag_payload(f, tag_type)
    return name, payload, tag_type


def read_nbt_from_gzipped_file(path):
    """
    Read the root NBT tag from a gzipped NBT file (like .schematic).
    Returns a tuple (root_name, root_payload).
    """
    with gzip.open(path, "rb") as f:
        name, payload, tag_type = _read_named_tag(f)
        if tag_type != TAG_Compound:
            raise ValueError("Root tag is not a Compound (got {})".format(tag_type))
        return name, payload


# --- CLI ---------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert Minecraft .schematic (gzipped NBT) file to JSON."
    )
    parser.add_argument("input", help=".schematic file path")
    parser.add_argument(
        "output",
        nargs="?",
        help="Output JSON file path (defaults to same name with .json extension)",
    )
    args = parser.parse_args(argv)

    in_path = pathlib.Path(args.input)
    if args.output:
        out_path = pathlib.Path(args.output)
    else:
        out_path = in_path.with_suffix(".json")

    if not in_path.is_file():
        print("Input file does not exist: {}".format(in_path), file=sys.stderr)
        return 1

    try:
        root_name, root_payload = read_nbt_from_gzipped_file(in_path)
    except Exception as e:
        print("Failed to read NBT from {}: {}".format(in_path, e), file=sys.stderr)
        return 1

    # Keep the root name (usually "Schematic") for clarity:
    json_obj = {root_name: root_payload}

    # If you prefer the bare payload, you could instead do:
    # json_obj = root_payload

    try:
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=2)
            f.flush()  # Ensure data is written to OS buffer
            os.fsync(f.fileno())  # Force write to disk
    except Exception as e:
        print(f"Error writing JSON to {out_path}: {e}")
        raise

    print("Wrote JSON to {}".format(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
