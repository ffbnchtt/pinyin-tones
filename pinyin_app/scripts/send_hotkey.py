from pynput.keyboard import Controller, Key
import time

if __name__ == '__main__':
    time.sleep(1)
    k = Controller()
    print('Sending Ctrl+Shift+P')
    k.press(Key.ctrl)
    k.press(Key.shift)
    k.press('p')
    k.release('p')
    k.release(Key.shift)
    k.release(Key.ctrl)
    print('Sent')
