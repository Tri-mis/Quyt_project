from ctypes import *
from enum import IntEnum


# -----------------------
# Constant
# -----------------------
NNO_STATUS_SCAN_IN_PROGRESS = 0x00000002


# -----------------------
# Enum
# -----------------------
class NANOAPI_ERR_CODE:
    NANOAPI_PASS = 0
    NANOAPI_ERR_FAIL = -1
    NANOAPI_ERR_NNO_CMD_NACK = -2
    NANOAPI_ERR_NNO_CMD_BUSY = -3
    NANOAPI_ERR_NNO_READ_TIMEOUT = -4


class NNO_FILE_TYPE:
    NNO_FILE_SCAN_DATA          = c_int(0)
    NNO_FILE_SCAN_CONFIG        = c_int(1)
    NNO_FILE_REF_CAL_DATA       = c_int(2)
    NNO_FILE_REF_CAL_MATRIX     = c_int(3)
    NNO_FILE_HADSNR_DATA        = c_int(4)
    NNO_FILE_SCAN_CONFIG_LIST   = c_int(5)
    NNO_FILE_SCAN_LIST          = c_int(6)
    NNO_FILE_SCAN_DATA_FROM_SD  = c_int(7)
    NNO_FILE_INTERPRET_DATA     = c_int(8)
    NNO_FILE_MAX_TYPES          = c_int(9)

