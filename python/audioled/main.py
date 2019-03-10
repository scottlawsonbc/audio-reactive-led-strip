import os
import argparse

from multiprocessing import Process, Pipe

import dotenv


parser = argparse.ArgumentParser()
parser.add_argument('--source', '-s', required=True, nargs='+')
parser.add_argument('--effect', '-e', required=True, nargs='+')
parser.add_argument('--output', '-o', required=True, nargs='+')
parser.add_argument('--venv', '-v', required=False, nargs=1)


if __name__ == '__main__':
    args, unknown = parser.parse_known_args()
    # Load environment variables.
    if args.venv:
        dotenv.load_dotenv(dotenv_path=args.venv[0])
    # Interpret unknown args as environment variables to be set.
    assert len(unknown) % 2 == 0
    for i in range(0, len(unknown), 2):
        key, val = unknown[i], unknown[i+1]
        os.environ[key] = val
    # Import only after environment variables have been set.
    import source
    import effect
    import device
    # Components.
    src = getattr(source, args.source[0])
    pre = effect.preprocess
    vis = getattr(effect, args.effect[0])
    out = getattr(device, args.output[0])
    # Communication channels.
    src_send, src_recv = Pipe()
    pre_send, pre_recv = Pipe()
    vis_send, vis_recv = Pipe()
    # Pipeline.
    pipeline = [
        (src, (src_send, (*args.source[1:]))),
        (pre, (src_recv, pre_send)),
        (vis, (pre_recv, vis_send, *args.effect[1:])),
        (out, (vis_recv, *args.output[1:])),
    ]

    processes = [Process(target=t, args=a) for t, a in pipeline]

    try:
        for p in processes:
            p.start()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()



    # # Broadcast.
    # for target, args in pipeline:
    #     Process(target=target, args=args).start()
