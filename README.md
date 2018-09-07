# FindFQPath
Returns a fully qualified file name

Finds the current the most current version of a file. Once it's found, it will be stored in a shelf file.
Future calls pull from the shelf file first, then search if the file is older than requested or missing
Handy for executables that move as they are updated (such as opera.exe).
At least Python uses a fully qualified name, so by using this function, the code won't need to change
as the exeutable is installed in new folders
