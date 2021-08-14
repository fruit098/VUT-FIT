#Author: Andrej Zaujec

import argparse
import dpkt
import os
import json

from ja3 import process_ja3, process_ja3s

keywords = {
    "instagram": [
        "instagram",
        "graph.facebook",
        "cdninstagram",
    ],
    "tiktok": [
        "tiktokcdn",
        "tiktokv" , "tiktok",
    ],
    "messenger": ["web.facebook", "fbcdn"],
    "gmail": [
        "googleusercontent",
        "googleapis",
        "mail.google",
        "inbox.google",
        "www.google",
    ],
    "blockfolio": [
        "api.blockfolio",
        "blockfolio",
        "cointelegraph",
        "coindesk",
        "cryptobriefing",
    ],
    "netflix": [
        "netflix",
        "nflxso",
        "nflxvideo",
    ],
    "binance": ["binance", "bnbstatic", "hanqiweb", "shyqxxy", "riskified"],
    "twitter": [
        "twitter",
        "twimg",
    ],
    "medium": [
        "medium",
    ],
    "kaloricketabulky": [
        "kaloricketabulky",
    ],
}


def main():
    """Intake arguments from the user and print out JA3 output."""
    desc = "A python script for extracting JA3 fingerprints from PCAP files"
    parser = argparse.ArgumentParser(description=(desc))
    parser.add_argument("pcap", help="The pcap file to process")
    parser.add_argument("output", help="The output csv file")

    help_text = "Look for client hellos on any port instead of just 443"
    parser.add_argument(
        "-a",
        "--any_port",
        required=False,
        action="store_true",
        default=False,
        help=help_text,
    )
    help_text = "Parse test set"
    parser.add_argument(
        "-t",
        "--test_set",
        required=False,
        action="store_true",
        default=False,
        help=help_text,
    )
    help_text = "Print packet related data for research (json only)"
    args = parser.parse_args()

    # Use an iterator to process each line of the file
    output = None
    with open(args.pcap, "rb") as fp:
        try:
            capture = dpkt.pcap.Reader(fp)
        except ValueError as e_pcap:
            try:
                fp.seek(0, os.SEEK_SET)
                capture = dpkt.pcapng.Reader(fp)
            except ValueError as e_pcapng:
                raise Exception(
                    "File doesn't appear to be a PCAP or PCAPng: %s, %s"
                    % (e_pcap, e_pcapng)
                )
        res_ja3 = process_ja3(capture, any_port=args.any_port)
        try:
            fp.seek(0, os.SEEK_SET)
            capture = dpkt.pcap.Reader(fp)
        except ValueError as e_pcap:
            try:
                fp.seek(0, os.SEEK_SET)
                capture = dpkt.pcapng.Reader(fp)
            except ValueError as e_pcapng:
                raise Exception(
                    "File doesn't appear to be a PCAP or PCAPng: %s, %s"
                    % (e_pcap, e_pcapng)
                )

        res_ja3s = process_ja3s(capture, any_port=args.any_port)

    count = 0
    output = []
    for ja3 in res_ja3:
        matching_ja3s = filter(
            lambda x: x["source_ip"] == ja3["destination_ip"]
            and x["source_port"] == ja3["destination_port"]
            and x["destination_ip"] == ja3["source_ip"]
            and x["destination_port"] == ja3["source_port"],
            res_ja3s,
        )
        match_list = list(matching_ja3s)
        match_len = len(match_list)
        if match_len == 1:
            output.append({"ja3": ja3, "ja3s": match_list[0]})
            count += 1
        if match_len > 1:
            output.append({"ja3": ja3, "ja3s": match_list[0]})
            res_ja3s.remove(match_list[0])

    print("fingerprints count: ", count)
    app_name = None
    if not args.test_set:
        app_name = os.path.basename(args.pcap).split(".")[0]
        print("App name is: ", app_name)

    save_to_db(output, app_name, args.output, test_set=args.test_set)

def save_to_db(output, app_name, db_file, test_set=False):
    from pathlib import Path
    import csv

    fieldnames = ["ja3", "ja3s", "sni", "app_name"]
    if os.path.exists(db_file):
        read_f = open(db_file)
        reader = csv.DictReader(read_f)
    else:
        reader = []
    rows = []
    for entry in output:
        row = {
            "ja3": entry["ja3"]["ja3_digest"],
            "sni": entry["ja3"]["sni"],
            "ja3s": entry["ja3s"]["ja3_digest"],
            "app_name": app_name,
        }
        if ("apple" in row["sni"]) or ("icloud" in row["sni"]):
            row["app_name"] = "apple"

        same_entries = list(
            filter(
                lambda x: x["ja3"] == row["ja3"]
                and x["ja3s"] == row["ja3s"]
                and x["sni"] == row["sni"],
                reader,
            )
        )
        if isinstance(reader, csv.DictReader):
            read_f.seek(0)

        if same_entries:
            continue

        sni = row["sni"]
        test_app_name = None
        for app, keywords_to_check in keywords.items():
            if list(filter(lambda keyword: keyword in sni, keywords_to_check)):
                test_app_name = app
                break
        if not test_app_name:
            continue  # unknown traffic

        if test_set: # we are assinging app name
            row["app_name"] = test_app_name

        if row in rows:
            continue
        rows.append(row)

    with open(db_file, mode="a") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
