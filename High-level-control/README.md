# 🍊 Citrus Sorting App

This document provides instructions on the project structure, build process, and execution of the Citrus Sorting App.

---

## 📋 Prerequisites

To build and develop the application, you will need:
* **Python 3.11** (the required version is specified in `pyproject.toml`)
* All Python libraries listed in `requirements.txt`.

---

## 📂 Project Structure

A brief overview of the key files and directories:

* `CitrusSortingApp.py`: The main entry point for the application.
* `CitrusSortingApp.spec`: The PyInstaller specification file used to build the `.exe`.
* `requirements.txt`: A list of required Python libraries.
* `pyproject.toml`: Project metadata, including the specific Python 3.11 version.
* `libs/`: Contains essential DLLs for spectrometer communication.
    * `libdlpspec.dll`: Handles encoding/decoding of NIR Spectrometer messages.
    * `nano_api.dll`: Handles USB communication with the spectrometer.
    * `hidapi.dll`: Low-level USB communication library required by `nano_api.dll`.
* `wrappers/`: Contains Python wrappers for the DLLs.
    * `dlpspec_...py`: Wrappers for `libdlpspec.dll`.
    * `nanoapi_...py`: Wrappers for `nano_api.dll`.
    * `NIR_wrapper.py`: Defines the `NIR_SPECTROMETER` class, which is the final object used to control the spectrometer.
* `models/`: Contains the machine learning models.
    * `citrus_brix_model.pkl`: The stacking ridge model for brix prediction.
    * `citrus_brix_scaler.pkl`: The scaler used for preprocessing data.
* `presets/`: Contains configuration and reference data.
    * `presets.txt`: App configuration loaded on startup and updated at runtime. (This may not exist yet)
    * `reference_scan_result.csv`: The reference whiteout scan (wavelengths 900-1700nm, single row, no headers).

---

## 🛠️ How to Build the Application (.exe)

Follow these steps to build the executable from the source code:

1.  **Create Virtual Environment**: Create a virtual environment using Python 3.11.
    ```bash
    python -m venv venv
    ```

2.  **Activate Environment**:
    * **Windows**: `.\venv\Scripts\activate`
    * **macOS/Linux**: `source venv/bin/activate`

3.  **Install Dependencies**: Install all required libraries.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run PyInstaller**: Run the PyInstaller build command from the project's root folder (the same directory as the `.spec` file).
    ```bash
    pyinstaller CitrusSortingApp.spec
    ```

5.  **Find Executable**: This process will generate `build/` and `dist/` folders. Your final application is located at `dist/CitrusSortingApp.exe`.

---

## 🏃 How to Run the Application

The executable **depends on the relative paths** to the `models/` and `presets/` folders.

1.  Create a new folder for your application (e.g., `C:\CitrusApp`).
2.  Copy the `CitrusSortingApp.exe` from the `dist/` folder into your new folder.
3.  Copy the **entire** `models/` folder and the **entire** `presets/` folder from the project source into your new folder.

The final directory structure for running the app **must** look like this:
    /YourAppFolder
    ├─ CitrusSortingApp.exe
    ├─ models/
    │ ├─ citrus_brix_model.pkl
    │ └─ citrus_brix_scaler.pkl
    ├─ presets/
    │ ├─ presets.txt
    │ └─ reference_scan_result.csv

4.  Double-click `CitrusSortingApp.exe` to run the application.

---

## 🔬 Advanced: Generating a New Reference Scan

The `reference_scan_result.csv` is a crucial file for calculating reflectance. If you need to generate a new one, you have two options:

### Method 1: Manual (Using Manufacturer GUI)

1.  Use the NIR spectrometer's official GUI software to perform a scan with whiteout reflectance.
2.  Export the scan result.
3.  Reformat the data into a CSV file containing **two rows** of data corresponding to wavelengths 900nm to 1700nm and their intensities
4.  Replace the old `presets/reference_scan_result.csv` with your new file.

### Method 2: Using the Python Script

This method requires the **source code** (specifically the `wrappers/` and `presets/` folders).

1.  Ensure your development environment is set up (with `wrappers/` and `presets/` in the same project folder).
2.  Prepare the spectrometer and sensor for a whiteout reflectance scan.
3.  Create a new Python script (e.g., `get_ref_scan.py`) in the **root** of your project (at the same level as the `wrappers/` folder).
4.  Add the following code to the script:

    ```python
    from wrappers.NIR_wrapper import NIR_SPECTROMETER

    # Initialize the spectrometer
    nir = NIR_SPECTROMETER()
    
    # Connect to the device
    nir.start_USB_communication()
    
    # Perform the scan and save the result
    nir.perform_ref_cal_scan()
    
    print("Reference scan complete. File saved to presets/reference_scan_result.csv")
    ```

5.  Run the script from your activated virtual environment:
    ```bash
    python get_ref_scan.py
    ```
6.  This will automatically perform the scan and overwrite the `presets/reference_scan_result.csv` file.

---

## ⚠️ Important Notes

* **Output Folder**: On its first run, `CitrusSortingApp.exe` will create an `output/` folder in its own directory (if it doesn't already exist).
* **Presets File**: The app loads settings from `presets.txt` on startup. If this file is missing, the app will create a new one, setting the default `save_data_path` to the `output/` folder. This file is updated during runtime.
* **Runtime vs. Development**: The `libs/` and `wrappers/` folders are **NOT** required for the built `CitrusSortingApp.exe` to run. They are bundled into the executable by PyInstaller. You only need them for development or for running the reference scan script.