#!/usr/bin/env python
# coding: utf-8

import json
import argparse
from pathlib import Path

import toml
from langdetect import detect

from krawl.licenses import getlicenseblacklists, getlicenses
from krawl.wf import make_version

FORBIDDEN = -1


def makerepo(dct):
    # TODO
    # > It's not possible to query a canonical URL from the API right now.
    # >
    # >
    # >
    # > These are the formats for:
    # >
    # > - Profiles: @slug
    # >
    # > - Organization: +slug
    # >
    # > - Project: parentSlug/slug
    # >
    # >
    # >
    # > parentSlug is a profile or organization slug. It can be queried as a field of Project.
    # >
    # prefixes = {
    #     "Project": "@",
    #     "Content": "+",
    # }
    # typename = dct["space"]["content"]["__typename"]
    # if typename not in prefixes.keys():
    #     print("[WF][MakeRepo] ", typename, " not found in repo prefix matcher")
    # prefix = prefixes.get(typename, "@")
    # stem = dct["space"]["content"]["slug"]
    prefix = ""
    try:
        stem = dct["creatorProfile"]["username"]
        leaf = dct["slug"]
        return f"https://wikifactory.com/{prefix}{stem}/{leaf}"
    except KeyError:
        print("couldt get creator profile:")
        print(dct)
        return ""


def get_license(dct):
    valid = getlicenses()
    lcns = dct.get("license", {})
    if lcns is None:
        return "N/A"
    lcns = lcns.get("abreviation", "na")
    if lcns not in valid:
        print("[WF/LicenseMatching] ", lcns, " is not valid spdx")
        return "BAD"
    blacklist = getlicenseblacklists()
    if lcns in blacklist:
        print("[WF/LicenseMatching] ", lcns, " is forbidden, will drop")
        return FORBIDDEN
    return lcns


def getfunction(dct):
    desc = dct.get("description", "").replace("<p>", "").replace("</p>", "\n").strip()
    if desc == "":
        return None
    return desc


def getlang(dct):
    desc = dct.get("description", "")
    if desc == "":
        return None
    if len(desc.split(" ")) <= 2:
        return "en"
    lang = detect(desc)
    return lang


def getfiles(dct):
    files = []
    if dct.get("contributionUpstream") is None:
        return None
    for file in dct.get("contributionUpstream", {}).get("files", []):
        inner = file.get("file")
        if inner is None:
            print("will skip, no file")
            continue
        if inner.get("permalink") is None:
            print("will skip, no permalink")
            continue
        files.append(
            {
                "name": f"{file['dirname']}/{file['filename']}",
                "permalink": inner["permalink"],
                "mimetype": inner["mimeType"],
            }
        )
    return files


def getimage(dct):
    if dct.get("image") is None:
        return None
    return dct.get("image").get("permalink", None)


def getreadme(dct):
    if dct.get("contributionUpstream") is None:
        return None
    # return (
    #     dct.get("contributionUpstream", {})
    #     .get("contribFile", {})
    #     .get("file", {})
    #     .get("permalink")
    # )
    return None


def convert(dct):
    return {
        "name": dct.get("name"),
        "repo": makerepo(dct),
        "version": make_version(dct),
        "spdx-license": get_license(dct),
        "licensor": dct.get("creatorProfile", {}).get("fullName"),
        "readme": getreadme(dct),
        "documentation-language": getlang(dct),
        "image": getimage(dct),
        "function": getfunction(dct),
        "files": getfiles(dct),
    }


# - =? okhv = "2.0"
# - name = "OHLOOM"
# - repo = "https://gitlab.com/OSEGermany/ohloom"
# - version = "0.10.0"
# ? release = "https://gitlab.com/OSEGermany/ohloom/-/tags/ohloom-0.10.0"
# - spdx-license = "CC-BY-SA-4.0"
# - licensor = "Jens Meisner"
# - readme = "README.md"
# - image = "/Documentation/User_Guide/User_Guide.jpg"
# - documentation-language = "en"
# ? open-technology-readiness-level = "OTLR-5"
# - function = "The Open Hardware Loom is a simple, hand-operated weaving loom made of wood, screws and 3D printed plastic pieces for the most part. It is simple to make and operate."
# ? cpc-patent-class = "D03D 35/00"
# ? tsdc-id = "ASM-MEC"
# ? bom = "sBoM.csv"
# ? manufacturing-instructions = "/Documentation/Assembly_Guide/AssemblyGuide.md"
# ?user-manual = "/Documentation/User_Guide/UserGuide.md"
# ?outer-dimension-dim = "mm"
# ?outer-dimension = "cube(size = [400,350,150]"
# ?risk-assessment = "risky"
# ?[functional-metadata]
# fabric-width-dim = "mm"
# fabric-width = 400

if __name__ == "__main__":
    # argv = sysconf.argv[1:]
    # args = argparser.parse_args(argv)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "files", metavar="files", help="filepaths to process", nargs="+"
    )
    args = parser.parse_args()
    print("Starting WF convert")
    print(args.files)
    for arg_file in args.files:
        file_path = Path(arg_file)
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        normalized = convert(data)
        print("[WF] Converting: ", str(file_path))
        with (file_path.parent / "normalized.toml").open("wb") as toml_file:
            toml_file.write(toml.dumps(normalized).encode("utf8"))
        print("[WF] sucess! - ", str(file_path))

        # with open("../samples/wf/recordforbidden.json", "r") as f:
        #     data = json.load(f)
        #     normalized = convert(data)
        #     print(normalized)
        #     print(toml.dumps(normalized))
