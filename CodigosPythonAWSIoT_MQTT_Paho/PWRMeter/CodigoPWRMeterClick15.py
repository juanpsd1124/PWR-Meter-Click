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
import logging
import queue as queue

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.WARNING, datefmt='%m/%d/%Y %I:%M:%S %p')

ser = serial.Serial(
    port     = 'COM6',
    baudrate = 115200,
    parity   = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout  =1 # add this
    )

hora = datetime.datetime.now()

fifo_queue = queue.Queue(0)
# semaforo = threading.Semaphore(1)
# semaforo2 = threading.Semaphore(1)

bloqueothread  = threading.Lock()
bloqueothread2 = threading.Lock()

ValuesList = [0,0,0,0,0,0,0,0,0,0]
ValuesSum  = [ [], [], [], [], [], [], [], [], [], [] ]

AlertByte  = 0
AlertLatch = 0

# UnitCost = GetUnitCost()

def SendSerial():
    
  global f_recibidoencoded

  global frecibido

  global intlista

  global recibido

  ser.write(fifo_queue.get())
 
  time.sleep(0.1)

  n = ser.inWaiting()

  bloqueothread.acquire()  

  recibido = ser.read(n)

  bloqueothread.release()

  #print(recibido)

  return recibido


class Registers(int , Enum):

    Reg_System_Status = 0x02
 
##Measurement Registers    
    Reg_Voltage_RMS        = 0x06
    Reg_Line_Frecuency     = 0x08
    Reg_Thermistor_Voltage = 0x0A
    Reg_Power_Factor       = 0x0C
    Reg_Current_RMS        = 0x0E
    Reg_Active_Power       = 0x12
    Reg_Reactive_Power     = 0x16
    Reg_Appareant_Power    = 0x1A
    Reg_Minimum_Record_One = 0x3E
    Reg_Minimum_Record_Two = 0x42
    Reg_Maximum_Record_Two = 0x46
    Reg_Maxinum_Record_Two = 0x4A
    
##Energy Counters Registers
    Reg_Import_Active      = 0x1E
    Reg_Export_Active      = 0x26
    Reg_Import_Reactive    = 0x2E
    Reg_Export_Reactive    = 0x36
    
##Design Configuration Registers
    
    Reg_System_Configuration = 0x94
    Reg_Event_Configuration  = 0x98
    Reg_Range                = 0x9C
    Reg_Calibration_Current  = 0xA0
    Reg_Calibration_Voltage  = 0xA4
    Reg_Calibration_Power_Active   = 0xA6
    Reg_Calibration_Power_Reactive = 0xAA
    
    Reg_App_Power_Divisors_Digits       = 0xBE
    Reg_Accumulation_Inverval_Parameter = 0xC0
    Reg_Min_Max_Pointer_One             = 0xC6
    Reg_Min_Max_Pointer_Two             = 0xC8
    Reg_Line_Frequency_Reference        = 0xCA
    Reg_Thermistor_Voltage_Calibration  = 0xCC
    
    Reg_Voltage_Sag_Limit      = 0xCE
    Reg_Voltage_Surge_Limit    = 0xD0
    Reg_OverCurrent_Limit      = 0xD2
    Reg_OverPower_Limit        = 0xD6
    Reg_OverTemperature_Limit  = 0xDA
    Reg_Voltage_Low_Threshold  = 0xDC
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
        
        self.SaveToFlash        = [0xA5 , 0x04, Commands.Command_Save_Flash, 0xFC]
        self.SaveEnergyCounters = [0xA5 , 0x04, Commands.Command_Save_Energy_Counters , 0xEE]
        self.AutoCalGain        = [0xA5 , 0x04, Commands.Command_Auto_Calibrate_Gain, 0x03]
        self.AutoCalReactGain   = [0xA5 , 0x04 , Commands.Command_Auto_Calibrate_Reactive_Gain , 0x23]
        self.AutoCalFrequency   = [0xA5 , 0x04 , Commands.Command_Auto_Calibrate_Frequency , 0x1F ]
        self.BulkEraseEEPROM    = [0xA4 , 0x04 , Commands.Command_Bulk_Erase_EEPROM , 0xF8]
                
class Values():
    
    def __init__(self, VoltageRMS = None , Frequency = None , Temperature = None,
                 PowerFactor = None , Current = None, ActivePower = None , ReactivePower = None, AppareantPower = None ):
        
        self.VoltageRMS     = VoltageRMS
        self.Frequency      = Frequency
        self.Temperature    = Temperature
        self.PowerFactor    = PowerFactor
        self.CurrentRMS     = Current
        self.ActivePower    = ActivePower
        self.ReactivePower  = ReactivePower
        self.AppareantPower = AppareantPower
              
class CalibrationValues():
    
    def __init__(self, VoltageCal = None , CurrentCal = None , PowerActCal = None , LineFreqRef = None , ThermistorVoltage = None):
        
        self.VoltageCal        = VoltageCal
        self.CurrentCal        = CurrentCal
        self.PowerActCal       = PowerActCal
        self.LineFreqRef       = LineFreqRef
        self.ThermistorVoltage = ThermistorVoltage
        
class EnergyCounters():
    
    def __init__(self, ImportActivePowerCounter = None , ImportReactivePowerCounter = None , ExportActivePowerCounter = None , ExportReactivePowerCounter = None):
        
         self.ImportActivePowerCounter   = ImportActivePowerCounter
         self.ImportReactivePowerCounter = ImportReactivePowerCounter
         self.ExportActivePowerCounter   = ExportActivePowerCounter
         self.ExportReactivePowerCounter = ExportReactivePowerCounter
                 
class EventsLimits():
    
    def __init__(self, VSag = None , VSurge = None , OverCurrent = None , OverPower = None , OverTemp = None):
        
         self.VSag        = VSag
         self.VSurge      = VSurge
         self.OverCurrent = OverCurrent
         self.OverPower   = OverPower
         self.OverTemp    = OverTemp
        
class EventsFlags():
    
    def __init__(self,NoEventFlag = False, VSagFlag = False , VSurgeFlag = False, OverCurrentFlag = False, OverPowerFlag = False):
              
         self.NoEventFlag     = NoEventFlag
         self.VSagFlag        = VSagFlag
         self.VSurgeFlag      = VSurgeFlag
         self.OverCurrentFlag = OverCurrentFlag
         self.OverPowerFlag   = OverPowerFlag
                
##-----------------------------------Methods-------------------------------------------##
         
def ReadFrame(Addr_Low, NoB):
        
	global fifo_queue

	HeaderByte     = 0xA5
	NoBF           = 0x08
	CommandPointer = 0x41
	Addr_High      = 0x00
	Addr_Low       = Addr_Low
	Command        = 0x4E
	NoB            = NoB
	Checksum       = None
	Buffer         = []

	Readframe = [HeaderByte , NoBF, CommandPointer, Addr_High, Addr_Low, Command , NoB]

	Checksum = sum(Readframe) % 256

	Readframe.append(Checksum)

	fifo_queue.put(Readframe)
	    
	Receive =  SendSerial()

	bloqueothread2.acquire() 

	Buffer.extend( Receive )

	bloqueothread2.release() 

	recibido = 0 
	    
	    #time.sleep(0.2)
	    
	#        print(Receive)
	    
	    #Buffer.extend( SendSerial(Readframe) ) 

	#print(Buffer)
	    
	return Buffer

def WriteFrame(Addr_Low, Data, NoB):
       
        HeaderByte     = 0xA5
        CommandPointer = 0x41
        Addr_High      = 0x00
        Addr_Low       = Addr_Low
        Command        = Commands.Command_Reg_Write
        NoB            = NoB
        NoBF           = NoB + 8
        Data           = Data
        
        WriteFrame = [HeaderByte , NoBF, CommandPointer, Addr_High, Addr_Low, Command , NoB]
           
        WriteFrame.extend(Data)
                    
        WriteFrame.append( sum(WriteFrame) % 256)
        
        #print (WriteFrame)
        
        #SendSerial(WriteFrame)
        
        fifo_queue.put(WriteFrame)
        
        answer = SendSerial()
   
        return answer
    
def SaveToFlash():
    
   SaveFixedCommand = FixedCommandsFrame()
   fifo_queue.put(SaveFixedCommand.SaveToFlash)
   response = SendSerial()

   if(response [0] == 0x06):

        logging.debug('Registros guardados en memoria flash')

   elif(response [0] == 0x15):

        logging.debug('Registros no guardados en memoria flash (NAK 0x15)')

   elif(response [0] == 0x51):

        logging.debug('Registros no guardados en memoria flash (CSFAIL 0x51)')

   return response[0]
   
def SaveEnergyCounters():

   SaveEnergyFixedCommand = FixedCommandsFrame()
   fifo_queue.put(SaveEnergyFixedCommand.SaveEnergyCounters )
   response = SendSerial()

   if(response [0] == 0x06):

        logging.debug('Contadores de energia guardados en EEPROM: %.2f KhW' , ValuesList[8])

   elif(response [0] == 0x15):

        logging.debug('Fallo al guardar contadores en EEPROM (NAK 0x15)')

   elif(response [0] == 0x51):

        logging.debug('Fallo al guardar contadores en EEPROM (CSFAIL 0x51)')

   return response[0]

def AutoCalibrationGain():
    
   AutoCalFixedCommand = FixedCommandsFrame()
   fifo_queue.put(AutoCalFixedCommand.AutoCalGain)
   response = SendSerial()

   if(response [0] == 0x06):

        logging.debug('Se ha realizado calibracion correctamente')

   elif(response [0] == 0x15):

        logging.debug('Fallo al realizar calibracion (NAK 0x15)')

   elif(response [0] == 0x51):

        logging.debug('Fallo al realizar calibracion (CSFAIL 0x51')

   return response[0]
        
def AutoCalibrationReactive():
    
   AutoCalReactFixedCommand = FixedCommandsFrame()
   fifo_queue.put(AutoCalReactFixedCommand.AutoCalReactGain)
   response = SendSerial()

   if(response [0] == 0x06):

        logging.debug('Se ha realizado calibracion de energia reactiva correctamente')
    
   elif(response [0] == 0x15):

        logging.debug('Fallo al realizar calibracion de energia reactiva (NAK 0x15)')

   elif(response [0] == 0x51):

        logging.debug('Fallo al realizar calibracion de energia reactiva (CSFAIL 0x51')

   return response[0]

def AutoCalibrationFrequency(FreqCal):

    AutoCalFreqFixedCommand = FixedCommandsFrame()
    fifo_queue.put(AutoCalFreqFixedCommand.AutoCalFrequency)
    response = SendSerial()

    if(response [0] == 0x06):

        logging.debug("Auto Calibracion de Frecuencia realizada Correctamente")

    elif(response [0] == 0x15):

        logging.debug("Comando Auto Calibracion de Frecuencia no ejecutado: NAK 0x15")

    elif(response [0] == 0x51):

        logging.debug("Comando Auto Calibracion de Frecuencia: CSFAIL 0x51")

    return response[0]
   
def SetCalibrationValues(VoltageCal, CurrentCal, PowerActCal, FreqCal):
    
    CalibrationValArray = []
    CalibrationFreqValArray = [] 

    numVoltageCal   = int( VoltageCal.replace(".","") )
    numCurrentCal   = int( CurrentCal.replace(".","") )
    numPowerActCal  = int( PowerActCal.replace(".","") )
    numFreqCal      = int( FreqCal.replace(".","") )
    
    CalibrationValArray.append( numCurrentCal & 0xFF )
    CalibrationValArray.append( ( numCurrentCal >> 8) & 0xFF )
    CalibrationValArray.append( ( numCurrentCal >> 16) & 0xFF )
    CalibrationValArray.append( ( numCurrentCal >> 24) & 0xFF )   
     
    CalibrationValArray.append( numVoltageCal & 0xFF )
    CalibrationValArray.append( ( numVoltageCal >> 8) & 0xFF )
     
    CalibrationValArray.append( numPowerActCal & 0xFF)
    CalibrationValArray.append( (numPowerActCal >> 8) & 0xFF)
    CalibrationValArray.append( (numPowerActCal >> 16) & 0xFF) 
    CalibrationValArray.append( (numPowerActCal >> 24) & 0xFF)

    CalibrationFreqValArray.append( numFreqCal & 0xFF)
    CalibrationFreqValArray.append( (numFreqCal >> 8) & 0xFF)
    
#    CalibrationValArray.append( PowerReactCal & 0xFF)
#    CalibrationValArray.append( (PowerReactCal >> 8) & 0xFF)
#    CalibrationValArray.append( (PowerReactCal >> 16) & 0xFF) 
#    CalibrationValArray.append( (PowerReactCal >> 24) & 0xFF)
    
    response = WriteFrame(Registers.Reg_Calibration_Current ,CalibrationValArray , 10)
    responseFreq = WriteFrame(Registers.Reg_Line_Frequency_Reference,CalibrationFreqValArray, 2)
    calibrationVal = ReadCalibrationValues()

    if(response == 0x06):

        logging.debug('Valores de calibracion ajustados. Voltage: %.2f V, Current: %.2f A, PowerAct: %.2f W, Frequency: %.2f Hz',
                        calibrationVal['VoltageCal'], calibrationVal['CurrentCal'], calibrationVal['PowerActCal'], calibrationVal['LineFreqRef'])

    elif(response == 0x15):

        logging.debug('Fallo al ajustar valores de calibracion (NAK 0x15)')
    
    if(responseFreq == 0x06):

        logging.debug('Valores de calibracion de frecuencia ajustado')

    elif(responseFreq == 0x15):

        logging.debug('Fallo al ajustar valor de calibracion de frecuencia (NAK 0x15)')

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

            return CalValuesDict

    except Exception as e:
               
            print("Se ha producido error de tipo: {}".format( type(e).__name__))

                 
def SetEventsLimits(VSag,VSurge,OverCurrent,OverPower):

    limitarray = []

    numVSag        = int( VSag.replace(".","") )
    numVSurge      = int( VSurge.replace(".","") )
    numOverCurrent = int( OverCurrent.replace(".","") )
    numOverPower   = int( OverPower.replace(".","") )

    limitarray.append( numVSag & 0xFF )
    limitarray.append( (numVSag >> 8) & 0xFF )
    
    limitarray.append( numVSurge & 0xFF )
    limitarray.append( (numVSurge >> 8) & 0xFF )
    
    limitarray.append( numOverCurrent & 0xFF )
    limitarray.append( (numOverCurrent >> 8) & 0xFF )
    limitarray.append( (numOverCurrent >> 16) & 0xFF )
    limitarray.append( (numOverCurrent >> 24) & 0xFF )
    
    limitarray.append( numOverPower & 0xFF )
    limitarray.append( (numOverPower >> 8) & 0xFF )
    limitarray.append( (numOverPower >> 16) & 0xFF )
    limitarray.append( (numOverPower >> 24) & 0xFF )
  
    response     = WriteFrame(Registers.Reg_Voltage_Sag_Limit , limitarray, 12)
    eventsvalues = ReadEventsLimits()

    if(response[0] == 0x06):

        logging.debug('Valores de alertas ajustados. VSag: %.2f V ,VSurge: %.2f V, OverCurrent: %.2f A, OverPower: %.2f W',
                       eventsvalues['VSagValue'], eventsvalues['VSurgeValue'], eventsvalues['OverCurrentValue'], eventsvalues['OverPowerValue'] )
     
    return limitarray

def ReadEventsLimits():
    
    bufferevent = ReadFrame(Registers.Reg_Voltage_Sag_Limit, 0x0E)
    Thresholds = EventsLimits()
    
    try:
        
        if( bufferevent[0] == 0x06):
    
            Thresholds.VSag        = round ( ( bufferevent[3] << 8 | bufferevent[2] ) * 0.01 , 2)
            Thresholds.VSurge      = round ( ( bufferevent[5] << 8 | bufferevent[4] ) * 0.01 , 2)
            Thresholds.OverCurrent = round( (bufferevent[9] << 24 | bufferevent[8] << 16 | bufferevent[7] << 8 | bufferevent[6] ) * 0.01 , 2)  
            Thresholds.OverPower   = round( (bufferevent[13] << 24 | bufferevent[12] << 16 | bufferevent[11] << 8 | bufferevent[10] ) * 0.01 , 2)
            Thresholds.OverTemp    = round( (bufferevent[15] << 8 | bufferevent[14] ) )

            ThresholdsValuesDict = { 'VSagValue': Thresholds.VSag,
                                     'VSurgeValue': Thresholds.VSurge,
                                     'OverCurrentValue': Thresholds.OverCurrent,
                                     'OverPowerValue': Thresholds.OverPower,
                                     'OverPowerValue' : Thresholds.OverTemp
                                   }
    
            # print("Valor Threshold VSag: {} V\nValor Threshold VSurge: {} V\nValor Threshold OverCurrent: {} A\nValor Threshold OverPower: {} W"
            #       .format(Thresholds.VSag ,Thresholds.VSurge , Thresholds.OverCurrent , Thresholds.OverPower) )

            return ThresholdsValuesDict

    except Exception as e:
                   
            print("Se ha producido error de tipo: {}".format( type(e).__name__ ) )
            
####################### Event Register Config Functions ################################    

def LatchEvents(VSurge,VSag,OverPower,OverCurrent):  ##Funcion para seleccionar que alertas deben ser recordadas hasta ser borradas
    
    bufferlatch = ReadFrame(Registers.Reg_Event_Configuration, 0x04)

    if(VSurge == False and VSag == False and OverPower == False and OverCurrent == False):

      bufferlatch[2] = 0x00

    elif(VSurge == False and VSag == False and OverPower == False and OverCurrent == True):

      bufferlatch[2] = 0x10

    elif(VSurge == False and VSag == False and OverPower == True and OverCurrent == False):

      bufferlatch[2] = 0x20

    elif(VSurge == False and VSag == False and OverPower == True and OverCurrent == True):

      bufferlatch[2] = 0x30

    elif(VSurge == False and VSag == True and OverPower == False and OverCurrent == False):

      bufferlatch[2] = 0x40

    elif(VSurge == False and VSag == True and OverPower == False and OverCurrent == True):

      bufferlatch[2] = 0x50

    elif(VSurge == False and VSag == True and OverPower == True and OverCurrent == False):

      bufferlatch[2] = 0x60

    elif(VSurge == False and VSag == True and OverPower == True and OverCurrent == True):

      bufferlatch[2] = 0x70

    elif(VSurge == True and VSag == False and OverPower == False and OverCurrent == False):

      bufferlatch[2] = 0x80

    elif(VSurge == True and VSag == False and OverPower == False and OverCurrent == True):

      bufferlatch[2] = 0x90

    elif(VSurge == True and VSag == False and OverPower == True and OverCurrent == False):

      bufferlatch[2] = 0xA0

    elif(VSurge == True and VSag == False and OverPower == True and OverCurrent == True):

      bufferlatch[2] = 0xB0

    elif(VSurge == True and VSag == True and OverPower == False and OverCurrent == False):

      bufferlatch[2] = 0xC0

    elif(VSurge == True and VSag == True and OverPower == False and OverCurrent == True):

      bufferlatch[2] = 0xD0

    elif(VSurge == False and VSag == False and OverPower == False and OverCurrent == False):

      bufferlatch[2] = 0xE0

    elif(VSurge == True and VSag == True and OverPower == True and OverCurrent == True):

      bufferlatch[2] = 0xF0
    
    eventdataset =[bufferlatch[2],
                   bufferlatch[3],
                   bufferlatch[4],
                   bufferlatch[5],
                  ]

    WriteFrame(Registers.Reg_Event_Configuration, eventdataset, 4)

    logging.debug('Latch de eventos realizado')
    
def ClearEvents():  ##Funcion para borrar todas las alertas

    bufferclear = ReadFrame(Registers.Reg_Event_Configuration, 0x04)

    bufferclear[3] = 0x0F

    bufferclear2   = [bufferclear[2],
                      bufferclear[3],
                      bufferclear[4],
                      bufferclear[5]
                     ]

    WriteFrame(Registers.Reg_Event_Configuration, bufferclear2, 4)
    
    print("Events Cleared")

#########################################################################################    

########################## Scan Events Function #########################################

def ScanEvents():
       
    alerts = EventsFlags()
    
    if(AlertByte == 0x0):

        alerts.NoEventFlag == True

    elif( AlertByte == 0x1 ):
        
        alerts.VSagFlag = True
        logging.warning('Alerta de Sag Voltage')
        
    elif( AlertByte == 0x2 ):
        
        alerts.VSurgeFlag = True
        logging.warning('Alerta de Surge Voltage')      
               
    elif( AlertByte == 0x4 ):
        
        alerts.OverCurrentFlag = True
        logging.warning('Alerta de SobreCorriente')
                
    elif( AlertByte == 0x5 ):
        
        alerts.VSagFlag = True
        alerts.OverCurrentFlag = True
        logging.warning('Alerta de Sag Voltage, SobreCorriente')
            
    elif( AlertByte == 0x6 ):
        
        alerts.VSurgeFlag = True
        alerts.OverCurrentFlag = True
        logging.warning('Alerta de Surge Voltage, SobreCorriente')
              
    elif( AlertByte == 0x8 ):
        
        alerts.OverPowerFlag = True
        logging.warning('Alerta de SobreCarga')
        
    elif( AlertByte == 0x9 ):
        
        alerts.VSagFlag = True
        alerts.OverPowerFlag = True
        logging.warning('Alerta de Sag Voltage, SobreCarga')
              
    elif( AlertByte == 0xA ):
        
        alerts.OverPowerFlag = True
        alerts.VSurgeFlag = True
        logging.warning('Alerta de SobreCarga, Surge Voltage')
           
    elif( AlertByte == 0xC ):
        
        alerts.OverPowerFlag = True
        alerts.OverCurrentFlag = True
        logging.warning('Alerta de SobreCarga, SobreCorriente')   
             
    elif( AlertByte == 0xD ):
        
        alerts.OverPowerFlag = True
        alerts.OverCurrentFlag = True
        alerts.VSagFlag = True
        logging.warning('Alerta de SobreCarga, SobreCorriente, Sag Voltage')
        
    elif( AlertByte == 0xE ): 
        
        alerts.OverPowerFlag = True
        alerts.OverCurrentFlag = True
        alerts.VSurgeFlag = True
        logging.warning('Alerta de SobreCarga, SobreCorriente, Surge Voltage')
        

    AlertsList = [alerts.VSagFlag, 
                  alerts.VSurgeFlag,
                  alerts.OverCurrentFlag,
                  alerts.OverPowerFlag,
                  alerts.NoEventFlag
                 ]
                 
    return(AlertsList)

#################################################################################

def GetValues():

  global ValuesList
  global AlertByte
  global AlertLatch

  buffervalues = ReadFrame(Registers.Reg_Voltage_RMS, 0x18)
  bufferaccum = ReadFrame(Registers.Reg_Import_Active , 0x20)
  bufferalerts = ReadFrame(Registers.Reg_System_Status, 0x02)

  AlertByte = bufferalerts[2] & 0xF
  AlertLatch = (bufferalerts[3] & 0x7) >> 2

  pfRaw = ( buffervalues[9] << 8 | buffervalues[8] )
  f = ((pfRaw & 0x8000) >> 15) * -1.0

  for ch in range (14,3,-1):

    f += ((pfRaw & (1 << ch)) >> ch) * 1.0 / (1 << (15 - ch))

  # print ("Factor de potencia: ",f)

  # print(bufferalerts)
  # print(AlertByte)
  # print(AlertLatch)

  Measurement = Values()
  EnergyAccum = EnergyCounters()
  alerts = EventsFlags()

  try:

    if(buffervalues[0] == 0x06 and bufferaccum[0] == 0x06 and bufferalerts[0] == 0x06):

      Measurement.VoltageRMS   = round( ( buffervalues[3] << 8 | buffervalues[2]  ) * 0.01 , 2)
      Measurement.Frequency    = round( ( buffervalues[5] << 8 | buffervalues[4]  ) * 0.001 , 2)
      Measurement.Temperature  = round(  ( ( (buffervalues[7] << 8 | buffervalues[6]) * (3.3/1023.0) - 0.5 ) / 0.01 ) ,2)
      Measurement.PowerFactor  = round( f , 2)
      Measurement.CurrentRMS   = round( ( buffervalues[13] << 24 | buffervalues[12] << 16 | buffervalues[11] << 8 | buffervalues[10] ) * 0.01 , 2)
      Measurement.ActivePower  = round( ( buffervalues[17] << 24 | buffervalues[16] << 16 | buffervalues[15] << 8 | buffervalues[14] ) * 0.01 , 2)
      Measurement.ReactivePower= round( ( buffervalues[21] << 24 | buffervalues[20] << 16 | buffervalues[19] << 8 | buffervalues[18] ) * 0.01 , 2)
      Measurement.AppareantPower=round( ( buffervalues[25] << 24 | buffervalues[24] << 16 | buffervalues[23] << 8 | buffervalues[22] ) * 0.1 , 2)

      EnergyAccum.ImportActivePowerCounter = round( ( bufferaccum[9] << 56 | bufferaccum[8] << 48 | bufferaccum[7] << 40 | bufferaccum[6] << 32 | bufferaccum[5] << 24 | bufferaccum[4] << 16 | bufferaccum[3] << 8
           | bufferaccum[2] ) * 0.000001 , 2 )
      EnergyAccum.ImportReactivePowerCounter = round( ( bufferaccum[17] << 56 | bufferaccum[16] << 48 | bufferaccum[15] << 40 | bufferaccum[14] << 32 | bufferaccum[13] << 24 | bufferaccum[12] << 16 | bufferaccum[11] << 8
           | bufferaccum[2] ) * 0.000001 , 3 )    
      EnergyAccum.ExportActivePowerCounter = round( ( bufferaccum[25] << 56 | bufferaccum[24] << 48 | bufferaccum[23] << 40 | bufferaccum[22] << 32 | bufferaccum[21] << 24 | bufferaccum[20] << 16 | bufferaccum[19] << 8
           | bufferaccum[18] ) * 0.000001 , 3 )    
      EnergyAccum.ExportReactivePowerCounter = round( ( bufferaccum[33] << 56 | bufferaccum[32] << 48 | bufferaccum[31] << 40 | bufferaccum[30] << 32 | bufferaccum[29] << 24 | bufferaccum[28] << 16 | bufferaccum[27] << 8
           | bufferaccum[26] ) * 0.000001 , 3 )

      ValuesList = [Measurement.VoltageRMS,
      Measurement.CurrentRMS,
      Measurement.ActivePower,
      Measurement.ReactivePower,
      Measurement.AppareantPower,
      Measurement.Frequency,
      Measurement.Temperature,
      Measurement.PowerFactor,
      EnergyAccum.ImportActivePowerCounter,
      EnergyAccum.ImportReactivePowerCounter
      ]

      #print(ValuesList)

      # print("Voltaje = {} V  Corriente = {} A  Potencia Activa = {} W  Potencia Reactiva = {} VAr  Potencia Aparente = {} VA  Frecuencia = {} Hz  Temperatura = {} Grados Potencia Consumida = {} KWh"
      #       .format (Measurement.VoltageRMS , Measurement.CurrentRMS , Measurement.ActivePower , Measurement.ReactivePower , Measurement.AppareantPower , Measurement.Frequency, Measurement.Temperature, EnergyAccum.ImportActivePowerCounter) )

      # print( buffervalues[7] << 8 | buffervalues[6])
    
    return ValuesList, ValuesList[7], ValuesList[8]

  except Exception as e:

    print("Se ha producido error de tipo: {}".format( type(e).__name__ ) )

def SumValues():

    global SumValues

    #Val,PWRAccum_Active,PWRAccum_React = GetValues()

    for i in range(0,7):
    
        ValuesSum[i].append(ValuesList[i])

    ValuesSum[8] = ValuesList[8]
    ValuesSum[9] = ValuesList[9]

    #print(ValuesSum)

    return ValuesSum
       
#SetCalibrationValues(11400, 1160, 13224, 50000)
        
# SaveToFlash()
# SaveEnergyCounters()
# AutoCalibrationGain()
# AutoCalibrationReactive()
# AutoCalibrationFrequency()

#LatchEvents(False,False,True,False)

#ClearEvents()

#GetValues()

# ScanEvents()

#SetEventsLimits("105.52","140.00","1.80","220.00")