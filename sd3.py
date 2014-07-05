# import re,os,shutil,sys,time,xlrd
import ssdt_python,sys,os,time,glob,shlex,subprocess
sys.path.append('/home/yoxu/sc/lib')

from lib import *
from optparse import OptionParser
import socket

def __ProcessCommandLine():
    parser = OptionParser()

    parser.add_option("--bl", "--buildlabel", dest="buildlabel",
                  help="Fill in build label format like e77 if you wanna cli version input e77c")
    parser.add_option("--bn", "--buildno", dest="buildno",
                  help="Fill in build number")

    parser.add_option("--s", "--serial", dest="serial",default=None,
                  help="Fill in serial number")
    parser.add_option("--c", "--config", dest="config",
                  help="Fill in config")

    parser.add_option("--e", "--end", dest="endnumber",default='01',
                  help="serialNumber end number. Default is 01 ")

    parser.add_option("--f", "--fd", dest="fd",default='y',
                  help="y. force download n. normal download ")

    parser.add_option("--so", "--serialouput", dest="serialouput",default=2,type=int,
                  help="Enable maximum serial output 0. no change 1. disable 2.* enable ")

    parser.add_option("--cdu", dest="cduenable",default=1,type=int,
                  help="Enable the cdu of this config 1.* disable 2. enable")

    parser.add_option("--wp", dest="wp",default=2,type=int,
                  help="Enable the wp option of this config 0. disable 1. enable 2.* None")
    parser.add_option("--l", dest="lifeinseconds",default=0,type=int,
                  help="Enable lifeinseconds option of this drive 0*. 0 1. customized by input ")
    parser.add_option("--d", dest="double",default=0,type=int,
                  help="Enable double size, 0.* default disable 1. customized capacity by input, 200 or 400 ")
    parser.add_option("--m", dest="misc_enable",default=2,type=int,
                  help="Enable misc feature 0.no change 1. disable 2.* enable ")
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
    path = '/mnt/ssdt/scratch/'
    full_path_cdu = path+''+str(configid)+'.bin'
    cdupath=glob.glob(full_path_cdu)
    returncode = 0
    if cdupath == []:
        print "no found cdu,skip"
    else:
        cdu = 'ConfigDriveUnique.py --cduimagefilename='+full_path_cdu+''
        print cdu
        #os.system(cdu)
        returncode = execute_command(cdu)
    return returncode


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

def cdu_dlc(dlc_enable):

    import SATA
    import SATA.Device
    import SATA.Diagnostics
    import SATA.ConfigDriveUniqueData

    if dlc_enable != 0:
        device = SATA.Device.Device.FindSandForceDevice()
        if device is not None:
            SATA.Diagnostics.UnlockCustomerFirstAttemptSuccess(device)
            cduClass = SATA.ConfigDriveUniqueData.ConfigDriveUniqueData(device)
            cduClass.DlcControl.DlcControl = dlc_enable
            cduClass.NcqTrimControl.NcqTrimControl = dlc_enable
            cduClass.Write()
            device.StandbyImmediate()
    else:
        pass

    if device is not None:
        ssdt_python.UnSelectHBA(0)

def cdu_miscfeature(misc_enable):

    import SATA
    import SATA.Device
    import SATA.Diagnostics
    import SATA.ConfigDriveUniqueData

    if misc_enable != 0:
        device = SATA.Device.Device.FindSandForceDevice()
        if device is not None:
            SATA.Diagnostics.UnlockCustomerFirstAttemptSuccess(device)
            cduClass = SATA.ConfigDriveUniqueData.ConfigDriveUniqueData(device)
            cduClass.MiscCustomerFeatures.MiscCustomerFeatures = misc_enable
            cduClass.Write()
            device.StandbyImmediate()
    else:
        pass

    if device is not None:
        ssdt_python.UnSelectHBA(0)

def cdu_serial_serialoutput(delay, options, serialNumber):
    if serialNumber is not None:
        cdu_serialnumber(serialNumber)

    if options.double != 0:
        cdu_dlc(2)

    cdu_miscfeature(options.misc_enable)
    cdu_serialoutput(options.serialouput)
    #     cdu_command += ' --serialnumber='+serialNumber+' --serialoutputcontrol='+str(options.serialouput) +''
    # else:
    #     cdu_command += ' --serialoutputcontrol='+str(options.serialouput) +''

    #os.system(cdu_command)

    #Powercycle(delay)
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

def getserial():
    cmd = 'hostname --s'
    hostname = socket.gethostname().split('.')[0]
    if stations[hostname] == 'NA':
        return None
    else:
        return stations[hostname]

def execute_command(cmdstring, cwd=None, timeout=None, shell=False):
    if shell:
        cmdstring_list = cmdstring
    else:
        cmdstring_list = shlex.split(cmdstring)
    if timeout:
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    sub = subprocess.Popen(cmdstring_list, cwd=cwd, stdin=subprocess.PIPE,shell=shell,bufsize=4096)
    while sub.poll() is None:
        time.sleep(0.1)
        if timeout:
            if end_time <= datetime.datetime.now():
                raise Exception(" time out")
    print str(sub.returncode)
    return str(sub.returncode)

if __name__ == "__main__":

    options = __ProcessCommandLine()

    build_location = os.environ.get("SSDT_FIRMWARE_ROOT", None)
    full_dir_build_location = build_location+'/builds/'

    build=None
    smart_download_command=None
    serialNumber=None
    delay=15
    returncode = 0

    if options.fd == 'y':
        #pass
        os.system("ForceDownLoad.py --u=0 --p=0 --force")
    if options.buildlabel is not None : #convert build label to build no
        print "Convert build label to build no"

        build=getbuildno(full_dir_build_location,getbuildlabel(options.buildlabel))

    elif options.buildno is not None:
        build=options.buildno

    if build is not None:
        print "get build %s" %build
        if options.serial is not None:
            serialNumber = options.serial
        else:
            serialNumber = getserial()
        if serialNumber is not None:
            smart_download_command='SmartDownload.py --fd='+options.fd+' --build='+build+\
            ' --serialnumber='+serialNumber+' --setserialnumber='+serialNumber+''
            configid = SerialnumberToConfigID(serialNumber)
            if str(configid) in ["33185","33134"]:
                topfile_location = '/mnt/ssdt/scratch/topfile/'+str(configid)+'.txt'
                smart_download_command = smart_download_command +' --topofile='+topfile_location+''
        else:
            raise Exception("can't get serial number, need to input")

    if smart_download_command is not None:
        if serialNumber in ['602006157001'] :
            smart_download_command = smart_download_command+' --writeprotectcircuit=0'
        elif options.wp != 2 :
            smart_download_command = smart_download_command+' --writeprotectcircuit='+str(options.wp)+''
        if options.lifeinseconds != 0:
            smart_download_command = smart_download_command+' --lifeinseconds='+str(options.lifeinseconds)+''
        if options.double != 0:
            smart_download_command = smart_download_command+' --supportdlc=1 --setdoublesize='+str(options.double)+''
    else:
        raise Exception(" can't get smart download command")

    print smart_download_command
    time.sleep(delay)
    #os.system(smart_download_command)
    returncode += int(execute_command(smart_download_command))

    time.sleep(delay)
    # try:
    returncode += int(cdu(configid))
    # except:
    #     raise Exception(" error occured during download cdu image")
    cdu = 'ConfigDriveUnique.py --serialoutputcontrol=2 --misccustomerfeatures=2'

    if options.double != 0:
        cdu += ' --dlccontrol=2 --ncqtrimcontrol=2 ' 
    time.sleep(delay)
    #os.system(cdu)
    returncode += int(execute_command(cdu))
    # print returncode
    #return returncode