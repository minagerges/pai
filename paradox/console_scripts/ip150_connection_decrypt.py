#!/usr/bin/env python3
import argparse
import binascii
from collections import OrderedDict

import yaml

from paradox.connections.ip.parsers import IPMessageRequest, IPMessageResponse
from paradox.lib.crypto import decrypt


def ordered_load(stream, Loader=yaml.loader.SafeLoader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )
    return yaml.load(stream, OrderedLoader)


def decrypt_file(file, password):
    PASSWORD2 = None
    try:
        data = ordered_load(file, yaml.loader.SafeLoader)

        n = 0
        for key, value in data.items():
            header = value[0:16]
            body = value[16:]

            if "peer0_" in key:
                parsed = IPMessageRequest.parse(value)
            else:
                parsed = IPMessageResponse.parse(value)

            if parsed.header.flags.encrypt:
                body = decrypt(body, password if n < 2 else PASSWORD2)
            if n < 2 and "peer1_" in key:
                PASSWORD2 = body[1:17]
                print(len(PASSWORD2))

            print(
                "PC->IP: " if "peer0_" in key else "IP->PC: ",
                binascii.hexlify(header),
                binascii.hexlify(body),
                body,
            )

            if "peer0_" in key:
                print(IPMessageRequest.parse(value))
            else:
                print(IPMessageResponse.parse(value))

            if "peer1_" in key:
                print(
                    "----end %s-------------------------------------------------------------"
                    % key
                )
            n += 1

    except yaml.YAMLError as exc:
        print(exc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=argparse.FileType("r"),
        help="YAML file to parse. In wireshark right click on the first "
        "package, 'Follow->TCP Stream', 'Show and save data as': "
        "'YAML', copy contents to a file.",
    )
    parser.add_argument("password", type=str, help="IP Module password for decryption")

    args = parser.parse_args()

    decrypt_file(args.file, args.password.encode("utf8"))


if __name__ == "__main__":
    main()
