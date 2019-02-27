import argparse
import config
import microphone
import led
import visualization

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--ip', help='IP address', required=True)
  parser.add_argument('-p', '--port', help='UDP port', default=7777, type=int)
  parser.add_argument('-n', '--num-leds', help='Number of LEDs', required=True, type=int)
  parser.add_argument('-f', '--fps', dest='fps', default=60, type=int)
  parser.add_argument('-d', '--display_fps', dest='display_fps', action='store_true')
  parser.set_defaults(display_fps=False)
  args = parser.parse_args()
  
  config.UDP_IP = args.ip
  config.UDP_PORT = args.port
  config.N_PIXELS = args.num_leds
  config.USE_GUI = False
  config.DISPLAY_FPS = args.display_fps
  config.FPS = args.fps

  # Initialize LEDs
  led.update()
  # Start listening to live audio stream
  microphone.start_stream(visualization.microphone_update)

if __name__ == '__main__':
  main()

