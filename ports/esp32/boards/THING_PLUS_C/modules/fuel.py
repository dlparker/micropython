

"""
Added support for MAX17048
Dennis Parker
2022/04/08

original version:
max17043 library for MicroPython
this is a lipo battery cells fuel gauge made by maxim
https://datasheets.maximintegrated.com/en/ds/MAX17043-MAX17044.pdf
small module by sparkfun
https://www.sparkfun.com/products/10617
based upon the max17043 library for arduino by lucadentella
https://github.com/lucadentella/ArduinoLib_MAX17043

Andre Peeters
2017/10/31
"""

import machine
import binascii
import struct

class FuelGauge:

    REGISTER_VCELL = const(0X02)             # Read only 12 (or 16) bit voltage level
    REGISTER_SOC = const(0X04)               # Read only 16 bit state of charge
    REGISTER_MODE = const(0X06)              # Write to send special command
    REGISTER_VERSION = const(0X08)           # Read only Chip version
    REGISTER_COMMAND = const(0XFE)           # Write to send special command
    # all the following are for (MAX17048/49) only
    REGISTER_HIBERNATE = const(0x0A)         # Read/Write Thresholds for entering hibernate
    REGISTER_CONFIG = const(0X0C)            # Read/Write battery compensation (default 0x971C)
    REGISTER_CONF_VOLT_ALRT = const(0x14)    # Read/Write Voltage range for alert (default 0x00ff)
    REGISTER_CHANGE_RATE = const(0x16)       # Read charge/discharge rate / .208 (???, confirmed)
    REGISTER_VOLT_ID_RST = const(0x18)       # Read/Write reset voltage and ID
    REGISTER_STATUS = const(0x1A)            # Read/Write reset status
    
    def __init__(self, is_48=True):
        """
        """
        self.is_48 = is_48
        self.p_sda = machine.Pin(21)
        self.p_scl = machine.Pin(22)
        self.i2c = machine.I2C(1, sda=self.p_sda, scl=self.p_scl)
        self.max17043Address = None
        for addr in self.i2c.scan():
            if addr == 54:
                self.max17043Address = 54
        if self.max17043Address is None:
            raise Exception('did not find correct address on i2c')

    def __str__(self):
        """
        string representation of the values
        """
        rs  = "i2c address is {}\n".format( self.max17043Address )
        rs += "version is {}\n".format( self.getVersion() )
        rs += "vcell is {} v\n".format( self.getVCell() )
        rs += "soc is {} %\n".format( self.getSoc() )
        if self.is_48:
            rs += "change rate is {}% per hour\n".format( self.getChangeRate() )
        rs += "compensatevalue is {}\n".format( self.getCompensateValue() )
        rs += "alert threshold is {} %\n".format( self.getAlertThreshold() )
        rs += "in alert is {}".format( self.inAlert() )
        return rs

    def address(self):
        """
        return the i2c address
        """
        return self.max17043Address

    def reset(self):
        """
        reset
        """
        self.__writeRegister(REGISTER_COMMAND,binascii.unhexlify('0054'))

    def getVCell(self):
        """
        get the volts left in the cell
        """
        buf = self.__readRegister(REGISTER_VCELL)
        if (not self.is_48):
            return (buf[0] << 4 | buf[1] >> 4) /1000.0
        divider = 65536.0/5.2
        return (buf[0] << 8 | buf[1] ) / divider
        
    def getSoc(self):
        """
        get the state of charge
        """
        buf = self.__readRegister(REGISTER_SOC)
        return (buf[0] + (buf[1] / 256.0) )

    def getVersion(self):
        """
        get the version of the max17043 module
        """
        buf = self.__readRegister(REGISTER_VERSION)
        return (buf[0] << 8 ) | (buf[1])

    def getCompensateValue(self):
        """
        get the compensation value
        """
        return self.__readConfigRegister()[0]

    def getAlertThreshold(self):
        """
        get the alert level
        """
        return ( 32 - (self.__readConfigRegister()[1] & 0x1f) )

    def setAlertThreshold(self, threshold):
        """
        sets the alert level
        """
        self.threshold = 32 - threshold if threshold < 32 else 32
        buf = self.__readConfigRegister()
        buf[1] = (buf[1] & 0xE0) | self.threshold
        self.__writeConfigRegister(buf)

    def inAlert(self):
        """
        check if the the max17043 module is in alert
        """
        return (self.__readConfigRegister())[1] & 0x20

    def getChangeRate(self):
        """
        Get charge or discharge rate
        """
        buf = self.__readRegister(REGISTER_CHANGE_RATE)
        value = struct.unpack_from("!h", buf)[0]
        return float(value) * 0.208
        
    def clearAlert(self):
        """
        clears the alert
        """
        self.__readConfigRegister()

    def quickStart(self):
        """
        does a quick restart
        """
        self.__writeRegister(REGISTER_MODE,binascii.unhexlify('4000'))

    def __readRegister(self,address):
        """
        reads the register at address, always returns bytearray of 2 char
        """
        return self.i2c.readfrom_mem(self.max17043Address,address,2)

    def __readConfigRegister(self):
        """
        read the config register, always returns bytearray of 2 char
        """
        return self.__readRegister(REGISTER_CONFIG)

    def __writeRegister(self,address,buf):
        """
        write buf to the register address
        """
        self.i2c.writeto_mem(self.max17043Address,address,buf)

    def __writeConfigRegister(self,buf):
        """
        write buf to the config register
        """
        self.__writeRegister(REGISTER_CONFIG,buf)

    def deinit(self):
        """
        turn off the peripheral
        """
        self.i2c.deinit()
