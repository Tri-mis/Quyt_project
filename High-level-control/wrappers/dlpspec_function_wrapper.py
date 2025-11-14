from ctypes import *
from .dlpspec_type_wrapper import *
import os


# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the DLL
dll_path = os.path.join(script_dir, r"..\libs\libdlpspec.dll")

# Load it
dll = cdll.LoadLibrary(dll_path)

# =========================== HELPER FUNCTION ===========================
def dlpspec_print_error_code(function_name: str, ret: int):
    for name, value in DLPSPEC_ERR_CODE.__dict__.items():
        if not name.startswith("__") and value == ret:
            print(f"{function_name} FAILED - ERROR: {name}")
            return

# =========================== dlpspec_get_scan_config_dump_size ===========================

dll.dlpspec_get_scan_config_dump_size.argtypes = [POINTER(UScanConfig), POINTER(c_size_t)]
dll.dlpspec_get_scan_config_dump_size.restype = c_int

def dlpspec_get_scan_config_dump_size(scan_cfg_ptr, dump_size_ptr):

    if not isinstance(scan_cfg_ptr, POINTER(UScanConfig)):
        raise TypeError(f"scan_cfg_ptr must be POINTER(UScanConfig), got {type(scan_cfg_ptr)}")
    if not isinstance(dump_size_ptr, POINTER(c_size_t)):
        raise TypeError(f"dump_size_ptr must be POINTER(c_size_t), got {type(dump_size_ptr)}")

    ret = dll.dlpspec_get_scan_config_dump_size(scan_cfg_ptr, dump_size_ptr)

    if ret < 0:
        dlpspec_print_error_code("dlpspec_get_scan_config_dump_size", ret)

# =========================== dlpspec_scan_write_configuration ===========================

dll.dlpspec_scan_write_configuration.argtypes = [POINTER(UScanConfig), c_void_p, c_size_t]
dll.dlpspec_scan_write_configuration.restype = c_int

def dlpspec_scan_write_configuration(scan_cfg_ptr, buf_ptr, buf_size):

    if not isinstance(scan_cfg_ptr, POINTER(UScanConfig)):
        raise TypeError(f"scan_cfg_ptr must be POINTER(UScanConfig), got {type(scan_cfg_ptr)}")
    if not isinstance(buf_ptr, c_void_p):
        raise TypeError(f"buf_ptr must be c_void_p, got {type(buf_ptr)}")
    if not isinstance(buf_size, c_size_t):
        raise TypeError(f"buf_size must be int, got {type(buf_size)}")

    ret = dll.dlpspec_scan_write_configuration(scan_cfg_ptr, buf_ptr, buf_size)

    if ret < 0:
        dlpspec_print_error_code("dlpspec_scan_write_configuration",ret)

# =========================== dlpspec_scan_read_configuration ===========================

dll.dlpspec_scan_read_configuration.argtypes = [c_void_p, c_size_t]
dll.dlpspec_scan_read_configuration.restype = c_int

def dlpspec_scan_read_configuration(buf_ptr, buf_size):

    if not isinstance(buf_ptr, c_void_p):
        raise TypeError(f"buf_ptr must be c_void_p, got {type(buf_ptr)}")
    if not isinstance(buf_size, c_size_t):
        raise TypeError(f"buf_size must be int, got {type(buf_size)}")

    ret = dll.dlpspec_scan_read_configuration(buf_ptr, buf_size)

    if ret < 0:
        dlpspec_print_error_code("dlpspec_scan_read_configuration",ret)

# =========================== dlpspec_scan_interpret ===========================

dll.dlpspec_scan_interpret.argtypes = [c_void_p, c_size_t, POINTER(ScanResults)]
dll.dlpspec_scan_interpret.restype = c_int

def dlpspec_scan_interpret(buf_ptr, buf_size, results_ptr):

    if not isinstance(buf_ptr, c_void_p):
        raise TypeError(f"buf_ptr must be c_void_p, got {type(buf_ptr)}")
    if not isinstance(buf_size, c_size_t):
        raise TypeError(f"buf_size must be c_size_t, got {type(buf_size)}")
    if not isinstance(results_ptr, POINTER(ScanResults)):
        raise TypeError(f"results_ptr must be POINTER(ScanResults), got {type(results_ptr)}")

    ret = dll.dlpspec_scan_interpret(buf_ptr, buf_size, results_ptr)

    if ret < 0:
        dlpspec_print_error_code("dlpspec_scan_interpret",ret)
    

# =========================== dlpspec_is_slewcfgtype ===========================

dll.dlpspec_is_slewcfgtype.argtypes = [c_void_p, c_size_t]
dll.dlpspec_is_slewcfgtype.restype = c_bool

def dlpspec_is_slewcfgtype(buf_ptr, buf_size):

    if not isinstance(buf_ptr, c_void_p):
        raise TypeError(f"buf_ptr must be c_void_p, got {type(buf_ptr)}")
    if not isinstance(buf_size, c_size_t):
        raise TypeError(f"buf_size must be int, got {type(buf_size)}")

    ret = dll.dlpspec_is_slewcfgtype(buf_ptr, buf_size)
    
    return ret

# =========================== dlpspec_scan_interpReference ===========================

dll.dlpspec_scan_interpReference.argtypes = [c_void_p, c_size_t, c_void_p, c_size_t, POINTER(ScanResults), POINTER(ScanResults)]
dll.dlpspec_scan_interpReference.restype = c_int

def dlpspec_scan_interpReference(ref_cal_data_ptr, ref_cal_data_size, ref_cal_matrix_ptr, ref_cal_matrix_size, result_ptr, ref_result_ptr):
    if not isinstance(ref_cal_data_ptr, c_void_p):
        raise TypeError(f"ref_cal_data_ptr must be c_void_p, got {type(ref_cal_data_ptr)}")
    if not isinstance(ref_cal_data_size, c_size_t):
        raise TypeError(f"ref_cal_data_size must be c_size_t, got {type(ref_cal_data_size)}")
    if not isinstance(ref_cal_matrix_ptr, c_void_p):
        raise TypeError(f"ref_cal_matrix_ptr must be c_void_p, got {type(ref_cal_matrix_ptr)}")
    if not isinstance(ref_cal_matrix_size, c_size_t):
        raise TypeError(f"ref_cal_matrix_size must be c_size_t, got {type(ref_cal_matrix_size)}")
    if not isinstance(result_ptr, POINTER(ScanResults)):
        raise TypeError(f"result_ptr must be POINTER(ScanResults), got {type(result_ptr)}")
    if not isinstance(ref_result_ptr, POINTER(ScanResults)):
        raise TypeError(f"ref_result_ptr must be POINTER(ScanResults), got {type(ref_result_ptr)}")

    ret = dll.dlpspec_scan_interpReference(ref_cal_data_ptr, ref_cal_data_size,
                                           ref_cal_matrix_ptr, ref_cal_matrix_size,
                                           result_ptr, ref_result_ptr)

    if ret < 0:
        dlpspec_print_error_code("dlpspec_scan_interpReference", ret)