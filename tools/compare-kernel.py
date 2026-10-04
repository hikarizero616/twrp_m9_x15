#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Compare the prebuilt kernel blob shipped in this device tree with the kernel
# section of a stock boot/recovery image (the one dumped from the device).
#
# Why: prebuilt/kernel is NOT a bare arm64 Image. It is
#      "gzip(Image) + appended DTB" (MTK's Image.gz-dtb export).
#      Verify that the stock image uses the exact same blob before flashing.
#
# Usage:
#   python3 tools/compare-kernel.py boot.img
#   python3 tools/compare-kernel.py recovery.img
#   python3 tools/compare-kernel.py --prebuilt prebuilt/kernel boot.img
#   python3 tools/compare-kernel.py --extract stock-kernel.bin boot.img
#
# Requires only the Python 3 standard library.

import argparse
import hashlib
import os
import struct
import sys
import zlib

BOOT_MAGIC = b"ANDROID!"
FDT_MAGIC = b"\xd0\x0d\xfe\xed"
GZIP_MAGIC = b"\x1f\x8b"
MTK_HEADER_MAGIC = bytes.fromhex("88168858")
HEADER_V0_SIZE = 1632  # 8 + 10*4 + 16 + 512 + 32 + 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def align(value, page):
    return (value + page - 1) // page * page


def parse_boot_image(data):
    """Return (kernel_blob, info dict) for an Android boot/recovery image."""
    if data[:8] != BOOT_MAGIC:
        raise ValueError("not an Android boot image (missing ANDROID! magic)")

    (kernel_size, kernel_addr, ramdisk_size, ramdisk_addr,
     second_size, second_addr, tags_addr, page_size,
     header_version, os_version) = struct.unpack_from("<10I", data, 8)

    if page_size == 0 or page_size > 65536:
        raise ValueError("implausible page size %d" % page_size)

    # v0 header layout: magic(8) + 10*u32(40) + name(16) + cmdline(512) + id(32)
    #                  + extra_cmdline(1024) = 1632 bytes
    name = data[48:64].split(b"\x00")[0].decode("utf-8", "replace")
    cmdline_parts = [data[64:576].split(b"\x00")[0], data[608:1632].split(b"\x00")[0]]
    cmdline = b" ".join(p for p in cmdline_parts if p).decode("utf-8", "replace")

    # dt_size lives right after the v0 header (union field in boot_img_hdr_v1)
    dt_size = 0
    if len(data) >= HEADER_V0_SIZE + 4:
        dt_size = struct.unpack_from("<I", data, HEADER_V0_SIZE)[0]
        if dt_size > len(data):
            dt_size = 0

    kernel_off = align(HEADER_V0_SIZE, page_size)
    # Some older images put the first section at page_size, not at the
    # page-aligned header size; they coincide for 2048-byte pages.
    if kernel_off < page_size:
        kernel_off = page_size

    kernel = data[kernel_off:kernel_off + kernel_size]
    if len(kernel) != kernel_size:
        raise ValueError("truncated image: kernel section shorter than declared")

    info = {
        "page_size": page_size,
        "kernel_size": kernel_size,
        "kernel_addr": kernel_addr,
        "ramdisk_size": ramdisk_size,
        "ramdisk_addr": ramdisk_addr,
        "second_size": second_size,
        "tags_addr": tags_addr,
        "dt_size": dt_size,
        "header_version": header_version,
        "os_version": os_version,
        "name": name,
        "cmdline": cmdline,
    }
    return kernel, info


def split_appended_dtb(payload):
    """Split '... FDT ...' into (image, dtb). The FDT total_size must match."""
    pos = payload.rfind(FDT_MAGIC)
    while pos > 0:
        if pos + 8 <= len(payload):
            total = int.from_bytes(payload[pos + 4:pos + 8], "big")
            if total == len(payload) - pos:
                return payload[:pos], payload[pos:]
        pos = payload.rfind(FDT_MAGIC, 0, pos)
    return payload, None


def strip_mtk_header(blob):
    """MTK often prepends a 512-byte header before the actual kernel."""
    if blob[:4] == MTK_HEADER_MAGIC:
        return blob[512:], True
    # plain "KERNEL" text header, also 512 bytes
    if blob[:6] == b"KERNEL" and len(blob) > 512:
        return blob[512:], True
    return blob, False


def describe(blob):
    """Normalize a kernel blob into a comparable dict."""
    out = {}
    blob, out["mtk_header"] = strip_mtk_header(blob)
    out["raw_size"] = len(blob)

    payload = blob
    trailing = b""
    out["gzip"] = blob[:2] == GZIP_MAGIC
    if out["gzip"]:
        d = zlib.decompressobj(31)
        try:
            payload = d.decompress(blob)
        except zlib.error as exc:
            out["error"] = "gzip payload corrupt: %s" % exc
            return out
        # Bytes after the gzip stream: usually an appended DTB on MTK devices.
        trailing = d.unused_data

    if trailing:
        if trailing[:4] == FDT_MAGIC:
            image, dtb = payload, trailing
        else:
            image, extra = split_appended_dtb(payload)
            dtb = extra or trailing
            if extra is None:
                image = payload
    else:
        image, dtb = split_appended_dtb(payload)
    out["image"] = image
    out["image_size"] = len(image)
    out["dtb"] = dtb
    out["dtb_size"] = len(dtb) if dtb else 0
    out["arm64_image"] = image[0x38:0x3c] == b"ARMd"
    out["image_sha256"] = sha256(image)
    out["dtb_sha256"] = sha256(dtb) if dtb else None
    out["blob_sha256"] = sha256(blob)

    idx = image.find(b"Linux version ")
    out["version"] = (image[idx:idx + 120].split(b"\x00")[0].decode("utf-8", "replace")
                      if idx >= 0 else None)
    return out


def print_summary(label, d):
    print("== %s ==" % label)
    print("  size            : %d bytes" % d["raw_size"])
    print("  container       : %s%s" % ("gzip" if d.get("gzip") else "raw",
                                        " + MTK 512B header" if d.get("mtk_header") else ""))
    print("  kernel Image    : %d bytes%s" % (d.get("image_size", 0),
                                              "  (arm64 'ARMd')" if d.get("arm64_image") else ""))
    print("  appended DTB    : %d bytes%s" % (d.get("dtb_size", 0),
                                              "" if d.get("dtb") else "  (none)"))
    print("  linux version   : %s" % (d.get("version") or "(not found)"))
    print("  sha256(Image)   : %s" % d.get("image_sha256"))
    print("  sha256(DTB)     : %s" % d.get("dtb_sha256"))
    print("  sha256(whole)   : %s" % d.get("blob_sha256"))
    if d.get("error"):
        print("  ERROR           : %s" % d["error"])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", help="stock boot/recovery image(s) to inspect")
    ap.add_argument("--prebuilt", default=None,
                    help="prebuilt kernel blob (default: prebuilt/kernel next to this tree)")
    ap.add_argument("--extract", default=None,
                    help="write the kernel section of the last given image to this file")
    args = ap.parse_args()

    if args.prebuilt is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args.prebuilt = os.path.join(root, "prebuilt", "kernel")

    with open(args.prebuilt, "rb") as fh:
        prebuilt_raw = fh.read()
    prebuilt = describe(prebuilt_raw)
    print("[device tree] %s" % args.prebuilt)
    print_summary("prebuilt/kernel", prebuilt)
    print()

    overall = 0
    for path in args.images:
        with open(path, "rb") as fh:
            data = fh.read()
        print("[stock image] %s" % path)
        try:
            kernel, info = parse_boot_image(data)
        except ValueError as exc:
            print("  could not parse: %s" % exc)
            overall = 1
            print()
            continue

        print("  page_size       : %d" % info["page_size"])
        print("  os_version      : 0x%08x" % info["os_version"])
        print("  product name    : %s" % (info["name"] or "(none)"))
        print("  cmdline         : %s" % (info["cmdline"] or "(none)"))
        print("  header dt_size  : %d" % info["dt_size"])
        print()

        stock = describe(kernel)
        print_summary("kernel section", stock)
        print()

        if stock["blob_sha256"] == prebuilt["blob_sha256"]:
            print("  VERDICT: IDENTICAL - the prebuilt blob matches the stock kernel exactly.")
        else:
            print("  VERDICT: DIFFERENT")
            print("    raw sha256 equal          : %s" % (sha256(kernel) == sha256(prebuilt_raw)))
            print("    gzip container equal      : %s" % (stock.get("gzip") == prebuilt.get("gzip")))
            print("    kernel Image payload equal: %s" % (stock.get("image_sha256") == prebuilt.get("image_sha256")))
            print("    appended DTB equal        : %s" % (stock.get("dtb_sha256") == prebuilt.get("dtb_sha256")))
            if stock.get("image_sha256") == prebuilt.get("image_sha256"):
                print("    -> same kernel, only the container/DTB differs (usually repacked).")
            else:
                print("    -> the kernel binary itself differs; do not assume it boots.")
            print("    If you intend to flash the prebuilt: diff the linux version above and")
            print("    prefer the blob that came out of this device's own image.")
            overall = 1
        print()

        if args.extract:
            with open(args.extract, "wb") as fh:
                fh.write(kernel)
            print("  wrote kernel section to %s (%d bytes)" % (args.extract, len(kernel)))
            print()

    return overall


if __name__ == "__main__":
    sys.exit(main())
