# FindFQPath

Returns a fully qualified file name

Finds the current the most current version of a file. Once it's found, it will be stored in a shelf file. Future calls pull from the shelf file first, then search if the file is older than requested or missing Handy for executables that move as they are updated (such as opera.exe). At least Python uses a fully qualified name, so by using this function, the code won't need to change as the exeutable is installed in new folders

This will run slow the FIRST time a new file is requested as it is searching the entire drive. Subsequent usage for the same file will be sub-second.

Install with pip install findfqpath

Usage:\
from findfqpath import find_fq_path\
fq_path = find_fq_path("opera.exe",1)

Optional:\
Scope="Local" - Will write shelf data to the folder where the script is located (So the FIRST execution of a new script will be slow)\
Scope="Shared" - Will write shelf data to the common documents folder and be used across python scripts 
 
Sample Application:\
options = webdriver.ChromeOptions()\
options.binary_location = find_fq_path(find_file='opera.exe', num_days_valid=1)
