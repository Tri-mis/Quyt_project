from ctypes import *

# -----------------------
# Constants
# -----------------------
CUR_SCANDATA_VERSION = 1
SLEW_SCAN_MAX_SECTIONS = 5
SCAN_CFG_FILENAME_LEN = 40
NANO_SER_NUM_LEN = 8
SCAN_NAME_LEN = 20
ADC_DATA_LEN = 864

PX_TO_LAMBDA_NUM_POL_COEFF = 3

NUM_PIXEL_NM_COEFFS = PX_TO_LAMBDA_NUM_POL_COEFF
NUM_SHIFT_VECTOR_COEFFS = PX_TO_LAMBDA_NUM_POL_COEFF

# -----------------------
# Enums (ctypes equivalents)
# -----------------------
class DLPSPEC_ERR_CODE:
    DLPSPEC_PASS                   =   0
    ERR_DLPSPEC_FAIL               =  -1
    ERR_DLPSPEC_INVALID_INPUT      =  -2
    ERR_DLPSPEC_INSUFFICIENT_MEM   =  -3
    ERR_DLPSPEC_TPL                =  -4
    ERR_DLPSPEC_ILLEGAL_SCAN_TYPE  =  -5
    ERR_DLPSPEC_NULL_POINTER       =  -6

class SCAN_TYPES:
    COLUMN_TYPE     = 0
    HADAMARD_TYPE   = 1
    SLEW_TYPE		= 2

# -----------------------
# Structs (ctypes equivalents)
# -----------------------

class CalibCoeffs(Structure):
    _fields_ = [
        ("ShiftVectorCoeffs", c_double * NUM_SHIFT_VECTOR_COEFFS),
        ("PixelToWavelengthCoeffs", c_double * NUM_PIXEL_NM_COEFFS),
    ]

class FrameBufferDescriptor(Structure):
    _fields_ = [
        ("frameBuffer", POINTER(c_uint32)),  # pointer to start of frame buffer
        ("numFBs", c_uint32),                # number of consecutive buffers
        ("width", c_uint32),                 # horizontal pixels
        ("height", c_uint32),                # vertical pixels
        ("bpp", c_uint32),                   # bits per pixel
    ]

class ScanConfig(Structure):
    """
    Corresponds to typedef struct { SCAN_CONFIG_HEAD SCAN_CONFIG_STUB } scanConfig;
    """
    _fields_ = [
        # SCAN_CONFIG_HEAD
        ("scan_type", c_uint8),
        ("scanConfigIndex", c_uint16),
        ("ScanConfig_serial_number", c_char * NANO_SER_NUM_LEN),
        ("config_name", c_char * SCAN_CFG_FILENAME_LEN),

        # SCAN_CONFIG_STUB
        ("wavelength_start_nm", c_uint16),
        ("wavelength_end_nm", c_uint16),
        ("width_px", c_uint8),
        ("num_patterns", c_uint16),
        ("num_repeats", c_uint16),
    ]

class SlewScanSection(Structure):
    _fields_ = [
        ("section_scan_type", c_uint8),
        ("width_px", c_uint8),
        ("wavelength_start_nm", c_uint16),
        ("wavelength_end_nm", c_uint16),
        ("num_patterns", c_uint16),
        ("exposure_time", c_uint16),  # should match EXP_TIME values
    ]

class SlewScanConfigHead(Structure):
    _fields_ = [
        # SCAN_CONFIG_HEAD (expanded)
        ("scan_type", c_uint8),
        ("scanConfigIndex", c_uint16),
        ("ScanConfig_serial_number", c_char * NANO_SER_NUM_LEN),
        ("config_name", c_char * SCAN_CFG_FILENAME_LEN),
        ("num_repeats", c_uint16),
        ("num_sections", c_uint8),
    ]

class SlewScanConfig(Structure):
    _fields_ = [
        ("head", SlewScanConfigHead),
        ("section", SlewScanSection * SLEW_SCAN_MAX_SECTIONS),
    ]

class UScanConfig(Union):
    _fields_ = [
        ("scanCfg", ScanConfig),
        ("slewScanCfg", SlewScanConfig),
    ]

class DateTimeStruct(Structure):
    _fields_ = [
        ("year", c_uint8),        # years since 2000
        ("month", c_uint8),       # months since January [0-11]
        ("day", c_uint8),         # day of month [1-31]
        ("day_of_week", c_uint8), # days since Sunday [0-6]
        ("hour", c_uint8),        # hours since midnight [0-23]
        ("minute", c_uint8),      # minutes after the hour [0-59]
        ("second", c_uint8),      # seconds after the minute [0-60]
    ]

class ScanData(Structure):
    _fields_ = [
        # SCAN_DATA_VERSION
        ("header_version", c_uint32),

        # SCAN_DATA_HEAD_NAME
        ("scan_name", c_char * SCAN_NAME_LEN),

        # DATE_TIME_STRUCT (expanded)
        ("year", c_uint8),
        ("month", c_uint8),
        ("day", c_uint8),
        ("day_of_week", c_uint8),
        ("hour", c_uint8),
        ("minute", c_uint8),
        ("second", c_uint8),

        # SCAN_DATA_HEAD_BODY
        ("system_temp_hundredths", c_int16),
        ("detector_temp_hundredths", c_int16),
        ("humidity_hundredths", c_uint16),
        ("lamp_pd", c_uint16),
        ("scanDataIndex", c_uint32),
        ("calibration_coeffs", CalibCoeffs),
        ("serial_number", c_char * NANO_SER_NUM_LEN),
        ("adc_data_length", c_uint16),
        ("black_pattern_first", c_uint8),
        ("black_pattern_period", c_uint8),
        ("pga", c_uint8),

        # SCAN_CONFIG_HEAD (embedded again)
        ("scan_type", c_uint8),
        ("scanConfigIndex", c_uint16),
        ("ScanConfig_serial_number", c_char * NANO_SER_NUM_LEN),
        ("config_name", c_char * SCAN_CFG_FILENAME_LEN),

        # SCAN_CONFIG_STUB (embedded again)
        ("wavelength_start_nm", c_uint16),
        ("wavelength_end_nm", c_uint16),
        ("width_px", c_uint8),
        ("num_patterns", c_uint16),
        ("num_repeats", c_uint16),

        # adc_data
        ("adc_data", c_int32 * ADC_DATA_LEN),
    ]

class SlewScanData(Structure):
    _fields_ = [
        # SCAN_DATA_VERSION
        ("header_version", c_uint32),

        # SCAN_DATA_HEAD_NAME
        ("scan_name", c_char * SCAN_NAME_LEN),

        # DATE_TIME_STRUCT
        ("year", c_uint8),
        ("month", c_uint8),
        ("day", c_uint8),
        ("day_of_week", c_uint8),
        ("hour", c_uint8),
        ("minute", c_uint8),
        ("second", c_uint8),

        # SCAN_DATA_HEAD_BODY
        ("system_temp_hundredths", c_int16),
        ("detector_temp_hundredths", c_int16),
        ("humidity_hundredths", c_uint16),
        ("lamp_pd", c_uint16),
        ("scanDataIndex", c_uint32),
        ("calibration_coeffs", CalibCoeffs),
        ("serial_number", c_char * NANO_SER_NUM_LEN),
        ("adc_data_length", c_uint16),
        ("black_pattern_first", c_uint8),
        ("black_pattern_period", c_uint8),
        ("pga", c_uint8),

        # slewCfg
        ("slewCfg", SlewScanConfig),

        # adc_data
        ("adc_data", c_int32 * ADC_DATA_LEN),
    ]

class UScanData(Union):
    _fields_ = [
        ("data", ScanData),
        ("slew_data", SlewScanData),
    ]

class ScanResults(Structure):
    _fields_ = [
        # SCAN_DATA_VERSION
        ("header_version", c_uint32),

        # SCAN_DATA_HEAD_NAME
        ("scan_name", c_char * SCAN_NAME_LEN),

        # DATE_TIME_STRUCT
        ("year", c_uint8),
        ("month", c_uint8),
        ("day", c_uint8),
        ("day_of_week", c_uint8),
        ("hour", c_uint8),
        ("minute", c_uint8),
        ("second", c_uint8),

        # SCAN_DATA_HEAD_BODY
        ("system_temp_hundredths", c_int16),
        ("detector_temp_hundredths", c_int16),
        ("humidity_hundredths", c_uint16),
        ("lamp_pd", c_uint16),
        ("scanDataIndex", c_uint32),
        ("calibration_coeffs", CalibCoeffs),
        ("serial_number", c_char * NANO_SER_NUM_LEN),
        ("adc_data_length", c_uint16),
        ("black_pattern_first", c_uint8),
        ("black_pattern_period", c_uint8),
        ("pga", c_uint8),

        # cfg (used for interpreting results)
        ("cfg", SlewScanConfig),

        # computed results
        ("wavelength", c_double * ADC_DATA_LEN),
        ("intensity", c_int * ADC_DATA_LEN),
        ("length", c_int),
    ]












