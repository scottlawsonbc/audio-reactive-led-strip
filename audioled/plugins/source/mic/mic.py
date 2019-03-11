import sys
import argparse

import pyaudio


parser = argparse.ArgumentParser(description='Stream audio from input source.')
parser.add_argument('--info', action='store_true', help='List audio devices.')
parser.add_argument('--index', type=int, default=None, help='Audio device index.')
parser.add_argument('--rate', type=int, default=None, help='Sampling rate (Hz)')
parser.add_argument('--chunk', type=int, default=2048, help='Audio buffer size.')


def main():
    p = pyaudio.PyAudio()
    args = parser.parse_args()

    # List available audio input devices.
    if args.info:
        info_fn = p.get_device_info_by_index
        info_list = [info_fn(n) for n in range(p.get_device_count())]
        print(info_list)
        info_list = [i for i in info_list if i['maxInputChannels'] > 0]
        print('index\tmaxInputChannels\tdefaultSampleRate\tname')
        for info in info_list:
            print(('{index}\t{maxInputChannels:<16}\t'
                   '{defaultSampleRate:<17}\t{name}').format(**info))
    # Stream audio input.
    else:
        try:
            if args.index:
                info = p.get_device_info_by_index(args.index)
            else:
                info = p.get_default_input_device_info()
        except IOError as e:
            if args.index:
                parser.error('no audio input device matches the given index')
            else:
                parser.error('no default system audio input is available.')
            parser.exit()

        rate = args.rate or int(info['defaultSampleRate'])
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=rate,
                        input_device_index=args.index,
                        frames_per_buffer=args.chunk,
                        input=True)
        # First four bytes of stream must be int32 framerate value.
        sys.stdout.buffer.write(rate.to_bytes(4, byteorder='big'))
        # Write audio chunks.
        chunk = stream.read(args.chunk)
        while len(chunk):
            sys.stdout.buffer.write(chunk)
            chunk = stream.read(args.chunk)
        stream.close()

    p.terminate()


if __name__ == '__main__':
    main()
