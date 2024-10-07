# Imports from the python standard library:
import ctypes as C
import os

class Driver:
    '''
    Basic device adaptor for Thorlabs DC40, LED driver, 4A/14V max.
    Many more commands are available and have not been implemented.
    '''
    def __init__(self,
                 port_number,   # which COM port number?
                 mode="CW",     # "CW", "TTL" or "MOD"
                 name='DC40',
                 verbose=True,
                 very_verbose=False):
        self.name = name
        self.verbose = verbose
        self.very_verbose = very_verbose
        if self.verbose: print("%s: opening..."%self.name)
        resourceName = ("ASRL" + port_number + "::INSTR").encode('ascii')
        self.handle = C.c_uint32()
        dll.init(resourceName, 1, 0, self.handle) # IDQuery, resetDevice = 0, 0
        if self.verbose: print("%s: open and ready."%self.name)
        # get basic info:
        self._get_led_info()
        self._get_current_min()
        self._get_current_max()
        self.get_power()
        self.set_enable(False)
        self.set_mode(mode)

    def _get_led_info(self):
        if self.very_verbose:
            print("%s: getting led info:"%self.name)
        led_info = [(256 * C.c_char)(), (256 * C.c_char)(),
                    C.c_double(), C.c_double(), C.c_double()]
        dll.get_led_info(self.handle, *led_info)
        for i, info in enumerate(led_info):
            if i < 2:
                led_info[i] = info.value.decode('ascii')
            else:
                led_info[i] = info.value
        if self.very_verbose:
            print("%s:  - name            = %s"%(self.name, led_info[0]))
            print("%s:  - serial number   = %s"%(self.name, led_info[1]))
            print("%s:  - current limit   = %s"%(self.name, led_info[2]))
            print("%s:  - forward voltage = %s"%(self.name, led_info[3]))
            print("%s:  - wavelength      = %s"%(self.name, led_info[4]))
        self.led_info = tuple(led_info)
        self.led_current_limit = self.led_info[2]
        return self.led_info

    def _get_current_min(self):
        if self.very_verbose:
            print("%s: getting current min"%self.name)
        current = C.c_double()
        dll.get_current_setpoint(self.handle, 1, current)
        self.current_min_a = current.value
        if self.very_verbose:
            print("%s:  = %s (A)"%(self.name, self.current_min_a))
        return self.current_min_a

    def _get_current_max(self):
        if self.very_verbose:
            print("%s: getting current max"%self.name)
        current = C.c_double()
        dll.get_current_setpoint(self.handle, 2, current)
        self.current_max_a = current.value
        if self.very_verbose:
            print("%s:  = %s (A)"%(self.name, self.current_max_a))
        return self.current_max_a

    def _get_current_setpoint(self):
        if self.very_verbose:
            print("%s: getting current setpoint"%self.name)
        current = C.c_double()
        dll.get_current_setpoint(self.handle, 0, current)
        self.current_setpoint_a = current.value
        if self.very_verbose:
            print("%s:  = %s (A)"%(self.name, self.current_setpoint_a))
        return self.current_setpoint_a

    def _set_current_setpoint(self, current_setpoint_a):
        if self.very_verbose:
            print("%s: setting current setpoint = %s"%(
                self.name, current_setpoint_a))
        assert (isinstance(current_setpoint_a, int)
                or isinstance(current_setpoint_a, float)), (
                    "%s: unexpected type for current_setpoint_a"%self.name)
        current_setpoint_a = round(current_setpoint_a, 4) # limit 4 d.p
        min_a , max_a = self.current_min_a, self.current_max_a
        assert min_a <= current_setpoint_a <= max_a, (
            "%s: current_setpoint_a (%s) out of range"%(
                self.name, current_setpoint_a))
        dll.set_current_setpoint(self.handle, current_setpoint_a)
        assert self._get_current_setpoint() == current_setpoint_a
        if self.very_verbose:
            print("%s: -> done setting current setpoint."%self.name)
        return None

    def get_mode(self):
        if self.verbose:
            print("%s: getting mode"%self.name)
        mode = C.c_uint32()
        dll.get_mode(self.handle, mode)
        number_to_mode = {0:"CW", 1:"TTL", 2:"MOD"}
        self.mode = number_to_mode[mode.value]
        if self.verbose:
            print("%s:  = %s"%(self.name, self.mode))
        return self.mode

    def set_mode(self, mode):
        if self.verbose:
            print("%s: setting mode = %s"%(self.name, mode))
        mode_to_number = {"CW":0, "TTL":1, "MOD":2}
        assert mode in mode_to_number, (
            "%s: unexpected mode (%s)"%(self.name, mode))
        dll.set_mode(self.handle, mode_to_number[mode])
        assert self.get_mode() == mode
        if self.verbose:
            print("%s: -> done setting mode."%self.name)
        return None

    def get_power(self):
        if self.verbose:
            print("%s: getting power"%self.name)
        current = self._get_current_setpoint()
        self.power_pct = round(100 * current / self.current_max_a, 2) # 2 d.p
        if self.verbose:
            print("%s:  = %s (%%)"%(self.name, self.power_pct))
        return self.power_pct

    def set_power(self, power_pct):
        if self.verbose:
            print("%s: setting power = %s (%%)"%(self.name, power_pct))
        assert (isinstance(power_pct, int) or isinstance(power_pct, float)), (
                    "%s: unexpected type for power_pct"%self.name)
        assert 1 <= power_pct <= 100, (
            "%s: power_pct (%s) out of range"%(self.name, power_pct))
        power_pct = round(power_pct, 2) # 2 d.p
        current_setpoint_a = (power_pct * self.current_max_a) / 100
        if current_setpoint_a < self.current_min_a:
            current_setpoint_a = self.current_min_a
        self._set_current_setpoint(current_setpoint_a)
        assert self.get_power() == power_pct
        if self.verbose:
            print("%s: -> done setting power."%self.name)
        return None

    def get_enable(self):
        if self.verbose:
            print("%s: getting enable"%self.name)
        enable = C.c_bool()
        dll.get_enable(self.handle, enable)
        self.enable = enable.value
        if self.verbose:
            print("%s:  = %s"%(self.name, self.enable))
        return self.enable

    def set_enable(self, enable):
        if self.verbose:
            print("%s: setting enable = %s"%(self.name, enable))
        assert isinstance(enable, bool)
        dll.set_enable(self.handle, enable)
        assert self.get_enable() == enable
        if self.verbose:
            print("%s: -> done setting enable."%self.name)
        return None

    def close(self):
        if self.verbose: print("%s: closing..."%self.name, end='')
        dll.close(self.handle)
        if self.verbose: print(" done.")
        return None

### Tidy and store DLL calls away from main program:

os.add_dll_directory(os.getcwd())
dll = C.cdll.LoadLibrary("TLDC_64.dll") # needs "TLDC_64.dll" in directory

## -> function 'tlccs_errorMessage' not found:

dll.get_error_message = dll.TLDC_errorMessage
dll.get_error_message.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.c_uint32,                 # statusCode
    C.c_char_p]                 # description[]
dll.get_error_message.restype = C.c_uint32

def check_error(error_code):
    if error_code != 0:
        print("Error message from Thorlabs DC40: ", end='')
        error_message = (512 * C.c_char)()
        dll.get_error_message(0, error_code, error_message)
        print(error_message.value.decode('ascii'))
        raise UserWarning(
            "Thorlabs DC40 error: %i; see above for details."%(error_code))
    return error_code

dll.init = dll.TLDC_init
dll.init.argtypes = [
    C.c_char_p,                 # resourceName
    C.c_bool,                   # IDQuery
    C.c_bool,                   # resetDevice
    C.POINTER(C.c_uint32)]      # instrumentHandle
dll.init.restype = check_error

dll.get_led_info = dll.TLDC_getLedInfo
dll.get_led_info.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.c_char_p,                 # _VI_FAR ledName[]
    C.c_char_p,                 # _VI_FAR ledSerialNumber[]
    C.POINTER(C.c_double),      # ledCurrentLimit
    C.POINTER(C.c_double),      # ledForwardVoltage
    C.POINTER(C.c_double)]      # ledWavelength
dll.get_led_info.restype = check_error

dll.get_current_setpoint = dll.TLDC_getLedCurrentSetpoint
dll.get_current_setpoint.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.c_int16,                  # Attribute
    C.POINTER(C.c_double)]      # LEDCurrentSetpoint
dll.get_current_setpoint.restype = check_error

dll.set_current_setpoint = dll.TLDC_setLedCurrentSetpoint
dll.set_current_setpoint.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.c_double]                 # LEDCurrentSetpoint
dll.set_current_setpoint.restype = check_error

dll.get_mode = dll.TLDC_getLedMode
dll.get_mode.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.POINTER(C.c_uint32)]      # pLEDMode
dll.get_mode.restype = check_error

dll.set_mode = dll.TLDC_setLedMode
dll.set_mode.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.c_uint32]                 # LEDMode
dll.set_mode.restype = check_error

dll.get_enable = dll.TLDC_getLedOutputState
dll.get_enable.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.POINTER(C.c_bool)]        # ledOutput
dll.get_enable.restype = check_error

dll.set_enable = dll.TLDC_switchLedOutput
dll.set_enable.argtypes = [
    C.c_uint32,                 # instrumentHandle
    C.c_bool]                   # ledOutput
dll.set_enable.restype = check_error

dll.close = dll.TLDC_close
dll.close.argtypes = [
    C.c_uint32]                 # instrumentHandle
dll.close.restype = check_error

if __name__ == '__main__':
    import numpy as np
    led = Driver(port_number="14", mode="CW", verbose=True, very_verbose=False)

    print('\n# Basic operation:')
    led.set_power(1)
    led.set_enable(True)
    led.set_enable(False)

##    print('\n# TTL operation:')
##    led.set_power(1)
##    led.set_mode("TTL")
##    # -> apply TTL to the BNC to toggle the LED on/off
##
##    print('\n# Analogue in operation:')
##    led.set_mode("MOD")
##    # -> apply 0-5V analogue in to the BNC for 0-4A current output!

    led.close()
