from math import ceil
import serial
#from busio import UART

class ArduinoConnectionError(Exception):
    pass

class Arduino(object):
    '''
    Acknowledgement schema should be: [len(data),data[0],"\n"]
    '''
    def __init__(self, port, baud_rate, timeout=2):
        self.error_count = 0
        self.max_msg_len = 8
        try:
            self.serial_cxn = serial.Serial(port, baud_rate, timeout=timeout)
            #self.serial_cxn = UART(tx, rx, baudrate=baud_rate, timeout=timeout)
        except Exception as e:
            print(e)
            raise ArduinoConnectionError()

    def write_data(self, data):
        num_msgs = ceil(len(data) / self.max_msg_len)
        i = 0; j = min(len(data), self.max_msg_len)
        print('Data: ', [x for x in data])
        for msg_num in range(num_msgs):
            msg_data = data[i:j]
            print(f'Sending message {msg_num} / {num_msgs}. msg: {msg_data}')
            self.serial_cxn.write(msg_data)
            i += self.max_msg_len # Move i down by max msg len
            j = min(j + self.max_msg_len, len(data)) # Move j down by max msg len or to last value
            # Wait for ack
            ack = self.serial_cxn.read(3)
            print(f'Ack: {ack}')
            if not ack:
                print('Error. No ack received')
            elif ack[0] != len(msg_data) or ack[1] != msg_data[0]: # Check ack
                print(f'Error with ack. expected num bytes: {len(msg_data)}, ack num bytes: {ack[0]}, ' + \
                        f'expected first msg byte: {msg_data[0]}, ack first msg byte: {ack[1]}')
                self.error_count += 1
