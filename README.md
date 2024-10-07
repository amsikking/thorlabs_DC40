# thorlabs_DC40
Python device adaptor: Thorlabs DC40, LED driver, 4A/14V max.
## Quick start:
- Install the 'Thorlabs DC40' GUI (from Thorlabs) and check the LED driver. It should be 
straightforward to run the GUI and control the LED (GUI version 1.0.0 used here).
- The GUI should install the device drivers and include a copy of the essential "TLDC_64.dll" file (a version included here for convenience).
- For Python control, download and run "thorlabs_DC40.py" with a copy of the .dll file in the same folder.

![social_preview](https://github.com/amsikking/thorlabs_DC40/blob/main/social_preview.png)

## Details:
- This adaptor was generated with reference to the "TLDC.h" header file that was installed by the GUI at location:
  - C:\Program Files\IVI Foundation\VISA\Win64\Include
- The essential "TLDC_64.dll" file was found here:
  - C:\Program Files\IVI Foundation\VISA\Win64\Bin
- Finding the critical "resourceName" string was tricky and done with a combination of finding the device in NI MAX, Windows Device Manager and with reference to the Python "PyVISA" docs.
- The "VISA data types" were translated to Python "ctypes" by searching those "key" words.
