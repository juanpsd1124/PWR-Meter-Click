# -*- coding: utf-8 -*-
"""
Created on Sun Jan 20 23:05:15 2019

@author: Juan Posada
"""
from enum import Enum
import serial
import time
import datetime
import json
import threading
import queue as queue
#from AWSPowerMeterClick import *

ser = serial.Serial(
    port = 'COM6',
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout=1 # add this
    )

fifo_queue = queue.Queue(0)
semaforo = threading.Semaphore(1)
semaforo2 = threading.Semaphore(1)

bloqueothread = threading.Lock()

ValuesSum = [ [], [], [], [], [], [], [], [] ]

AlertByte = 0
AlertLatch = 0

def SendSerial():
    
  global f_recibidoencoded

  global frecibido

  global intlista

  global recibido

  #semaforo2.acquire()

  #bloqueothread.acquire()

  semaforo2.acquire()

  ser.write(fifo_queue.get())

  # semaforo2.release()
   
  time.sleep(0.1)    

  n = ser.inWaiting()

  recibido = ser.read(n)

  semaforo2.release()

  #bloqueothread.release()

  # print(recibido)

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
    Command_Auto_Calibrate_Reactive_Gain = 0x7A
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

        recibido = 0 
        
        semaforo.release()
        
        time.sleep(0.2)
        
#        print(Receive)
        
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
        
        print(WriteFrame)
        
        #SendSerial(WriteFrame)
        
        fifo_queue.put(WriteFrame)
        
        SendSerial()
   
        return WriteFrame
    
def SaveToFlash():
    
   SaveFixedCommand = FixedCommandsFrame()
   fifo_queue.put(SaveFixedCommand.SaveToFlash)
   response = SendSerial()

   if(response [0] == 0x06):

        print("Registros guardados Memoria Flash Correctamente")

   elif(response [0] == 0x15):

        print("Comando guardar registros en Memoria Flash no ejecutado: NAK 0x15")

   elif(response [0] == 0x51):

        print("Comando guardar registros en Memoria Flash: CSFAIL 0x51")

   return response[0]
   
def SaveEnergyCounters():

   SaveEnergyFixedCommand = FixedCommandsFrame()
   fifo_queue.put(SaveEnergyFixedCommand.SaveEnergyCounters )
   response = SendSerial()

   if(response [0] == 0x06):

        print("Contadores guardados en EEPROM Correctamente")

   elif(response [0] == 0x15):

        print("Comando guardar contadores no ejecutado: NAK 0x15")

   elif(response [0] == 0x51):

        print("Comando guardar contadores no ejecutado: CSFAIL 0x51")

   return response[0]

def AutoCalibrationGain():
    
   AutoCalFixedCommand = FixedCommandsFrame()
   fifo_queue.put(AutoCalFixedCommand.AutoCalGain)
   response = SendSerial()

   if(response [0] == 0x06):

        print("Auto Calibracion realizada Correctamente")

   elif(response [0] == 0x15):

        print("Comando Auto Calibracion no ejecutado: NAK 0x15")

   elif(response [0] == 0x51):

        print("Comando Auto Calibracion: CSFAIL 0x51")

   return response[0]
        
def AutoCalibrationReactive():
    
   AutoCalReactFixedCommand = FixedCommandsFrame()
   fifo_queue.put(AutoCalReactFixedCommand.AutoCalReactGain)
   response = SendSerial()

   if(response [0] == 0x06):

        print("Auto Calibracion Reactiva realizada Correctamente")

   elif(response [0] == 0x15):

        print("Comando Auto Calibracion Reactiva no ejecutado: NAK 0x15")

   elif(response [0] == 0x51):

        print("Comando Auto Calibracion Reactiva: CSFAIL 0x51")

   return response[0]

def AutoCalibrationFrequency():

    AutoCalFreqFixedCommand = FixedCommandsFrame()
    fifo_queue.put(AutoCalFreqFixedCommand.AutoCalFrequency)
    response = SendSerial()

    if(response [0] == 0x06):

        print("Auto Calibracion de Frecuencia realizada Correctamente")

    elif(response [0] == 0x15):

        print("Comando Auto Calibracion de Frecuencia no ejecutado: NAK 0x15")

    elif(response [0] == 0x51):

        print("Comando Auto Calibracion de Frecuencia: CSFAIL 0x51")

    return response[0]
   
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
    
    response = WriteFrame(Registers.Reg_Calibration_Current ,CalibrationValArray , 10)

    return response[0]
    
def ReadCalibrationValues():
    
    try:

        buffercal = ReadFrame(Registers.Reg_Calibration_Current, 0x0E)
        time.sleep(0.1)
        buffercal2 = ReadFrame(Registers.Reg_Line_Frequency_Reference, 0x04)
        time.sleep(0.1)
    
        CalValues = CalibrationValues()
        
        if(buffercal[0] == 0x06):
    
            CalValues.VoltageCal =  round( (buffercal[7] << 8 | buffercal[6] )  / 100.0 , 2 )
            CalValues.CurrentCal =  round( (buffercal[5] << 24 | buffercal[4] << 16 | buffercal[3] << 8 | buffercal[2] ) / 1000.0 , 2)
            CalValues.PowerActCal = round( (buffercal[11] << 24 | buffercal[10] << 16 | buffercal[9] << 8 | buffercal[8] ) / 100000 , 2)
            CalValues.LineFreqRef = round( (buffercal[3] << 8 | buffercal[2] ) / 1000.0 , 2) 
            CalValues.ThermistorVoltage = round( (buffercal2[5] << 8 | buffercal2[4] ) / 100.0 , 2)

            CalValuesDict = {  'Success': True,
                               'VoltageCal': CalValues.VoltageCal,
                               'CurrentCal': CalValues.CurrentCal,
                               'PowerActCal': CalValues.PowerActCal,
                               'LineFreqRef': CalValues.LineFreqRef,
                               'ThermistorVoltage': CalValues.ThermistorVoltage 
                            }
            
            # print("Valor Calibracion Voltaje: {} V\nValor Calibracion Corriente: {} mA\nValor Calibracion Potencia Activa: {} W\nValor Calibracion Frecuencia: {} Hz\nValor Calibracion Voltaje Termistor: {} V"
            #       .format(CalValues.VoltageCal , CalValues.CurrentCal , CalValues.PowerActCal , CalValues.LineFreqRef , CalValues.ThermistorVoltage) )                   

            # CalValues.VoltageCal =  buffercal[7] << 8 | buffercal[6] 
            # CalValues.CurrentCal =  buffercal[5] << 24 | buffercal[4] << 16 | buffercal[3] << 8 | buffercal[2]
            # CalValues.PowerActCal = buffercal[11] << 24 | buffercal[10] << 16 | buffercal[9] << 8 | buffercal[8]
            # CalValues.LineFreqRef = buffercal[3] << 8 | buffercal[2] 
            # CalValues.ThermistorVoltage = buffercal2[5] << 8 | buffercal2[4]

            # CalValuesDict = {  'Success': True,
            #                    'VoltageCal': round ( CalValues.VoltageCal / 100.0, 2) ,
            #                    'CurrentCal': round (CalValues.CurrentCal /  1000.0, 2),
            #                    'PowerActCal': round(CalValues.PowerActCal/ 100000, 2 ),
            #                    'LineFreqRef': round(CalValues.LineFreqRef / 100000, 2),
            #                    'ThermistorVoltage': round(CalValues.ThermistorVoltage / 100.0 , 2) 
            #}

            return CalValuesDict

    except Exception as e:
               
            print("Se ha producido error de tipo: {}".format( type(e).__name__))

                 
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
    #bufferevent = ReadFrame(Registers.Reg_Voltage_Sag_Limit, 0x0A)
        
    Thresholds = EventsLimits()
    
    try:
        
        if( bufferevent[0] == 0x06):
    
            Thresholds.VSag =   round ( ( bufferevent[3] << 8 | bufferevent[2] ) / 100.0 , 2)
            Thresholds.VSurge = round ( ( bufferevent[5] << 8 | bufferevent[4] ) / 100.0 , 2)
            Thresholds.OverCurrent = round( (bufferevent[9] << 24 | bufferevent[8] << 16 | bufferevent[7] << 8 | bufferevent[6] ) / 1000.0 , 2)  
            Thresholds.OverPower =   round( (bufferevent[13] << 24 | bufferevent[12] << 16 | bufferevent[11] << 8 | bufferevent[10] ) / 100000 , 2)
            Thresholds.OverTemp =    round( (bufferevent[15] << 8 | bufferevent[14] ) )

            ThresholdsValuesDict = { 'VSagValue': Thresholds.VSag,
                                     'VSurgeValue': Thresholds.VSurge,
                                     'OverCurrentValue': Thresholds.OverCurrent,
                                     'OverPowerValue': Thresholds.OverPower,
                                     'OverTempValue' : Thresholds.OverTemp
                                   }
    
            print("Valor Threshold VSag: {} V\nValor Threshold VSurge: {} V\nValor Threshold OverCurrent: {} mA\nValor Threshold OverPower: {} W"
                  .format(Thresholds.VSag ,Thresholds.VSurge , Thresholds.OverCurrent , Thresholds.OverPower) )

            return ThresholdsValuesDict

    except Exception as e:
                   
            print("Se ha procucido error de tipo: {}".format( type(e).__name__ ) )
            
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

    print("Latch Events Ready")
    
def ClearEvents():
    
    EventConfigRegister(0x000F0FF0)

def GetValues():

    global AlertByte
    global AlertLatch
    
    buffervalues = ReadFrame(Registers.Reg_Voltage_RMS, 0x18)
    bufferaccum = ReadFrame(Registers.Reg_Import_Active , 0x20)
    bufferalerts = ReadFrame(Registers.Reg_System_Status, 0x02)

    AlertByte = bufferalerts[2] & 0xF
    AlertLatch = (bufferalerts[3] & 0x7) >> 2

    # print(bufferalerts)
    # print(AlertByte)
    # print(AlertLatch)
      
    Measurement = Values()
    EnergyAccum = EnergyCounters()
    alerts = EventsFlags()
    
    try:
        
        if(buffervalues[0] == 0x06 and bufferaccum[0] == 0x06 and bufferalerts[0] == 0x06):
    
            Measurement.VoltageRMS =   round( ( buffervalues[3] << 8 | buffervalues[2]  ) / 100.0 , 2 )
            Measurement.Frequency =    round( ( buffervalues[5] << 8 | buffervalues[4]  ) / 1000.0 , 2)
            Measurement.Temperature =  round( ( buffervalues[7] << 8 | buffervalues[6]  ) / 1023.0 * 3.3 , 2)
    
            Measurement.CurrentRMS =   round( ( buffervalues[13] << 24 | buffervalues[12] << 16 | buffervalues[11] << 8 | buffervalues[10] ) / 1000.0 , 2)
            Measurement.ActivePower =  round( ( buffervalues[17] << 24 | buffervalues[16] << 16 | buffervalues[15] << 8 | buffervalues[14] ) / 100000 , 2)
            Measurement.ReactivePower= round( ( buffervalues[21] << 24 | buffervalues[20] << 16 | buffervalues[19] << 8 | buffervalues[18] ) / 100000 , 2)
            Measurement.AppareantPower=round( ( buffervalues[25] << 24 | buffervalues[24] << 16 | buffervalues[23] << 8 | buffervalues[22] ) / 100000 , 2)

            EnergyAccum.ImportActivePowerCounter = round( ( bufferaccum[9] << 56 | bufferaccum[8] << 48 | bufferaccum[7] << 40 | bufferaccum[6] << 32 | bufferaccum[5] << 24 | bufferaccum[4] << 16 | bufferaccum[3] << 8
                                                           | bufferaccum[2] ) * 0.000001 , 2 )
            EnergyAccum.ImportReactivePowerCounter = round( ( bufferaccum[17] << 56 | bufferaccum[16] << 48 | bufferaccum[15] << 40 | bufferaccum[14] << 32 | bufferaccum[13] << 24 | bufferaccum[12] << 16 | bufferaccum[11] << 8
                                                           | bufferaccum[2] ) * 0.000001 , 3 )    
            EnergyAccum.ExportActivePowerCounter = round( ( bufferaccum[25] << 56 | bufferaccum[24] << 48 | bufferaccum[23] << 40 | bufferaccum[22] << 32 | bufferaccum[21] << 24 | bufferaccum[20] << 16 | bufferaccum[19] << 8
                                                           | bufferaccum[18] ) * 0.000001 , 3 )    
            EnergyAccum.ExportReactivePowerCounter = round( ( bufferaccum[33] << 56 | bufferaccum[32] << 48 | bufferaccum[31] << 40 | bufferaccum[30] << 32 | bufferaccum[29] << 24 | bufferaccum[28] << 16 | bufferaccum[27] << 8
                                                           | bufferaccum[26] ) * 0.000001 , 3 )
           
            # ValuesDict = { 'voltaje':  Measurement.VoltageRMS ,
            #                'corriente' : Measurement.CurrentRMS ,
            #                'potencia activa' : Measurement.ActivePower, 
            #                'potencia reactiva' : Measurement.ReactivePower ,
            #                'potencia aparente' : Measurement.AppareantPower , 
            #                'frecuencia' : Measurement.Frequency ,
            #                'temperatura' : Measurement.Temperature,
            #                'potencia activa consumida' : EnergyAccum.ImportActivePowerCounter,
            #                'potencia consumida reactiva' : EnergyAccum.ImportReactivePowerCounter}

            ValuesList = [Measurement.VoltageRMS,
                          Measurement.CurrentRMS,
                          Measurement.ActivePower,
                          Measurement.ReactivePower,
                          Measurement.AppareantPower,
                          Measurement.Frequency,
                          Measurement.Temperature,
                          EnergyAccum.ImportActivePowerCounter,
                          EnergyAccum.ImportReactivePowerCounter
                          ]

            # print("Voltaje = {} V  Corriente = {} mA  Potencia Activa = {} W  Potencia Reactiva = {} VAr  Potencia Aparente = {} VA  Frecuencia = {} Hz  Temperatura = {} Grados Potencia Consumida = {} W/h"
            #       .format (Measurement.VoltageRMS , Measurement.CurrentRMS , Measurement.ActivePower , Measurement.ReactivePower , Measurement.AppareantPower , Measurement.Frequency, Measurement.Temperature, EnergyAccum.ImportActivePowerCounter) )
     
            return ValuesList, EnergyAccum.ImportActivePowerCounter, EnergyAccum.ImportReactivePowerCounter
            # return Measurement.VoltageRMS, Measurement.CurrentRMS, Measurement.ActivePower, Measurement.ReactivePower, Measurement.AppareantPower, Measurement.Frequency, Measurement.Temperature, EnergyAccum.ImportActivePowerCounter
    
    except Exception as e:
                   
            print("Se ha producido error de tipo: {}".format( type(e).__name__ ) )


def SumValues():

    global SumValues

    
    Val,PWRAccum_Active,PWRAccum_React = GetValues()

    for i in range(0,7):
    
        ValuesSum[i].append(Val[i])

    ValuesSum[7] = PWRAccum_Active
    #ValuesSum[8] = PWRAccum_React

    #print(ValuesSum)

    return ValuesSum
       
def ScanEvents():
       
    alerts = EventsFlags()
    
    if(AlertByte == 0x0):

        alerts.NoEventFlag == True

        print("No se han detectado alertas\nHora : {}".format( datetime.datetime.now() ))

    elif( AlertByte == 0x1 ):
        
        alerts.VSagFlag = True        
        print("Se ha detectado SAG Voltage")
        
    elif( AlertByte == 0x2 ):
        
        alerts.VSurgeFlag = True        
        print("Se ha detectado Surge Voltage")
        
    elif( AlertByte == 0x4 ):
        
        alerts.OverCurrentFlag = True
        print("Se ha detectado Sobre Corriente")
        
    elif( AlertByte == 0x5 ):
        
        alerts.VSagFlag = True
        alerts.OverCurrentFlag = True
        print("Se ha detectado SAG Voltage y Sobre Corriente") 
    
    elif( AlertByte == 0x6 ):
        
        alerts.VSurgeFlag = True
        alerts.OverCurrentFlag = True
        print("Se ha detectado Surge Voltage y Sobre Corriente")
           
    elif( AlertByte == 0x8 ):
        
        alerts.OverPowerFlag = True
        print("Se ha detectado Sobre Carga")
        
    elif( AlertByte == 0x9 ):
        
        alerts.VSagFlag = True
        alerts.OverPowerFlag = True
        print("Se ha detectado SAG Voltage y Sobre Carga")
        
    elif( AlertByte == 0xA ):
        
        alerts.OverPowerFlag = True
        alerts.VSurgeFlag = True
        print("Se ha detectado Sobre Carga y Surge Voltaje")
        
    elif( AlertByte == 0xC ):
        
        alerts.OverPowerFlag = True
        alerts.OverCurrentFlag = True
        print("Se ha detectado Sobre Carga y Sobre Corriente")   
             
    elif( AlertByte == 0xD ):
        
        alerts.OverPowerFlag = True
        alerts.OverCurrentFlag = True
        alerts.VSagFlag = True
        print("Se ha detectado Sobre Carga , Sobre Corriente , SAG Voltage")
        
    elif( AlertByte == 0xE ): 
        
        alerts.OverPowerFlag = True
        alerts.OverCurrentFlag = True
        alerts.VSurgeFlag = True
        print("Se ha detectado Sobre Carga , Sobre Corriente , Surge Voltage")

    AlertsList = [alerts.VSagFlag, 
                  alerts.VSurgeFlag,
                  alerts.OverCurrentFlag,
                  alerts.OverPowerFlag,
                  alerts.NoEventFlag
                 ]
                 
    return(AlertsList)


        
# SaveToFlash()
# SaveEnergyCounters()
# AutoCalibrationGain()
# AutoCalibrationReactive()
# AutoCalibrationFrequency()

print(GetValues())

#GetValues()
