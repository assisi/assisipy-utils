import argparse

def default_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logpath', type=str, required=True,
                        help="path to record output in")
    parser.add_argument('-bn', '--bee-name', type=str, default='BEE',
                        help="name of the bee to attach to")
    parser.add_argument('-pa', '--pub-addr', type=str, default='tcp://127.0.0.1:5556',
                        help="publish address (wherever the enki server listens for commands)")
    parser.add_argument('-sa', '--sub-addr', type=str, default='tcp://127.0.0.1:5555',
                        help="subscribe address (wherever the enki server emits commands)")
    parser.add_argument('-c', '--conf-file', type=str, default=None)
    parser.add_argument('-v', '--verb', action='store_true', help="be verbose")

    return parser

