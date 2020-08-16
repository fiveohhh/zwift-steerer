#!/usr/bin/env python3

import logging

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from ble import (
    Advertisement,
    Characteristic,
    Service,
    Application,
    find_adapter,
    Descriptor,
    Agent,
)

import struct
import array
from enum import Enum

import sys

MainLoop = None
try:
    from gi.repository import GLib

    MainLoop = GLib.MainLoop
except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)



mainloop = None

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.InvalidValueLength"


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.Failed"


def register_app_cb():
    logger.info("GATT application registered")


def register_app_error_cb(error):
    logger.critical("Failed to register application: " + str(error))
    mainloop.quit()


class SteererService(Service):
    """
    Custom service for Steerer
    """

    SVC_UUID = "347b0001-7635-408b-8918-8ff3949ce592"

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.SVC_UUID, True)
        self.add_characteristic(Unknown1Characteristic(bus, 0, self))
        self.add_characteristic(Unknown2Characteristic(bus, 1, self))
        self.add_characteristic(Unknown3Characteristic(bus, 2, self))
        self.add_characteristic(Unknown4Characteristic(bus, 3, self))
        self.add_characteristic(Unknown5Characteristic(bus, 4, self))
        self.add_characteristic(Unknown6Characteristic(bus, 5, self))
        self.add_characteristic(SteererCharacteristic(bus, 6, self))



class Unknown1Characteristic(Characteristic):
    uuid = "347b0012-7635-408b-8918-8ff3949ce592"
    description = b"Get/set machine power state {'ON', 'OFF', 'UNKNOWN'}"


    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["write"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))


    def WriteValue(self, value, options):
        logger.debug("Write to unknown1: " + repr(value))
        self.value = value

class Unknown2Characteristic(Characteristic):
    uuid = "347b0013-7635-408b-8918-8ff3949ce592"
    description = b"Unknown"


    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["read"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def ReadValue(self, options):
        logger.debug("Read from unknown2: " + repr(self.value))
        return self.value


class Unknown3Characteristic(Characteristic):
    uuid = "347b0014-7635-408b-8918-8ff3949ce592"
    description = b"Unknown"


    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["notify"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def StartNotify(self):
        logger.info("Enabling notifications unknown3")
        

    def StopNotify(self):
        logger.info("Disabling notifications unknown3")

class Unknown4Characteristic(Characteristic):
    uuid = "347b0019-7635-408b-8918-8ff3949ce592"
    description = b"Unknown"


    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["read"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def ReadValue(self, options):
        logger.debug("Unknown4 Read: " + repr(self.value))
        return self.value



class SteererCharacteristic(Characteristic):
    uuid = "347b0030-7635-408b-8918-8ff3949ce592"
    description = b"notifications for steering angle"


    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["notify"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def StartNotify(self):
        logger.info("Enabling notifications steerer")
        

    def StopNotify(self):
        logger.info("Disabling notifications steerer")

class Unknown5Characteristic(Characteristic):
    uuid = "347b0031-7635-408b-8918-8ff3949ce592"
    description = b"Handshaking thing?"
    # Zwift writes 0x0310 to here and that causes the Sterzo to emit an indication of
    # 0x0310xxxx on characteristic 0x0032 where xxxx is some random value
    # Zwift than writes 0x0311yyyy back to this characteristic
    # which than causes the Sterzo to emit 0x0311ff on characteristic 0x0032
    # The sterzo then starts emitting steering info on characteristic 0x0030
    # Zwift than writes 0x0202 to 0x0031 <- data has already started flowing at this point

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["write"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def WriteValue(self, value, options):
        logger.debug("Unknown 5 Write: " + repr(value))
        self.value = value
class Unknown6Characteristic(Characteristic):
    uuid = "347b0032-7635-408b-8918-8ff3949ce592"
    description = b"indicate other side of handshake"


    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["indicate"], service,
        )

        self.value = [0xFF]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def StartNotify(self):
        logger.info("Enabling indications unknown6")
        

    def StopNotify(self):
        logger.info("Disabling indications unknown6")




class CharacteristicUserDescriptionDescriptor(Descriptor):
    """
    Writable CUD descriptor.
    """

    CUD_UUID = "2901"

    def __init__(
        self, bus, index, characteristic,
    ):

        self.value = array.array("B", characteristic.description)
        self.value = self.value.tolist()
        Descriptor.__init__(self, bus, index, self.CUD_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value


class SteererAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_service_uuid(SteererService.SVC_UUID)

        self.add_local_name("Steerer")
        self.include_tx_power = True


def register_ad_cb():
    logger.info("Advertisement registered")


def register_ad_error_cb(error):
    logger.critical("Failed to register advertisement: " + str(error))
    mainloop.quit()



def main():
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    adapter = find_adapter(bus)

    if not adapter:
        logger.critical("GattManager1 interface not found")
        return

    adapter_obj = bus.get_object(BLUEZ_SERVICE_NAME, adapter)

    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")

    # powered property on the controller to on
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    # Get manager objs
    service_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)

    advertisement = SteererAdvertisement(bus, 0)
    obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")

   

    app = Application(bus)
    app.add_service(SteererService(bus, 2))

    mainloop = MainLoop()


    ad_manager.RegisterAdvertisement(
        advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

    logger.info("Registering GATT application...")

    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=[register_app_error_cb],
    )



    mainloop.run()
    # ad_manager.UnregisterAdvertisement(advertisement)
    # dbus.service.Object.remove_from_connection(advertisement)


if __name__ == "__main__":
    main()