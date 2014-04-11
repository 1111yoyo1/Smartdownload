# import re,os,shutil,sys,time,xlrd
import ssdt_python,sys,os,time,glob
from lib import *
from optparse import OptionParser

def __ProcessCommandLine():
    parser = OptionParser()

    parser.add_option("--bl", "--buildlabel", dest="buildlabel",
                  help="Fill in build label format like e77 if you wanna cli version input e77c")
    parser.add_option("--bn", "--buildno", dest="buildno",
                  help="Fill in build number")

    parser.add_option("--s", "--serial", dest="serial",
                  help="Fill in serial number")
    parser.add_option("--c", "--config", dest="config",
                  help="Fill in config")

    parser.add_option("--e", "--end", dest="endnumber",default='01',
                  help="serialNumber end number. Default is 01 ")

    parser.add_option("--f", "--fd", dest="fd",default='y',
                  help="y. force download n. normal download ")

    parser.add_option("--so", "--serialouput", dest="serialouput",default=2,type=int,
                  help="Enable maximum serial output 0. default (no change) 1. disable 2.* enable ")

    parser.add_option("--cdu", dest="cduenable",default=1,type=int,
                  help="Enable the cdu of this config 1.* disable 2. enable")

    parser.add_option("--wp", dest="wp",default=2,type=int,
                  help="Enable the wp option of this config 0. disable 1. enable 2.* None")
    parser.add_option("--l", dest="lifeinseconds",default=31536000,type=int,
                  help="Enable lifeinseconds option of this drive 31536000*. 31536000 1. customized by input ")
    parser.add_option("--d", dest="double",default=0,type=int,
                  help="Enable double size, 0.* default disable 1. customized capacity by input, 200 or 400 ")
    (options, args) = parser.parse_args()

    return options

def getconfig(string):
    #pattern=re.compile(r'\w*(\d{5})\w*')
    if string is not None:
        pattern=re.compile(r'\w{0,1}(\d{5})\w{0,1}')
        match=pattern.match(string)
        if match:
            configid=match.group(1)
            return configid

def cdu(configid):
    cdupath=glob.glob('/home/yoxu/SF_Genesis/*'+configid+'.bin')

    if cdupath == []:
        print "no found cdu,skip"
    else:
        import SATA.Diagnostics
        import SATA.Device
        import SATA.ConfigDriveUniqueData
        import Utilities.Log

        device = SATA.Device.Device.FindSandForceDevice()
        if device is not None:
            SATA.Diagnostics.UnlockCustomerFirstAttemptSuccess(device)
            cduClass = SATA.ConfigDriveUniqueData.ConfigDriveUniqueData(device)
            #log = Utilities.Log.StartLog(device,None)
            log = Utilities.Log.StartLog(device, None, messageFormatString=None,useXmlFormatting=False,showHeaderTrailer=False, showSsdInfo=False)
        cduClass.UpdateFromFile(str(cdupath[0]), log)
        if device is not None:
            ssdt_python.UnSelectHBA(0)


def cdu_serialnumber(serialNumber):

    import Ssd.Ata
    import Ssd.IdentifyDevice
    import Ssd.Device
    import SATA.Device
    import array
    import Ssd.SerialNumber
    import SATA.Diagnostics

    device = SATA.Device.Device.FindSandForceDevice()
    if device is not None:
        SATA.Diagnostics.UnlockCustomerFirstAttemptSuccess(device)
        readData = SATA.Diagnostics.ConfigDriveUniqueRead(device)
        length = len(readData)/512
        writeData = array.array('B', [0x00] *   512 * (length-1))
        for i in range(0,512*(length-1),1):
            writeData[i]=readData[512+i]

    while len(serialNumber) < 20:
        serialNumber += " "
    serialNumber = Ssd.SerialNumber.SerialNumber(serialNumber)       
    if serialNumber is not None:

        serialNumberOffsetInBytes = Ssd.IdentifyDevice.serialNumberOffset * 2
        serialNumberSizeInBytes   = serialNumber.requiredLength

        for currIndex in range(serialNumberSizeInBytes):
            writeData[serialNumberOffsetInBytes + currIndex] = 0xFF

        for currIndex, currData in enumerate(Ssd.Ata.ByteSwapAtaString(serialNumber)):
            writeData[512 + serialNumberOffsetInBytes + currIndex] = ord(currData)

    SATA.Diagnostics.ConfigDriveUniqueWrite(device, writeData)
    if device is not None:
        ssdt_python.UnSelectHBA(0)

def cdu_serialoutput(serialouput):

    import Ssd.Ata
    import Ssd.IdentifyDevice
    import Ssd.Device
    import SATA.Device
    import array
    import Ssd.SerialNumber
    import SATA.Diagnostics

    device = SATA.Device.Device.FindSandForceDevice()
    if device is not None:
        SATA.Diagnostics.UnlockCustomerFirstAttemptSuccess(device)
        readData = SATA.Diagnostics.ConfigDriveUniqueRead(device)
        length = len(readData)/512
        writeData = array.array('B', [0x00] * 512 * (length-1))
        for i in range(0,512*(length-1),1):
            writeData[i]=readData[512+i]

    if serialouput == 2:
        configDriveUniqueFlags = writeData[514*2+1]*256+writeData[514*2]
        configDriveUniqueFlags = configDriveUniqueFlags & 0xFFE7
        configDriveUniqueFlags = configDriveUniqueFlags | ((serialouput & 0x03) << 3)
        writeData[514*2]   = configDriveUniqueFlags & 0xFF
        writeData[514*2+1] = (configDriveUniqueFlags >> 8)& 0xFF

    SATA.Diagnostics.ConfigDriveUniqueWrite(device, writeData)
    if device is not None:
        ssdt_python.UnSelectHBA(0)

def cdu_serial_serialoutput(delay, options, configid, serialNumber):
    if configid is not None:
        real_config = configid
    else:
        real_config = options.config
        time.sleep(delay)

    if real_config is not None and options.cduenable == 2:
        cdu(real_config)
        # if cdu(real_config):
        #     Powercycle(delay)
    #cdu_command = 'ConfigDriveUnique.py '
    if getconfig(real_config) is not None:
        serialNumber=configIDtoSerialnumber(getconfig(real_config), options.endnumber)

    if serialNumber is not None:
        cdu_serialnumber(serialNumber)
    cdu_serialoutput(options.serialouput)
    #     cdu_command += ' --serialnumber='+serialNumber+' --serialoutputcontrol='+str(options.serialouput) +''
    # else:
    #     cdu_command += ' --serialoutputcontrol='+str(options.serialouput) +''

    #os.system(cdu_command)

    Powercycle(delay)
    os.system('IdentifyDevice.py')

def standbyimmediate(delay):
    import SATA.Device
    time.sleep(delay)
    device = SATA.Device.Device.FindSandForceDevice()
    if device is not None:
        device.StandbyImmediate()
    if device is not None:
        ssdt_python.UnSelectHBA(0)
    
def Powercycle(delay):
    standbyimmediate(delay/2)
    time.sleep(delay/2)
    os.system('PowerOff.py')
    time.sleep(delay/2)
    os.system('PowerOn.py')
    time.sleep(delay)

if __name__ == "__main__":

    options = __ProcessCommandLine()

    build_location = os.environ.get("SSDT_FIRMWARE_ROOT", None)
    full_dir_build_location = build_location+'/builds/'

    flag_build=False

    build=None
    smart_download_command=None
    serialNumber=None
    configid=None
    delay=15

    if options.buildlabel is not None : #convert build label to build no
        print "Convert build label to build no"

        build=getbuildno(full_dir_build_location,getbuildlabel(options.buildlabel))

    elif options.buildno is not None:
        build=options.buildno

    if build is not None:
        print "get build %s" %build 

        configid = options.config

        if build is not None and configid is not None: # have config and build no
            serialNumber=configIDtoSerialnumber(configid, options.endnumber)

            if serialNumber is not None: # found serialnumber
                smart_download_command='SmartDownload.py --fd='+options.fd+' --build='+build+\
                ' --serialnumber='+serialNumber+''

            else: 
                try:                       # only have config, found master table to get op and raise

                    buildpath=glob.glob(full_dir_build_location+'*'+build+'')
                    master_table=buildpath[0]+'/'+'cfg_customer/db/PPRO_tbl_master_config.csv'
                    op_option=op_return(master_table, configid)
                    raise_option=raise_return(master_table,configid)

                    smart_download_command='SmartDownload.py --fd='+ options.fd +' --build='+ build +\
                    ' --config='+ configid +' --logicalcapacity='+ op_option +' --disableuserraise='\
                    +raise_option+'' 

                except:                     # only have config, no found master table or op and raise
                    print "no found master table use configID to download, may be not accurate"

                    smart_download_command='SmartDownload.py --fd='+options.fd+' --build='+build+\
                    ' --config='+configid+''

        elif build is not None and options.serial is not None:
            serialNumber=options.serial
            smart_download_command='SmartDownload.py --fd='+options.fd+' --build='+build+\
                ' --serialnumber='+serialNumber+''

        elif len(sys.argv) == 1:
            import SATA.Diagnostics
            import SATA.Device

            print "doing self download"
            device = SATA.Device.Device.FindSandForceDevice()

            try:
                build = str(SATA.Diagnostics.GetDriveBuildLabel(device))

            except:
                raise Exception(" no found build id, can't self download")

            import SATA.IdentifyDeviceData

            identifyDeviceData = SATA.IdentifyDeviceData.IdentifyDeviceData( device )
            serialNumber = str(identifyDeviceData.serialNumber.strip())

            if serialNumber != '1':
                smart_download_command='SmartDownload.py --build='+build+\
                ' --serialnumber='+serialNumber+''
            else:
                import TestFramework.LogData

                print "device serial number is 1, use config to get serial number"
                configidCls = TestFramework.LogData.SsdInfoData(device)
                configid = str(configidCls.getConfigIdFromDevice(device))

                if configid is not None:
                    smart_download_command='SmartDownload.py --build='+build+\
                ' --configid='+configid+''
                else:
                    raise Exception(" no found valid serialnumber and valid configID abort self download")


            wp=str(SerialnumberTowriteProtectCircuit(serialNumber))

            if device is not None:
                ssdt_python.UnSelectHBA(0) 

        if smart_download_command is not None:
            if options.wp != 2:
                smart_download_command=smart_download_command+' --writeprotectcircuit='+str(options.wp)+''
            if options.lifeinseconds != 31536000:
                smart_download_command=smart_download_command+' --lifeinseconds='+str(options.lifeinseconds)+''
            if options.double != 0:
                smart_download_command=smart_download_command+'--supportdlc=1 --setdoublesize='+str(options.double)+''
            else:
                smart_download_command=smart_download_command+' --lifeinseconds=31536000'
        else:
            raise Exception(" can't get smart download command")

        print smart_download_command
        os.system(smart_download_command)
        
        #cdu_serial_serialoutput(delay, options, configid, serialNumber)

    else:
        pass
    cdu_serial_serialoutput(delay, options, configid, serialNumber)


