# -*- coding: utf-8 -*-
"""
Created on Sun Jan 20 23:05:15 2019

@author: Juan Posada
"""

from enum import Enum
import serial
import time
import datetime
import threading
import queue as queue

ser = serial.Serial(
    port = 'COM4',
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout=1 # add this
    )

fifo_queue = queue.Queue(0)
semaforo = threading.Semaphore(1)
semaforo2 = threading.Semaphore(1)

def SendSerial():
    
    global f_recibidoencoded
    
    global frecibido
    
    global intlista
    
    size = 2
    
    #semaforo2.acquire()
    
    ser.write(fifo_queue.get())
    
    #semaforo2.release()
       
    time.sleep(0.1)    

    n = ser.inWaiting()

    recibido = ser.read(n)
    
    print(recibido)
    
#    frecibido = recibido.hex()
#
#    f_recibidoencoded = [frecibido[i:i+size] for i in range(0, len(frecibido), size)]
#
#    ':'.join(f_recibidoencoded)
 
#    if(f_recibidoencoded[0] == '06'):
#    
#        print("ACK")
#        
#    elif(f_recibidoencoded[0] == '51'):
#    
#        print("CSFAIL")
#        
#    return (f_recibidoencoded[0])
    
    #print(frecibido)
    #print(f_recibidoencoded)
    
    #intlista.clear()
    
    return recibido


class Registers(int , Enum):

    Reg_System_Status = 0x02
 
##Measurement Registers    
    Reg_Voltage_RMS = 0x06
    Reg_Line_Frecuency = 0x08
    Reg_Thermistor_Voltage = 0x0A
    Reg_Power_Factor = 0x0C
    Reg_Current_RMS = 0x0E
    Reg_Active_Power = 0x12
    Reg_Reactive_Power = 0x16
    Reg_Appareant_Power = 0x1A
    Reg_Minimum_Record_One = 0x3E
    Reg_Minimum_Record_Two = 0x42
    Reg_Maximum_Record_Two = 0x46
    Reg_Maxinum_Record_Two = 0x4A
    
##Energy Counters Registers
    Reg_Import_Active = 0x1E
    Reg_Export_Active = 0x26
    Reg_Import_Reactive = 0x2E
    Reg_Export_Reactive = 0x36
    
##Design Configuration Registers
    
    Reg_System_Configuration = 0x94
    Reg_Event_Configuration = 0x98
    Reg_Range = 0x9C
    Reg_Calibration_Current = 0xA0
    Reg_Calibration_Voltage = 0xA4
    Reg_Calibration_Power_Active = 0xA6
    Reg_Calibration_Power_Reactive = 0xAA
    
    Reg_App_Power_Divisors_Digits = 0xBE
    Reg_Accumulation_Inverval_Parameter = 0xC0
    Reg_Min_Max_Pointer_One = 0xC6
    Reg_Min_Max_Pointer_Two = 0xC8
    Reg_Line_Frequency_Reference = 0xCA
    Reg_Thermistor_Voltage_Calibration = 0xCC
    
    Reg_Voltage_Sag_Limit = 0xCE
    Reg_Voltage_Surge_Limit = 0xD0
    Reg_OverCurrent_Limit = 0xD2
    Reg_OverPower_Limit = 0xD6
    Reg_OverTemperature_Limit = 0xDA
    Reg_Voltage_Low_Threshold = 0xDC
    Reg_Voltage_High_Threshold = 0xDE
    
class Commands(int, Enum):

    Command_Reg_Read = 0x4E
    Command_Reg_Write = 0x4D
    Command_Set_Pointer = 0x41
    Command_Save_Flash = 0x53
    Command_Page_Read_EEPROM = 0x42
    Command_Page_Write_EEPROM = 0x50
    Command_Bulk_Erase_EEPROM = 0x4F
    Command_Auto_Calibrate_Gain = 0x5A
    Command_Auto_Calibrate_Reactive_Gain = 0x5A
    Command_Auto_Calibrate_Frequency = 0x76
    Command_Save_Energy_Counters = 0x45
    
class FixedCommandsFrame():
    
    def __init__(self):
        
        self.SaveToFlash = [0xA5 , 0x04, Commands.Command_Save_Flash, 0xFC]
        self.SaveEnergyCounters = [0xA5 , 0x04, Commands.Command_Save_Energy_Counters , 0xEE]
        self.AutoCalGain = [0xA5 , 0x04, Commands.Command_Auto_Calibrate_Gain, 0x03]
        self.AutoCalReactGain = [0xA5 , 0x04 , Commands.Command_Auto_Calibrate_Reactive_Gain , 0x23]
        self.AutoCalFrequency = [0xA5 , 0x04 , Commands.Command_Auto_Calibrate_Frequency , 0x1F ]
        self.BulkEraseEEPROM =  [0xA4 , 0x04 , Commands.Command_Bulk_Erase_EEPROM , 0xF8]
                
class Values():
    
    def __init__(self, VoltageRMS = None , Frequency = None , Temperature = None,
                 PowerFactor = None , Current = None, ActivePower = None , ReactivePower = None, AppareantPower = None ):
        
        self.VoltageRMS = VoltageRMS
        self.Frequency = Frequency
        self.Temperature = Temperature
        self.PowerFactor = PowerFactor
        self.CurrentRMS = Current
        self.ActivePower = ActivePower
        self.ReactivePower = ReactivePower
        self.AppareantPower = AppareantPower
              
class CalibrationValues():
    
    def __init__(self, VoltageCal = None , CurrentCal = None , PowerActCal = None , LineFreqRef = None , ThermistorVoltage = None):
        
        self.VoltageCal = VoltageCal
        self.CurrentCal = CurrentCal
        self.PowerActCal = PowerActCal
        self.LineFreqRef = LineFreqRef
        self.ThermistorVoltage = ThermistorVoltage
        
class EnergyCounters():
    
    def __init__(self, ImportActivePowerCounter = None , ImportReactivePowerCounter = None , ExportActivePowerCounter = None , ExportReactivePowerCounter = None):
        
         self.ImportActivePowerCounter =  ImportActivePowerCounter
         self.ImportReactivePowerCounter = ImportReactivePowerCounter
         self.ExportActivePowerCounter = ExportActivePowerCounter
         self.ExportReactivePowerCounter = ExportReactivePowerCounter
                 
class EventsLimits():
    
    def __init__(self, VSag = None , VSurge = None , OverCurrent = None , OverPower = None , OverTemp = None):
        
         self.VSag = VSag
         self.VSurge = VSurge
         self.OverCurrent = OverCurrent
         self.OverPower = OverPower
         self.OverTemp = OverTemp
        
class EventsFlags():
    
    def __init__(self,NoEventFlag = None, VSagFlag = None , VSurgeFlag = None, OverCurrentFlag = None, OverPowerFlag = None):
              
         self.NoEventFlag = NoEventFlag
         self.VSagFlag = VSagFlag
         self.VSurgeFlag = VSurgeFlag
         self.OverCurrentFlag = OverCurrentFlag
         self.OverPowerFlag = OverPowerFlag
                
##-----------------------------------Methods-------------------------------------------##
         
def ReadFrame(Addr_Low, NoB):
        
        global fifo_queue
    
        HeaderByte = 0xA5
        NoBF = 0x08
        CommandPointer = 0x41
        Addr_High = 0x00
        Addr_Low = Addr_Low
        Command = 0x4E
        NoB = NoB
        Checksum = None
        Buffer = []
        
        Readframe = [HeaderByte , NoBF, CommandPointer, Addr_High, Addr_Low, Command , NoB]
  
        Checksum = sum(Readframe) % 256
        
        Readframe.append(Checksum)
        
        fifo_queue.put(Readframe)
         
        semaforo.acquire()
        
        Receive =  SendSerial()
                          
        Buffer.extend( Receive ) 
        
        semaforo.release()
        
        time.sleep(0.2)
        
        #print(Receive)
        
        #Buffer.extend( SendSerial(Readframe) ) 

        #print(Buffer)
        
        return Buffer

def WriteFrame(Addr_Low, Data, NoB):
       
        HeaderByte = 0xA5
        CommandPointer = 0x41
        Addr_High = 0x00
        Addr_Low = Addr_Low
        Command = Commands.Command_Reg_Write
        NoB = NoB
        NoBF = NoB + 8
        Data = Data
        
        WriteFrame = [HeaderByte , NoBF, CommandPointer, Addr_High, Addr_Low, Command , NoB]
           
        WriteFrame.extend(Data)
                    
        WriteFrame.append( sum(WriteFrame) % 256)
        
        #print (WriteFrame)
        
        #SendSerial(WriteFrame)
        
        fifo_queue.put(WriteFrame)
        
        SendSerial()
   
        return WriteFrame
    
def SaveToFlash():
    
   FixedCommand = FixedCommandsFrame()
   SendSerial( FixedCommand.SaveToFlash )
   
def SaveEnergyCounters():

   FixedCommand = FixedCommandsFrame()
   SendSerial( FixedCommand.SaveEnergyCounters )
     
def AutoCalibrationGain():
    
   FixedCommand = FixedCommandsFrame()
   SendSerial( FixedCommand.AutoCalGain )
        
def AutoCalibrationReactive():
    
   FixedCommand = FixedCommandsFrame()
   SendSerial( FixedCommand.AutoCalReactGain ) 
   
def SetCalibrationValues(VoltageCal, CurrentCal, PowerActCal):
    
    CalibrationValArray = []
    
    CalibrationValArray.append( CurrentCal & 0xFF )
    CalibrationValArray.append( ( CurrentCal >> 8) & 0xFF )
    CalibrationValArray.append( ( CurrentCal >> 16) & 0xFF )
    CalibrationValArray.append( ( CurrentCal >> 24) & 0xFF )   
     
    CalibrationValArray.append( VoltageCal & 0xFF )
    CalibrationValArray.append( ( VoltageCal >> 8) & 0xFF )
     
    CalibrationValArray.append( PowerActCal & 0xFF)
    CalibrationValArray.append( (PowerActCal >> 8) & 0xFF)
    CalibrationValArray.append( (PowerActCal >> 16) & 0xFF) 
    CalibrationValArray.append( (PowerActCal >> 24) & 0xFF)
    
#    CalibrationValArray.append( PowerReactCal & 0xFF)
#    CalibrationValArray.append( (PowerReactCal >> 8) & 0xFF)
#    CalibrationValArray.append( (PowerReactCal >> 16) & 0xFF) 
#    CalibrationValArray.append( (PowerReactCal >> 24) & 0xFF) 
    
    WriteFrame(Registers.Reg_Calibration_Current ,CalibrationValArray , 10)
    
    #SaveToFlash()
    
def ReadCalibrationValues():

    buffercal = ReadFrame(Registers.Reg_Calibration_Current, 0x0E)
    time.sleep(0.1)
    buffercal2 = ReadFrame(Registers.Reg_Line_Frequency_Reference, 0x04)
    time.sleep(0.1)
    
    CalValues = CalibrationValues()
    
    CalValues.VoltageCal =  round( (buffercal[7] << 8 | buffercal[6] )  / 100.0 , 2 )
    CalValues.CurrentCal =  round( (buffercal[5] << 24 | buffercal[4] << 16 | buffercal[3] << 8 | buffercal[2] ) / 1000.0 , 2)
    CalValues.PowerActCal = round( (buffercal[11] << 24 | buffercal[10] << 16 | buffercal[9] << 8 | buffercal[8] ) / 100000 , 2)
    CalValues.LineFreqRef = round( (buffercal2[3] << 8 | buffercal2[2] ) / 1000.0 , 2) 
    CalValues.ThermistorVoltage = round( (buffercal2[5] << 8 | buffercal2[4] ) / 100.0 , 2)
    
    print("Valor Calibracion Voltaje: {} V\nValor Calibracion Corriente: {} mA\nValor Calibracion Potencia Activa: {} W\nValor Calibracion Frecuencia: {} Hz\nValor Calibracion Voltaje Termistor: {} V"
          .format(CalValues.VoltageCal , CalValues.CurrentCal , CalValues.PowerActCal , CalValues.LineFreqRef , CalValues.ThermistorVoltage) )

    # print("Valor Calibracion Voltaje: {} V\nValor Calibracion Corriente: {} mA\nValor Calibracion Potencia Activa: {} W\nValor Calibracion Frecuencia: {} Hz"
    #       .format(CalValues.VoltageCal , CalValues.CurrentCal , CalValues.PowerActCal , CalValues.LineFreqRef ) )
         
def SetEventsLimits(VSag, VSurge, OverCurrent, OverPower):

    limitarray = []
    
    limitarray.append( VSag & 0xFF )
    limitarray.append( (VSag >> 8) & 0xFF )
    
    limitarray.append( VSurge & 0xFF )
    limitarray.append( (VSurge >> 8) & 0xFF )
    
    limitarray.append( OverCurrent & 0xFF )
    limitarray.append( (OverCurrent >> 8) & 0xFF )
    limitarray.append( (OverCurrent >> 16) & 0xFF )
    limitarray.append( (OverCurrent >> 24) & 0xFF )
    
    limitarray.append( OverPower & 0xFF )
    limitarray.append( (OverPower >> 8) & 0xFF )
    limitarray.append( (OverPower >> 16) & 0xFF )
    limitarray.append( (OverPower >> 24) & 0xFF )
    
    WriteFrame(Registers.Reg_Voltage_Sag_Limit , limitarray, 12)
    
   # print (limitarray)
    
    return limitarray

def ReadEventsLimits():
    
    bufferevent = ReadFrame(Registers.Reg_Voltage_Sag_Limit, 0x0E)
    
    Thresholds = EventsLimits()
    
    Thresholds.VSag =   round ( ( bufferevent[3] << 8 | bufferevent[2] ) / 100.0 , 2)
    Thresholds.VSurge = round ( ( bufferevent[5] << 8 | bufferevent[4] ) / 100.0 , 2)
    Thresholds.OverCurrent = round( (bufferevent[9] << 24 | bufferevent[8] << 16 | bufferevent[7] << 8 | bufferevent[6] ) / 1000.0 , 2)  
    Thresholds.OverPower =   round( (bufferevent[13] << 24 | bufferevent[12] << 16 | bufferevent[11] << 8 | bufferevent[10] ) / 100000 , 2)
    Thresholds.OverTemp =    round( (bufferevent[15] << 8 | bufferevent[14] ) )
    
    print("Valor Threshold VSag: {} V\nValor Threshold VSurge: {} V\nValor Threshold OverCurrent: {} mA\nValor Threshold OverPower: {} W"
          .format(Thresholds.VSag ,Thresholds.VSurge , Thresholds.OverCurrent , Thresholds.OverPower) )

def EventConfigRegister(Value):
    
    dataArray = [0]*4;
    dataArray[0] = Value & 0xFF;
    dataArray[1] = (Value >> 8) & 0xFF;
    dataArray[2] = (Value >> 16) & 0xFF;
    dataArray[3] = (Value >> 24) & 0xFF;
    
    WriteFrame(Registers.Reg_Event_Configuration , dataArray , 4)
          
    return dataArray

def LatchEvents():
    
    EventConfigRegister(0x000200F0)
    
def ClearEvents():
    
    EventConfigRegister(0x00020FF0)

def GetValues():
    
    buffervalues = ReadFrame(Registers.Reg_Voltage_RMS, 0x18)
      
    Measurement = Values()
    
    Measurement.VoltageRMS =   round( ( buffervalues[3] << 8 | buffervalues[2]  ) / 100.0 , 2 )
    Measurement.Frequency =    round( ( buffervalues[5] << 8 | buffervalues[4]  ) / 1000.0 , 2)
    Measurement.Temperature =  round( ( buffervalues[7] << 8 | buffervalues[6]  ) / 1023.0 * 3.3 , 2)
    
    Measurement.CurrentRMS =   round( ( buffervalues[13] << 24 | buffervalues[12] << 16 | buffervalues[11] << 8 | buffervalues[10] ) / 1000.0 , 2)
    Measurement.ActivePower =  round( ( buffervalues[17] << 24 | buffervalues[16] << 16 | buffervalues[15] << 8 | buffervalues[14] ) / 100000 , 2)
    Measurement.ReactivePower= round( ( buffervalues[21] << 24 | buffervalues[20] << 16 | buffervalues[19] << 8 | buffervalues[18] ) / 100000 , 2)
    Measurement.AppareantPower=round( ( buffervalues[25] << 24 | buffervalues[24] << 16 | buffervalues[23] << 8 | buffervalues[22] ) / 100000 , 2)
    
    ValuesDict = { 'Voltaje':  Measurement.VoltageRMS , 'Corriente' : Measurement.CurrentRMS , 'Potencia Activa' : Measurement.ActivePower 
                     , 'Potencia Reactiva' : Measurement.ReactivePower , 'Potencia Aparente' : Measurement.AppareantPower 
                     , 'Frecuencia' : Measurement.Frequency , 'Temperatura' : Measurement.Temperature}
    
    
    print("Voltaje = {} V  Corriente = {} mA  Potencia Activa = {} W  Potencia Reactiva = {} VAr  Potencia Aparente = {} VA  Frecuencia = {} Hz  Temperatura = {} Grados"
          .format (Measurement.VoltageRMS , Measurement.CurrentRMS , Measurement.ActivePower , Measurement.ReactivePower , Measurement.AppareantPower , Measurement.Frequency, Measurement.Temperature) )
          
    return ValuesDict
    
def EnergyAccumValues(): 

    bufferaccum = ReadFrame(Registers.Reg_Import_Active , 0x20)
    
    EnergyAccum = EnergyCounters()
    
    EnergyAccum.ImportActivePowerCounter = round( ( bufferaccum[9] << 56 | bufferaccum[8] << 48 | bufferaccum[7] << 40 | bufferaccum[6] << 32 | bufferaccum[5] << 24 | bufferaccum[4] << 16 | bufferaccum[3] << 8
                                            | bufferaccum[2] ) * 0.000001 , 3 )
    
    EnergyAccum.ImportReactivePowerCounter = round( ( bufferaccum[17] << 56 | bufferaccum[16] << 48 | bufferaccum[15] << 40 | bufferaccum[14] << 32 | bufferaccum[13] << 24 | bufferaccum[12] << 16 | bufferaccum[11] << 8
                                            | bufferaccum[2] ) * 0.000001 , 3 )
    
    EnergyAccum.ExportActivePowerCounter = round( ( bufferaccum[25] << 56 | bufferaccum[24] << 48 | bufferaccum[23] << 40 | bufferaccum[22] << 32 | bufferaccum[21] << 24 | bufferaccum[20] << 16 | bufferaccum[19] << 8
                                            | bufferaccum[18] ) * 0.000001 , 3 )
    
    EnergyAccum.ExportReactivePowerCounter = round( ( bufferaccum[33] << 56 | bufferaccum[32] << 48 | bufferaccum[31] << 40 | bufferaccum[30] << 32 | bufferaccum[29] << 24 | bufferaccum[28] << 16 | bufferaccum[27] << 8
                                            | bufferaccum[26] ) * 0.000001 , 3 )
    
    EnergyAccumDict = {'ImportActivePowerCounter' : EnergyAccum.ImportActivePowerCounter , 'ImportReactivePowerCounter' :EnergyAccum.ImportReactivePowerCounter ,
                       'ExportActivePowerCounter' : EnergyAccum.ExportActivePowerCounter , 'ExportReactivePowerCounter' :EnergyAccum.ExportReactivePowerCounter }
    
    print("Potencia Activa Acumulada: {} W/h" .format(EnergyAccum.ImportActivePowerCounter) )
    
    return EnergyAccumDict

def ScanEvents():
    
    bufferevents = ReadFrame(Registers.Reg_System_Status, 0x02)
    
    Events = EventsFlags()
    
    EventByteBin = bufferevents[2] & 0xF
   
    print(EventByteBin)
       
    if( EventByteBin == 0x0 ):
        
        Events.NoEventFlag = True
        
        print("No se han detectado alertas\nHora : {}".format( datetime.datetime.now() ))
        
    elif( EventByteBin == 0x1 ):
        
        Events.VSagFlag = True        
        print("Se ha detectado SAG Voltage")
        
    elif( EventByteBin == 0x2 ):
        
        Events.VSurgeFlag = True        
        print("Se ha detectado Surge Voltage")
        
    elif( EventByteBin == 0x4 ):
        
        Events.OverCurrentFlag = True
        print("Se ha detectado Sobre Corriente")
        
    elif( EventByteBin == 0x5 ):
        
        Events.VSagFlag = True
        Events.OverCurrentFlag = True
        print("Se ha detectado SAG Voltage y Sobre Corriente") 
    
    elif( EventByteBin == 0x6 ):
        
        Events.VSurgeFlag = True
        Events.OverCurrentFlag = True
        print("Se ha detectado Surge Voltage y Sobre Corriente")
           
    elif( EventByteBin == 0x8 ):
        
        Events.OverPowerFlag = True
        print("Se ha detectado Sobre Carga")
        
    elif( EventByteBin == 0x9 ):
        
        Events.VSagFlag = True
        Events.OverPowerFlag = True
        print("Se ha detectado SAG Voltage y Sobre Carga")
        
    elif( EventByteBin == 0xA ):
        
        Events.OverPowerFlag = True
        Events.VSurgeFlag = True
        print("Se ha detectado Sobre Carga y Surge Voltaje")
        
    elif( EventByteBin == 0xC ):
        
        Events.OverPowerFlag = True
        Events.OverCurrentFlag = True
        print("Se ha detectado Sobre Carga y Sobre Corriente")   
             
    elif( EventByteBin == 0xD ):
        
        Events.OverPowerFlag = True
        Events.OverCurrentFlag = True
        Events.VSagFlag = True
        print("Se ha detectado Sobre Carga , Sobre Corriente , SAG Voltage")
        
    elif( EventByteBin == 0xE ): 
        
        Events.OverPowerFlag = True
        Events.OverCurrentFlag = True
        Events.VSurgeFlag = True
        print("Se ha detectado Sobre Carga , Sobre Corriente , Surge Voltage")
    
    EventsDict = { 'VSag':  Events.VSagFlag , 'VSurge' : Events.VSurgeFlag , 'OverCurrent' : Events.OverCurrentFlag  , 'OverPower' : Events.OverPowerFlag , 'NoEvent': Events.NoEventFlag , 'Hour' : datetime.datetime.now() }
    
    #ClearEvents()
    #print(EventsDict)
   
    return(EventsDict)
    
    #print (buffer)
