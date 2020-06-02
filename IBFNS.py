#Libraries
import serial
import time
import libscrc
import pyrebase
from pandas import DataFrame
from time import sleep
#Libraries
#Database Configuration
config = {
  "apiKey": "AIzaSyCV-zR0q7iJue1bPyk8OzJHu4H5iFqy-38",
  "authDomain": "ibfns-fcdf3.firebaseapp.com",
  "databaseURL": "https://ibfns-fcdf3.firebaseio.com",
  "storageBucket": "ibfns-fcdf3.appspot.com"
}
#Database Configuration
#Database Initialize
firebase = pyrebase.initialize_app(config)
db = firebase.database()
#Database Initialize
#Detector Status Variables
DeviceAddress="0"
DeviceType="0"
AlarmStatus="0"
AlarmThreshold="0"
Temperature="0"
Smoke="0"
#Detector Status Variables
#Detector Types
HeatDetector="1"
SmokeDetector="2"
Button="3"
#Detector Types
#Alarm Status
Alarm="10"
NoAlarm="11"
#Alarm Status
#CRC Calculation Function
def CalculateCRC (Packet):
    ModbusData =bytearray([0x00,0x00,0x00,0x00,0x00,0x00])
    #Read Received Modbus Packet
    ModbusData[0]=Packet[2]
    ModbusData[1]=Packet[3]
    ModbusData[2]=Packet[4]
    ModbusData[3]=Packet[5]
    ModbusData[4]=Packet[6]
    ModbusData[5]=Packet[7]
    #Read Received Modbus Packet
    crc16 = libscrc.modbus(ModbusData)
    CRC1=(crc16>>8)&0x00FF
    CRC2=(crc16)&0x00FF
    if Packet[8]==CRC1 and Packet[9]==CRC2:
        return True
    else:
        return False
#CRC Calculation Function
#SerialPort Configuarion
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
#SerialPort Configuarion
#UniqueID Setup
UniqueID="12345"
#UniqueID Setup
#Open Serial Port
port.close()
port.open()
print(port.isOpen())
print("Port opened...")
#Open Serial Port
while True:
    #Write Connection Status to Database
    db.child(UniqueID).child("SystemSettings").child("SystemCheck").set("Connected")
    #Write Connection Status to Database
    #Read System Settings from Database
    DatabaseSettings = db.child(UniqueID).child("SystemSettings").get()
    Data=DatabaseSettings.val()
    #Read System Settings from Database
    #Check Reset Command
    if Data['SystemReset']=='Reset':
        #System Reset received set default system reset status.
        db.child(UniqueID).child("SystemSettings").child("SystemReset").set("Default")
        now=time.strftime("%H:%M:%S %d.%m.%y")
        db.child(UniqueID).child("SystemSettings").child("TimeReset").set(now)
        cmdReset = bytearray([0x00])
        cmdReset[0] = 0x55
        #Send Reset to Detectors
        port.write(cmdReset)
    #Check Reset Command
    #Read 127 Detector status from Database
    Database = db.child(UniqueID).child("Devices").get()
    Data=Database.val()
    #Read 127 Detector status from Database
    #Organize Received Data Format
    data_frame = DataFrame(Data[1:])
    #Organize Received Data Format
    #Introgate 127 Detector
    for x in range(127):
        DatabaseDevices = data_frame.iloc[x]
        #Check Connected, Disconnected and Not connected(Newly added devices) Devices
        if DatabaseDevices.Connection == "Not Connected" or DatabaseDevices.Connection == "Connected" or DatabaseDevices.Connection == "Disconnected":
            #Request Detector Status
            cmdDetectorAddress = bytearray([0x00])
            cmdDetectorAddress[0] = x+1
            port.write(cmdDetectorAddress)
            #Request Detector Status
            #Request Read From serial port
            ModbusPacket=port.read(10)
            #Request Read From serial port
            if len(ModbusPacket) == 10:
                Address=ModbusPacket[0]
                Function=ModbusPacket[1]
                #Accept Data
                RxDeviceAddress=ModbusPacket[2]
            else:
                Address=0
                Function=0
                #Faulty Data Received
                now=time.strftime("%H:%M:%S %d.%m.%y")
                db.child(UniqueID).child("Devices").child(DatabaseDevices.DeviceAddress).child("TimeConnection").set(now)
                db.child(UniqueID).child("Devices").child(DatabaseDevices.DeviceAddress).child("Connection").set("Disconnected")
            if Address == 0x03 and Function == 0x04:
                #Check CRC
                if CalculateCRC(ModbusPacket)== True:
                    #Convert Data to String
                    DeviceAddress=(ModbusPacket[2])
                    DeviceType=str(ModbusPacket[3])
                    AlarmStatus=str(ModbusPacket[4])
                    AlarmThreshold=str(ModbusPacket[5])
                    Temperature=str(ModbusPacket[6])
                    Smoke=str(ModbusPacket[7])
                    #Write CRC result and Device Address
                    print("Device Address" + DeviceAddress + "CRC True")
                    #Change Connection Status
                    if DatabaseDevices.Connection != "Connected":
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("Connection").set("Connected")
                        now=time.strftime("%H:%M:%S %d.%m.%y")
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeConnection").set(now)
                    #if it is Heat Detector Write Heat values to database
                    if DeviceType == HeatDetector:
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("Temperature").set(Temperature)
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("AlarmThreshold").set(AlarmThreshold)
                        if AlarmStatus==Alarm:
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Heat Alarm")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                        elif AlarmStatus==NoAlarm:
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Default")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                    #if it is Smoke Detector Write Smoke values to database
                    elif DeviceType==SmokeDetector:
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("Smoke").set(Smoke)
                        db.child(UniqueID).child("Devices").child(DeviceAddress).child("AlarmThreshold").set(AlarmThreshold)
                        if AlarmStatus==Alarm:
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Smoke Alarm")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                        elif AlarmStatus==NoAlarm:
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Default")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                    #if it is Button Device Write Button values to database
                    elif DeviceType==Button:
                        if AlarmStatus==Alarm:
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Button Alarm")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
                        elif AlarmStatus==NoAlarm:
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("Status").set("Default")
                            now=time.strftime("%H:%M:%S %d.%m.%y")
                            db.child(UniqueID).child("Devices").child(DeviceAddress).child("TimeStatus").set(now)
        #Check Connected, Disconnected and Not connected(Newly added devices) Devices
    #Introgate 127 Detector
