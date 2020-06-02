
import serial
import time
import libscrc
import pyrebase
from pandas import DataFrame
from time import sleep
config = {
  "apiKey": "AIzaSyCV-zR0q7iJue1bPyk8OzJHu4H5iFqy-38",
  "authDomain": "ibfns-fcdf3.firebaseapp.com",
  "databaseURL": "https://ibfns-fcdf3.firebaseio.com",
  "storageBucket": "ibfns-fcdf3.appspot.com"
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()
DeviceAddress="0"
DeviceType="0"
AlarmStatus="0"
AlarmThreshold="0"
Temperature="0"
Smoke="0"
def CalculateCRC (Packet):
    ModbusData =bytearray([0x00,0x00,0x00,0x00,0x00,0x00])
    ModbusData[0]=Packet[2]
    ModbusData[1]=Packet[3]
    ModbusData[2]=Packet[4]
    ModbusData[3]=Packet[5]
    ModbusData[4]=Packet[6]
    ModbusData[5]=Packet[7]
    crc16 = libscrc.modbus(ModbusData)
    CRC1=(crc16>>8)&0x00FF
    CRC2=(crc16)&0x00FF
    if Packet[8]==CRC1 and Packet[9]==CRC2:
        return True
    else:
        return False
port =serial.Serial(
    "/dev/ttyUSB0",
    baudrate=19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    writeTimeout = 0,
    timeout = 0.05,
    rtscts=False,
    dsrdtr=False,
    xonxoff=False)
UniqueID="12345"
port.close()
port.open()
print(port.isOpen())
print("Port opened...")
while True:
    db.child(UniqueID).child("SystemSettings").child("SystemCheck").set("Connected")
    DatabaseSettings = db.child(UniqueID).child("SystemSettings").get()
    Data=DatabaseSettings.val()
    if Data['SystemReset']=='Reset':
        db.child(UniqueID).child("SystemSettings").child("SystemReset").set("Default")
        now=time.strftime("%H:%M:%S %d.%m.%y")
        db.child(UniqueID).child("SystemSettings").child("TimeReset").set(now)
        cmdReset = bytearray([0x00])
        cmdReset[0] = 0x55
        port.write(cmdReset)
    Database = db.child(UniqueID).child("Devices").get()
    Data=Database.val()
    data_frame = DataFrame(Data[1:])
    for x in range(127):
        DatabaseDevices = data_frame.iloc[x]
        if DatabaseDevices.Connection == "Not Connected" or DatabaseDevices.Connection == "Connected" or DatabaseDevices.Connection == "Disconnected":
            cmdDetectorAddress = bytearray([0x00])
            cmdDetectorAddress[0] = x+1
            port.write(cmdDetectorAddress)
            ModbusPacket=port.read(10)
            if len(ModbusPacket) == 10:
                Address=ModbusPacket[0]
                Function=ModbusPacket[1]
                RxDeviceAddress=ModbusPacket[2]
            else:
                Address=0
                Function=0
                now=time.strftime("%H:%M:%S %d.%m.%y")
                db.child(UniqueID).child("Devices").child(DatabaseDevices.DeviceAddress).child("TimeConnection").set(now)
                db.child(UniqueID).child("Devices").child(DatabaseDevices.DeviceAddress).child("Connection").set("Disconnected")
            if Address == 0x03 and Function == 0x04:
                if CalculateCRC(ModbusPacket)== True:
                    DeviceAddress=(ModbusPacket[2])
                    DeviceType=str(ModbusPacket[3])
                    AlarmStatus=str(ModbusPacket[4])
                    AlarmThreshold=str(ModbusPacket[5])
                    Temperature=str(ModbusPacket[6])
                    Smoke=str(ModbusPacket[7])
                    print("CRC True")
                    print("CRC True")
                    db.child(UniqueID).child("Devices").child(DeviceAddress).child("Connection").set("Connected")
                    now=time.strftime("%H:%M:%S %d.%m.%y")
                    db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeConnection").set(now)
                    if DeviceType == "1":
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("Temperature").set(Temperature)
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("AlarmThreshold").set(AlarmThreshold)
                        if AlarmStatus=="10":
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Heat Alarm")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                        elif AlarmStatus=="11":
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Default")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                    elif DeviceType=="2":
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("Smoke").set(Smoke)
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("AlarmThreshold").set(AlarmThreshold)
                        if AlarmStatus=="10":
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Smoke Alarm")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                        elif AlarmStatus=="11":
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Default")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                    elif DeviceType=="3":
                        if AlarmStatus=="10":
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Button Alarm")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                        elif AlarmStatus=="11":
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Default")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)

