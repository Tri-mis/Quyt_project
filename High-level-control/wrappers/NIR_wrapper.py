from .dlpspec_function_wrapper import *
from .nanoapi_function_wrapper import *
import time
import matplotlib.pyplot as plt
import numpy as np
import csv

class NIR_SPECTROMETER:
    def __init__(self):

        # scan_config
        self.scan_config = ScanConfig(scan_type = SCAN_TYPES.HADAMARD_TYPE,
                        scanConfigIndex = 10,
                        ScanConfig_serial_number = b'C370270',
                        config_name= b'TestScan',
                        wavelength_start_nm = 900,
                        wavelength_end_nm = 1700,
                        width_px = 8,
                        num_patterns = 255,
                        num_repeats = 6)
        self.scan_result = ScanResults()
        self.pgaGain = 16

        # scan result broken down
        self.wavelength = None
        self.sample_intensity = None
        self.reflectance = None
        self.absorbance = None

        # reference calibration scan data (in bytes)
        self.ref_cal_scan = None
        self.ref_cal_scan_byte = None

        # reference calibration scan matrix (in bytes)
        self.ref_cal_matrix = None
        self.ref_cal_matrix_byte = None

        # scan result referenced
        self.ref_scan_result = ScanResults()

        # use referenced from eeprom?
        self.use_reference_from_nir_eeprom = False

    def start_USB_communication(self):
        return USB_Start()
    
    def stop_USB_communication(self):
        return USB_Stop()
  
    def perform_ref_cal_scan(self, save_reference_in_nir_eeprom = False, file_dir = None, num_repeats = 32, pgaGain = 16):

        old_pgaGain = self.pgaGain
        old_num_repeats = self.scan_config.num_repeats
        self.pgaGain = pgaGain
        self.scan_config.num_repeats = num_repeats
        if save_reference_in_nir_eeprom:

            self.perform_scan()
            NNO_UpdateRefCalDataWithWORefl()
            NNO_SaveRefCalPerformed()

            print("REFERENCE SCAN PERFORMED AND SAVED IN NIR")
        else:
            self.perform_scan()

            if file_dir == None:
                raise ValueError("File dir must not be None if reference scan saved in pc")
            filename = os.path.join(file_dir,"reference_scan_result.csv")
            wavelength = list(self.scan_result.wavelength)
            intensity = list(self.scan_result.intensity)
            
            with open(filename, "w") as f:
                f.write(",".join(str(x) for x in wavelength) + "\n")
                f.write(",".join(str(x) for x in intensity) + "\n")
                        
            print("REFERENCE SCAN PERFROMED AND SAVED IN CSV FILE")
        
        self.pgaGain = old_pgaGain
        self.scan_config.num_repeats = old_num_repeats

    def fetch_reference(self, fetch_reference_from_nir_eeprom = False, file_dir = None):

        if fetch_reference_from_nir_eeprom:

            # Read the reference calibration ScanResult struct in raw bytes
            self.ref_cal_scan_byte = c_int()
            self.ref_cal_scan_byte.value = NNO_GetFileSizeToRead(NNO_FILE_TYPE.NNO_FILE_REF_CAL_DATA)
            self.ref_cal_scan = create_string_buffer(self.ref_cal_scan_byte.value)
            self.ref_cal_scan = cast(self.ref_cal_scan, POINTER(c_ubyte))
            NNO_GetFile(self.ref_cal_scan, self.ref_cal_scan_byte)

            #Read the reference calibration matrix
            self.ref_cal_matrix_byte = c_int()
            self.ref_cal_matrix_byte.value = NNO_GetFileSizeToRead(NNO_FILE_TYPE.NNO_FILE_REF_CAL_MATRIX)
            self.ref_cal_matrix = create_string_buffer(self.ref_cal_matrix_byte.value)
            self.ref_cal_matrix = cast(self.ref_cal_matrix, POINTER(c_ubyte))
            NNO_GetFile(self.ref_cal_matrix, self.ref_cal_matrix_byte)

            self.ref_cal_scan = cast(self.ref_cal_scan, c_void_p)
            self.ref_cal_matrix = cast(self.ref_cal_matrix, c_void_p)

            self.use_reference_from_nir_eeprom = True
            print("fetch reference from nir eeprom")
        else:
            
            if file_dir == None:
                raise ValueError("File dir must not be None if reference scan saved in pc")
            filename = os.path.join(file_dir, "reference_scan_result.csv")

            try:
                with open(filename, "r", newline='') as f:
                    reader = csv.reader(f)
                    rows = list(reader)

                if len(rows) < 2:
                    raise ValueError("CSV must have at least 2 rows: wavelengths and intensities")

                # Convert strings to numbers
                wavelength_values = [float(x) for x in rows[0]]
                intensity_values = [float(x) for x in rows[1]]  # or int(x) if you saved as int

                # Fill the ScanResults arrays
                length = min(len(wavelength_values), len(self.ref_scan_result.wavelength))
                for i in range(length):
                    self.ref_scan_result.wavelength[i] = c_double(wavelength_values[i])
                    self.ref_scan_result.intensity[i] = c_int(int(intensity_values[i]))

            except FileNotFoundError:
                print(f"Error: {filename} not found. Please perform a reference scan first.")

                self.use_reference_from_nir_eeprom = False
                print("fetch reference from csv file")

    def data_cal(self):

        if self.use_reference_from_nir_eeprom:
            print("Calib with reference calibration data loaded form NIR EEPROM")
            dlpspec_scan_interpReference(self.ref_cal_scan, c_size_t(self.ref_cal_scan_byte.value),
                                        self.ref_cal_matrix, c_size_t(self.ref_cal_matrix_byte.value),
                                        pointer(self.scan_result), pointer(self.ref_scan_result))
        else:
            print("Calib with reference calibration data loaded form binary file")
        
        # Convert ctypes arrays to numpy
        self.wavelength = np.ctypeslib.as_array(self.scan_result.wavelength)
        valid_len = np.count_nonzero(self.wavelength)
        self.wavelength = self.wavelength[:valid_len]
        self.sample_intensity = np.ctypeslib.as_array(self.scan_result.intensity).astype(np.float64)[:valid_len]
        self.ref_intensity = np.ctypeslib.as_array(self.ref_scan_result.intensity).astype(np.float64)[:valid_len]

        # Compute reflectance and absorbance safely
        with np.errstate(divide='ignore', invalid='ignore'):
            self.reflectance = np.where(self.ref_intensity != 0, self.sample_intensity / self.ref_intensity, 0)
            self.absorbance = -np.log10(np.clip(self.reflectance, 1e-8, None))

    def perform_scan(self):

        # Turn to UscanConfig
        uscan_config = UScanConfig(scanCfg = self.scan_config)

        # Get the dump size
        dump_size = c_size_t()
        dlpspec_get_scan_config_dump_size(pointer(uscan_config), pointer(dump_size))

        # Create buffer with the dump size
        uscan_config_buf = create_string_buffer(dump_size.value)
        uscan_config_buf = cast(uscan_config_buf, c_void_p)

        # Serialize to the buffer
        dlpspec_scan_write_configuration(pointer(uscan_config), uscan_config_buf, dump_size)

        # ApplyScanConfig to NIR
        NNO_ApplyScanConfig(uscan_config_buf, c_int(dump_size.value))
        
        # Optionally set PGA gain
        NNO_SetFixedPGAGain(c_bool(True), c_uint8(self.pgaGain))
        
        # Get estimated time out
        estimated_scan_time = NNO_GetEstimatedScanTime() * 3
        start_scan_time = time.time() * 1000

        # PerformScan
        NNO_PerformScan(c_bool(False))

        # Oscationally check status
        status = c_uint32()
        while True:
            NNO_ReadDeviceStatus(pointer(status))
            if (status.value & NNO_STATUS_SCAN_IN_PROGRESS) != NNO_STATUS_SCAN_IN_PROGRESS:
                break
            if ((time.time() * 1000 - start_scan_time)  > estimated_scan_time):
                print("Scan failed - Timeout")
                break

        # Read the number of byte in scan data
        scan_data_byte = c_int()
        scan_data_byte.value = NNO_GetFileSizeToRead(NNO_FILE_TYPE.NNO_FILE_SCAN_DATA)

        # Read the raw data
        scan_data_buf = create_string_buffer(scan_data_byte.value)
        scan_data_buf = cast(scan_data_buf, POINTER(c_ubyte))
        NNO_GetFile(scan_data_buf, scan_data_byte)

        # Cast scan data to ScanResult struct
        self.scan_result = ScanResults()
        scan_data_buf = cast(scan_data_buf, c_void_p)
        dlpspec_scan_interpret(scan_data_buf, c_size_t(scan_data_byte.value), pointer(self.scan_result))

    def plot_result(self, plot_sample_intensity = False, plot_reflectance = False, plot_absorbance = False):
        
        if plot_sample_intensity == True:
            # --- Sample Intensity ---
            plt.figure()
            plt.plot(self.wavelength, self.sample_intensity)
            plt.title("Sample Intensity Spectrum")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Intensity (a.u.)")
            plt.grid(True)

        if plot_reflectance == True:
            # --- Reflectance ---
            plt.figure()
            plt.plot(self.wavelength, self.reflectance)
            plt.title("Reflectance Spectrum")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Reflectance")
            plt.grid(True)
        
        if plot_absorbance == True:
            # --- Absorbance ---
            plt.figure()
            plt.plot(self.wavelength, self.absorbance)
            plt.title("Absorbance Spectrum")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Absorbance (log₁₀ scale)")
            plt.grid(True)
        
        plt.show()      
