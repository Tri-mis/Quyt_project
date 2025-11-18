from ctypes import *
from .nanoapi_type_wrapper import *
import os


# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the DLL
dll_path = os.path.join(script_dir, r"..\libs\nano_api.dll")

# Load it
dll = cdll.LoadLibrary(dll_path)
# =========================== HELPER ===========================
def nano_print_error_code(function_name: str, ret: int):
    for name, value in NANOAPI_ERR_CODE.__dict__.items():
        if not name.startswith("__") and value == ret:
            print(f"{function_name} FAILED - ERROR: {name}")
            return

# =========================== USB_Start and USB_Stop ===========================
dll.USB_Init.argtypes = []
dll.USB_Init.restype = c_int
dll.USB_Open.argtypes = []
dll.USB_Open.restype = c_int
dll.USB_Close.argtypes = []
dll.USB_Close.restype = c_int
dll.USB_Exit.argtypes = []
dll.USB_Exit.restype = c_int
dll.USB_IsConnected.argtypes = []
dll.USB_IsConnected.restype = c_bool

def USB_Start():
    print (f"Init: {dll.USB_Init()}")
    print (f"Open: {dll.USB_Open()}")

    return dll.USB_IsConnected()

def USB_Stop():
    print(f"Close: {dll.USB_Close()}")
    print(f"Exit: {dll.USB_Exit()}")

    return dll.USB_IsConnected()
# =========================== NNO_ApplyScanConfig ===========================

dll.NNO_ApplyScanConfig.argtypes = [c_void_p, c_int]
dll.NNO_ApplyScanConfig.restype = c_int

def NNO_ApplyScanConfig(buf_ptr, buf_size):

    if not isinstance(buf_ptr, c_void_p):
        raise TypeError(f"buf_ptr must be c_void_p, got {type(buf_ptr)}")
    if not isinstance(buf_size, c_int):
        raise TypeError(f"buf_size must be c_int, got {type(buf_size)}")

    ret = dll.NNO_ApplyScanConfig(buf_ptr, buf_size)

    if ret < 0:
        nano_print_error_code("NNO_ApplyScanConfig", ret)

    return ret


# =========================== NNO_SetFixedPGAGain ===========================

dll.NNO_SetFixedPGAGain.argtypes = [c_bool, c_uint8]
dll.NNO_SetFixedPGAGain.restype = c_int

def NNO_SetFixedPGAGain(isFixed, gainVal):

    if not isinstance(isFixed, c_bool):
        raise TypeError(f"isFixed must be c_bool, got {type(isFixed)}")
    if not isinstance(gainVal, c_uint8):
        raise TypeError(f"gainVal must be c_uint8, got {type(gainVal)}")
    
    ret = dll.NNO_SetFixedPGAGain(isFixed, gainVal)

    if ret < 0:
        nano_print_error_code("NNO_SetFixedPGAGain", ret)
    
    return ret

# =========================== NNO_SetScanNumRepeats ===========================

dll.NNO_SetScanNumRepeats.argtypes = [c_uint16]
dll.NNO_SetScanNumRepeats.restype = c_int

def NNO_SetScanNumRepeats(num):
    
    if not isinstance(num, c_uint16):
        raise TypeError(f"num must be c_uint16, got {type(num)}")
    
    ret = dll.NNO_SetScanNumRepeats(num)

    if ret < 0:
        nano_print_error_code("NNO_SetScanNumRepeats", ret)

    return ret

# =========================== NNO_GetEstimatedScanTime ===========================

dll.NNO_GetEstimatedScanTime.argtypes = []
dll.NNO_GetEstimatedScanTime.restype = c_int

def NNO_GetEstimatedScanTime():
    
    ret = dll.NNO_GetEstimatedScanTime()

    if ret < 0:
        nano_print_error_code("NNO_GetEstimatedScanTime", ret)
        
    return ret

# =========================== NNO_PerformScan ===========================

dll.NNO_PerformScan.argtypes = [c_bool]
dll.NNO_PerformScan.restype = c_int

def NNO_PerformScan(StoreInSDCard):
    
    if not isinstance(StoreInSDCard, c_bool):
        raise TypeError(f"StoreInSDCard must be c_bool, got {type(StoreInSDCard)}")
    
    ret = dll.NNO_PerformScan(StoreInSDCard)

    if ret < 0:
        nano_print_error_code("NNO_PerformScan", ret)
    
    return ret

# =========================== NNO_ReadDeviceStatus ===========================

dll.NNO_ReadDeviceStatus.argtypes = [POINTER(c_uint32)]
dll.NNO_ReadDeviceStatus.restype = c_int

def NNO_ReadDeviceStatus(pVal):
    
    if not isinstance(pVal, POINTER(c_uint32)):
        raise TypeError(f"pVal must be POINTER(c_uint32), got {type(pVal)}")
    
    ret = dll.NNO_ReadDeviceStatus(pVal)

    if ret < 0:
        nano_print_error_code("NNO_ReadDeviceStatus", ret)
    
    return ret


# =========================== NNO_GetFileSizeToRead ===========================

dll.NNO_GetFileSizeToRead.argtypes = [c_int]
dll.NNO_GetFileSizeToRead.restype = c_int

def NNO_GetFileSizeToRead(file_type):
    if not isinstance(file_type, c_int):
        raise TypeError(f"file_type must be c_int from NNO_FILE_TYPE, got {type(file_type)}")
    
    ret = dll.NNO_GetFileSizeToRead(file_type)
    if ret < 0:
        nano_print_error_code("NNO_GetFileSizeToRead", ret)
    return ret

# =========================== NNO_GetFile ===========================

dll.NNO_GetFile.argtypes = [POINTER(c_ubyte), c_int]
dll.NNO_GetFile.restype = c_int

def NNO_GetFile(pData, size_in_bytes):

    if not isinstance(pData, (POINTER(c_ubyte))):
        raise TypeError(f"pData must be POINTER(c_ubyte), got {type(pData)}")
    if not isinstance(size_in_bytes, c_int):
        raise TypeError(f"size_in_bytes must be c_int, got {type(size_in_bytes)}")

    ret = dll.NNO_GetFile(pData, size_in_bytes)

    if ret < 0:
        nano_print_error_code("NNO_GetFile", ret)
    
    return ret


# =========================== NNO_UpdateRefCalDataWithWORefl ===========================

dll.NNO_UpdateRefCalDataWithWORefl.argtypes = []
dll.NNO_UpdateRefCalDataWithWORefl.restype = c_int

def NNO_UpdateRefCalDataWithWORefl():

    ret = dll.NNO_UpdateRefCalDataWithWORefl()

    if ret < 0:
        nano_print_error_code("NNO_UpdateRefCalDataWithWORefl", ret)

# =========================== NNO_SaveRefCalPerformed ===========================

dll.NNO_SaveRefCalPerformed.argtypes = []
dll.NNO_SaveRefCalPerformed.restype = c_int

def NNO_SaveRefCalPerformed():

    ret = dll.NNO_SaveRefCalPerformed()

    if ret < 0:
        nano_print_error_code("NNO_SaveRefCalPerformed", ret)

# =========================== NNO_DLPCEnable ===========================

dll.NNO_DLPCEnable.argtypes = [c_bool, c_bool]
dll.NNO_DLPCEnable.restype = c_int

def NNO_DLPCEnable(enable, enable_lamp):

    if not isinstance(enable, c_bool):
        raise TypeError(f"enable must be c_bool, got {type(enable)}")
    if not isinstance(enable_lamp, c_bool):
        raise TypeError(f"enable_lamp must be c_bool, got {type(enable_lamp)}")

    ret = dll.NNO_DLPCEnable(enable, enable_lamp)

    if ret < 0:
        nano_print_error_code("NNO_DLPCEnable", ret)
    
    return ret

# =========================== NNO_SetScanControlsDLPCOnOff ===========================

dll.NNO_SetScanControlsDLPCOnOff.argtypes = [c_bool]
dll.NNO_SetScanControlsDLPCOnOff.restype = c_int

def NNO_SetScanControlsDLPCOnOff(enable):

    if not isinstance(enable, c_bool):
        raise TypeError(f"enable must be c_bool, got {type(enable)}")

    ret = dll.NNO_SetScanControlsDLPCOnOff(enable)

    if ret < 0:
        nano_print_error_code("NNO_SetScanControlsDLPCOnOff", ret)
    
    return ret


# =========================== NNO_SetScanNumRepeats ===========================
dll.NNO_SetScanNumRepeats.argtypes = [c_uint16]
dll.NNO_SetScanNumRepeats.restype = c_int

def NNO_SetScanNumRepeats(num_repeats):

    if not isinstance(num_repeats, c_uint16):
        raise TypeError(f"enable must be c_uint16, got {type(num_repeats)}")

    ret = dll.NNO_SetScanNumRepeats(num_repeats)

    if ret < 0:
        nano_print_error_code("NNO_SetScanNumRepeats", ret)
    
    return ret