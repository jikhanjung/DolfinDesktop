import sys
from cx_Freeze import setup, Executable

dist_dir = 

numpy_core_dir = os.path.join(dist_dir, 'lib', 'numpy', 'core')
for file_name in os.listdir(numpy_core_dir):
    if file_name.lower().endswith('.dll'):
        file_path = os.path.join(numpy_core_dir, file_name)
        os.remove(file_path)

setup(name = "DolfinDetector",
      version = "0.0.2",
      description = "Dolfin Detector",
      executables = [Executable("DolfinDetector.py")])

    