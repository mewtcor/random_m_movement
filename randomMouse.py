#!/usr/bin/env python

from time import sleep
import pyautogui
import numpy as np

# Check your screen size
print(pyautogui.size())

count=0
while count<1000:
    x=np.random.randint(1,1792)
    y=np.random.randint(1,1120)
    pyautogui.moveTo(x, y)
    print(x)
    print(y)
    sleep(20)
    count+=1