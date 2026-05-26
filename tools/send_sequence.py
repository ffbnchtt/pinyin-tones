from pynput.keyboard import Controller, Key
import time
k = Controller()
print('Sleeping 1s')
time.sleep(1)
print('Toggling app')
# send Ctrl+Shift+P
k.press(Key.ctrl)
k.press(Key.shift)
k.press('p')
k.release('p')
k.release(Key.shift)
k.release(Key.ctrl)
time.sleep(0.5)
print('Typing ni3')
k.type('ni3')
print('Done')
