"""
Load and manipulate data from csv files created by WatchTracker.
   
"""

__version__ = "2024.10.01"
__last_edit__ = "In the process of finishing linspaceTime()..."

import numpy as np
import matplotlib.pyplot as plt
import os
import csv
from copy import deepcopy
from scipy.ndimage import median_filter
from datetime import datetime
from shutil import copy as shutil_copy
from subprocess import call

from matplotlib.ticker import MultipleLocator
#import re

DEFAULT_PATHS = []
DEFAULT_PATHS.append('/Users/Mats/Library/CloudStorage/iCloudDrive/WatchTracker')
DEFAULT_PATHS.append('/Users/matsleandersson/Library/Mobile Documents/iCloud~com~WatchTracker/Documents')
DEFAULT_PATHS.append('/Users/matlea/Library/Mobile Documents/iCloud~com~WatchTracker/Documents')

def Help():
    print("myWatchTracker\n==============")
    print("For loading, plotting, and manipulating data in WatchTracker csv files.\n")
    print("Classes")
    print("   Files()")
    print("      Returns an object with info about all files in the WatchTracker folder.")
    print("   TimingRun()")
    print("      Returns an object with timing run data and meta data from a WatchTracker csv file.")
    print("Methods")
    print("   plot()")
    print("      Plot the data in a TimingRun object. Use multiPlot() for more options.")
    print("   multiPlot()")
    print("      Plot the data in several TimingRun objects.")
    print("   concatTimingRuns()")
    print("      Concatenate data from several timing runs.")
    print("   smooth()")
    print("      Smooth an array (1d) using median_filter from scipy.")
#Help()

print(f"myWatchTracker.py version {__version__}\nlast edit: {__last_edit__}\nRun Help() for help.\n")





# ============================================================================================================
# ============================================================================================================
# ============================================================================================================
# ============================================================================================================





class TimingRun():
    def __init__(self, file_name = "_no_name_", path = "_no_path_", watch_index = -1, file_index = -1, shup = False):
        #
        self._class_type = "TimingRun"
        self._ok = False
        self._path = ""
        self._file = ""
        self._watch = ""
        self._watch_index = -1
        #
        self._time = np.array([])
        self._offset = np.array([])
        self._comment = np.array([])
        self._unix_time = np.array([])
        self._atomic_clock_error = np.array([])
        self._ios_clock_offset = np.array([])
        self._header = []
        self._other_files = []                      # this keeps a list of other timing files associated with the particular watch
        #
        self._point_index = 0
        #
        self._offset_shifted = 0
        self._time_shifted = 0
        #
        if file_name == "_no_name_":
            _Files = Files(path = path, shup = True)
            if not _Files.ok:
                print("Could not find the file (any files, really)."); return
            self._path = _Files.path
            try: watch_index, file_index = int(watch_index), int(file_index)
            except:
                print("The arguments watch_index and file_index must both be integers."); return
            if watch_index < 0:
                print("The argument watch_index must be an integer >= 0."); return
            if watch_index >= len(_Files._watches):
                print("The argument watch_index is too large. See list below.")
                _Files.Watches()
                return
            _Files.watch_index = watch_index
            self._other_files = _Files.files
            if file_index < 0 or file_index >= len(_Files.files):
                print(f"The argument file_index must be an integer between 0 and {len(_Files.files)-1}."); return
            _Files.file_index = file_index
            #
            self._file = _Files.file
            self._path = _Files.path
            self._watch_index = watch_index
            self._watch = _Files._watches[watch_index]
            del _Files
        else:
            self._file = file_name
            if path == "_no_path_": self._path = ""
            else: self._path = path
        #
        if self._path.endswith("/"): self._path = self._path[:-1]
        _ = self._loadFile(shup = shup)
        #
        self._original_data = {"watch": self.watch,
                               "watch_index": self._watch_index,
                               "file": self.file,
                               "path": self.path,
                               "header": self._header,
                               "time": self.time,
                               "offset": self.offset,
                               "comment": self.timing_comments,
                               "unix_time": self.unix_time,
                               "atomic_clock_error": self.atomic_clock_error,
                               "ios_clock_offset": self.ios_clock_offset}
        if self._ok and not shup:
            print("myWatchTracker TimingRun\n------------------------")
            self.Info()
            print("(use .Help() to... well, get help.)\n")
            
    # ----------------
    def Help(self):
        print("myWatchTracker TimingRun\n------------------------")
        print(f"Path:  {self.path}")
        print(f"File:  {self.file}")
        if self._ok:
            print(f"Watch: {self.watch}")

        print()
        print("properties:")
        print("  .path                      get         string             path to the file folder")
        print("  .file                      get         string             file name")
        print("  .watch                     get         string             watch name")
        print("  .time                      get         array of floats    time axis")
        print("  .unix_time                 get         array of floats    time axis")
        print("  .offset                    get         array of floats    watch time offset from atomic time")
        print("  .rate                      get         dict               rate in s/day vs time")
        print("  .atomic_clock_error        get         array of floats    atomic time error")
        print("  .ios_clock_offset          get         array of floats    iOS time error")
        print("  .timing_comments           get         array of strings   comments made during timing")
        print("  .start                     get         string             start time")
        print("  .end                       get         string             end time")
        print("  .duration                  get         float              timing run duration in days")
        print("  .unix_start                get         float              start time")
        print("  .unix_end                  get         float              end time")
        print("  .unix_duration             get         float              timing run duration in seconds")
        print("  .num_points                get         integer            number of data points")
        print("  .info                      get         dict               data info (see also .Info())")
        print("  .original_data             get         dict               dict containing all loaded data and info")
        print("")
        print("other properties:")
        print("  .point_index               get/set     integer")
        print("  .point_time                get/set     float         the value for the n:th element in .time, where n = .point_index")
        print("  .point_unix_time           get/set     float         the value for the n:th element in .unix_time")
        print("  .point_offset              get/set     float         the value for the n:th element in .offset")
        print("  .point_timing_comment      get/set     string        ...")
        print("  .point_atomic_clock_error  get/set     float         ...")
        print("  .point_ios_clock_offset    get/set     float         ...")
        print("  .point_datetime            get         datetime      a datetime object for data point .point_index")
        print("  .point                     get         dict          a dict with all data in the .point_index:th data point")
        print("  .point_delete              get/set     dict/int      deletes the n:th data point after returning it")
        print("  .point_insert              get ('set') dict          duplicates the point at point_index and returns it. See also .InsertPoint().")
        print("")
        print("methods:")
        print("  .Help()                    If you need help understanding what this method does...")
        print("  .Info()                    Prints the data in .info to screen.")
        print("  .Smooth()                  Smooth data using module method smooth(). Args size (int) and mode (str).")
        print("  .ShiftOffset()             Shifts the offset. Arg value (float).")
        print("  .ShiftOffsetReset():       Resets any shift set to the offset by .ShiftOffset().")
        print("  .ShiftTime()               Shifts the time axis. Arg value (float) in days.")
        print("  .ShiftTimeReset():         Resets any shift set to the time by .ShiftTime().")
        print("  .Reset()                   Resets all data to the loaded data.")
        print("  .Plot()                    Plots the data using module method plot(). See also module method multiPlot().")
        print("  .Save2txt()                Save data to text")
        print("  .Save2csv()                Save current data to a WatchTracker-formatted csv file.")
        print("  .ListPoints()              Lists index, time, unix time, offset, and comment to screen.")
        print("  .InsertPoint()             Inserts a data point.")
        print()
        print("other methods:")
        print("  .OpenCSV()                 Opens the loaded csv file in e.g. Excel.")
        print("  .Finder()                  Open a Finder window / tab.")
        print("  .FinderCWD()               Open a Finder window / tab for the current working directory.")
        print("  .FinderWT()                Open a Finder window / tab for the current WatchTracker folder.")

    # ----------------
    def _loadFile(self, shup = False):
        """
        """
        if self._path == "": file_name = self._file
        else: file_name = f"{self._path}/{self._file}"
        try:
            csv_file = open(file_name, "r")
            reader = csv.reader(csv_file)
        except:
            print(f"Could not open or find the file '{file_name}'.")
            return False
        #
        self._time, self._offset, self._comment, self._unix_time = [], [], [], []
        self._atomic_clock_error, self._ios_clock_offset, self._header = [], [], []
        try:
            for i, row in enumerate(reader):
                if i>=3 and i<=7:
                    self._header.append(row[1])
                elif i>9:
                    self._time.append( float(row[0]) )
                    self._offset.append( float(row[1]) ) 
                    self._comment.append(str(row[2]))
                    self._unix_time.append(int(row[3]))
                    self._atomic_clock_error.append(float(row[4]))
                    self._ios_clock_offset.append(float(row[5]))
            self._time, self._offset, self._comment = np.array(self._time), np.array(self._offset), np.array(self._comment)
            self._unix_time, self._atomic_clock_error = np.array(self._unix_time), np.array(self._atomic_clock_error)
            self._ios_clock_offset = np.array(self._ios_clock_offset)
            csv_file.close()
            self._ok = True
        except:
            print(f"There was an unexpected error when reading from file '{file_name}'.")
            self._time, self._offset, self._comment, self._unix_time = [], [], [], []
            self._atomic_clock_error, self._ios_clock_offset, self._header = [], [], []
            try: csv_file.close()
            except: pass
            return False
        #
        return True
    
    # ----------------
    def _deletePoint(self, index = None):
        if type(index) is type(None):
            index = self._point_index
        if len(self._time) <= 1:
            print("There's ony one data point so we are keeping it!"); return False
        #
        try: index = int(index)
        except:
            print(f"The argument index must be an integer (range 0 to {len(self._time)-1})."); return False
        #
        if index < 0 or index >= len(self._time):
            print(f"The argument index must be an integer (range 0 to {len(self._time)-1})."); return False
        #
        self._time = np.delete(self._time, index)
        self._offset = np.delete(self._offset, index)
        self._comment = np.delete(self._comment, index)
        self._unix_time = np.delete(self._unix_time, index)
        self._atomic_clock_error = np.delete(self._atomic_clock_error, index)
        self._ios_clock_offset = np.delete(self._ios_clock_offset, index)
        #
        if index >= len(self._time): self._point_index = len(self._time)-1
        return True


    # ----------------
    def Info(self):
        """
        Prints info about the loaded file / data to screen.
        The info is printed from the .info property.
        Arguments: none.
        """
        for key in self.info:
            print(f"{key:<11}: {self.info[key]}")
    
    def ListPoints(self):
        """
        Prints all data points to screen as a list with columns index, time, unix time, offset, and comment.
        """
        for i, time in enumerate(self.time):
            print(f"{i:3.0f}  {time:7.3f}  {self.unix_time[i]:10.0f}  {self.offset[i]:8.3f}  {self.timing_comments[i]}")
    
    # ----------------
    def Point(self):
        """
        Prints info from property .point (dict) to screen.
        Arguments: none.
        """
        for key in self.point:
            print(f"{key:<19}: {self.point[key]}")

    # ------- properties

    @property
    def path(self): return self._path
    @property
    def file(self): return self._file
    @property
    def watch(self): return self._header[0]
    @property
    def watch_index(self): return self._watch_index
    @property
    def time(self): return self._time
    @property
    def unix_time(self): return self._unix_time
    @property
    def offset(self): return self._offset
    @property
    def atomic_clock_error(self): return self._atomic_clock_error
    @property
    def ios_clock_offset(self): return self._ios_clock_offset
    @property
    def timing_comments(self): return self._comment
    @property
    def start(self): return datetime.fromtimestamp(self._unix_time[0]).isoformat().replace("T", ",")
    @property
    def unix_start(self): return self._unix_time[0]
    @property
    def end(self): return datetime.fromtimestamp(self._unix_time[-1]).isoformat().replace("T", ",")
    @property
    def unix_end(self): return self._unix_time[-1]
    @property
    def duration(self):
        return round((self._unix_time[-1] - self._unix_time[0])/(60*60*24),2)
    @property
    def unix_duration(self): return self._unix_time[-1] - self._unix_time[0]
    @property
    def other_files(self): return self._other_files
    @property
    def original_data(self): return self._original_data
    @property
    def info(self):
        return {"watch": self.watch, "file": self.file, "path": self.path, 
                "start": self.start, "end": self.end, "duration": self.duration, "data points": len(self.time)}

    @property
    def rate(self): return self._calcRate()

    
    @property
    def point_index(self):
        return self._point_index
    @property
    def point_time(self): return self._time[self._point_index]
    @property
    def point_unix_time(self): return self._unix_time[self._point_index]
    @property
    def point_offset(self): return self._offset[self._point_index]
    @property
    def point_timing_comment(self): return self._comment[self._point_index]
    @property
    def point_atomic_clock_error(self): return self._atomic_clock_error[self._point_index]
    @property
    def point_ios_clock_offset(self): return self._ios_clock_offset[self._point_index]
    @property
    def point_datetime(self):
        return datetime.fromtimestamp(self._unix_time[self._point_index])
    @property
    def point(self):
        return {"point_index": self.point_index,
                "time": self.point_time,
                "unix_time": self.point_unix_time,
                "offset": self.point_offset,
                "timing_comment": self.point_timing_comment,
                "atomic_clock_error": self.point_atomic_clock_error,
                "ios_clock_offset": self.point_ios_clock_offset}
    @property
    def point_delete(self):
        p = self.point
        if self._deletePoint(): return p
        else: return {}
    @property
    def point_insert(self):
        index = self.point_index
        time = self.point_time
        offset = self.point_offset
        comment = self.point_timing_comment
        unix_time = self.point_unix_time
        atomic_clock_error = self.point_atomic_clock_error
        ios_clock_offset = self.point_ios_clock_offset
        #
        self._time = np.insert(self._time, index, time)
        self._offset = np.insert(self._offset, index, offset)
        self._comment = np.insert(self._comment, index, comment)
        self._unix_time = np.insert(self._unix_time, index, unix_time)
        self._atomic_clock_error = np.insert(self._atomic_clock_error, index, atomic_clock_error)
        self._ios_clock_offset = np.insert(self._ios_clock_offset, index, ios_clock_offset)
        #
        self.point_index = self.point_index + 1
        #
        return self.point

    @property
    def num_points(self):
        return len(self._time)

    def _set_not_allowed(self, txt = ""):
        print(f"The property .{txt} can not be set.")
    @path.setter
    def path(self, *args, **kwargs): self._set_not_allowed(txt = "path")
    @file.setter
    def file(self, *args, **kwargs): self._set_not_allowed(txt = "file")
    @watch.setter
    def watch(self, *args, **kwargs): self._set_not_allowed(txt = "watch")
    @watch_index.setter
    def watch_index(self, *args, **kwargs): self._set_not_allowed(txt = "watch_index")
    @time.setter
    def time(self, *args, **kwargs): self._set_not_allowed(txt = "time")
    @unix_time.setter
    def unix_time(self, *args, **kwargs): self._set_not_allowed(txt = "unix_time")
    @offset.setter
    def offset(self, *args, **kwargs): self._set_not_allowed(txt = "offset")
    @atomic_clock_error.setter
    def atomic_clock_error(self, *args, **kwargs): self._set_not_allowed(txt = "atomic_clock_error")
    @ios_clock_offset.setter
    def ios_clock_offset(self, *args, **kwargs): self._set_not_allowed(txt = "ios_clock_offset")
    @timing_comments.setter
    def timing_comments(self, *args, **kwargs): self._set_not_allowed(txt = "timing_comments")
    @start.setter
    def start(self, *args, **kwargs): self._set_not_allowed(txt = "start")
    @unix_start.setter
    def unix_start(self, *args, **kwargs): self._set_not_allowed(txt = "unix_start")
    @end.setter
    def end(self, *args, **kwargs): self._set_not_allowed(txt = "end")
    @unix_end.setter
    def unix_end(self, *args, **kwargs): self._set_not_allowed(txt = "unix_end")
    @duration.setter
    def duration(self, *args, **kwargs): self._set_not_allowed(txt = "duration")
    @unix_duration.setter
    def unix_duration(self, *args, **kwargs): self._set_not_allowed(txt = "unix_duration")
    @other_files.setter
    def other_files(self, *args, **kwargs): self._set_not_allowed(txt = "other_files")
    @original_data.setter
    def original_data(self, *args, **kwargs): self._set_not_allowed(txt = "original_data")
    @rate.setter
    def rate(self, *args, **kwargs): self._set_not_allowed(txt = "rate")
    @info.setter
    def info(self, *args, **kwargs): self._set_not_allowed(txt = "info")
    @num_points.setter
    def num_points(self, *args, **kwargs): self._set_not_allowed(txt = "num_points")
    
    @point_index.setter
    def point_index(self, index):
        try: index = int(index)
        except:
            print(f"Property point_index must be an integer between 0 and {len(self._time)-1}."); return
        if index < 0 or index >= len(self._time):
            print(f"Property point_index must be an integer between 0 and {len(self._time)-1}."); return
        self._point_index = index
    
    @point_time.setter  
    def point_time(self, value): 
        try: value = float(value)
        except:
            print("The point_time property must be set with a float."); return
        dvalue = value - self.point_time
        self._time[self._point_index] = value
        self._unix_time[self._point_index] = self._unix_time[self._point_index] + dvalue*60*60*24
    @point_unix_time.setter
    def point_unix_time(self, value):
        try: value = float(value)
        except:
            print("The point_unix_time property must be set with a float."); return
        dvalue = value - self.point_unix_time
        self._unix_time[self._point_index] = value
        self._time[self._point_index] = self.time[self._point_index] + dvalue/60/60/24
    @point_offset.setter
    def point_offset(self, value): 
        try: value = float(value)
        except:
            print("The point_offset property must be set with a float."); return
        self._offset[self._point_index] = value
    @point_timing_comment.setter
    def point_timing_comment(self, comment):
        try: comment = str(comment)
        except:
            print("The point_timing_comment property must be set with a string."); return
        self._comment[self._point_index] = comment
    @point_atomic_clock_error.setter
    def point_atomic_clock_error(self, value):
        try: value = float(value)
        except:
            print("The point_atomic_clock_error property must be set with a float."); return
        self.point_atomic_clock_error[self._point_index] = value        
    @point_ios_clock_offset.setter
    def point_ios_clock_offset(self, value): 
        try: value = float(value)
        except:
            print("The point_ios_clock_offset property must be set with a float."); return
        self.point_ios_clock_offset[self._point_index] = value        
    @point_datetime.setter
    def point_datetime(self, *args, **kwargs): self._set_not_allowed(txt = "point_datetime")
    @point_delete.setter
    def point_delete(self, index):
        try: index = int(index)
        except:
            print("The attribute point_delete must be set with an integer."); return
        if index < 0: index = 0
        if index >= len(self._time): index = len(self._time)-1
        self.point_index = index
        return self.point_delete
    @point_insert.setter
    def point_insert(self, *args, **kwargs): self._set_not_allowed(txt = "point_insert")


    # ---------------------------

    def OtherFiles(self):
        """
        Prints a list of other timing run files associated with this watch, 
        provided that the file was loaded with watch_index and file_index.
        Arguments: none.
        """
        print(f"Watch: {self._watch}")
        print(f"Total number of files: {len(self._other_files)}")
        print("index  file")
        for i, file in enumerate(self._other_files):
            print(f"{i:<7}{file}")
    
    # ---------------------------

    def Reset(self):
        """
        Resets to data as loaded.
        Arguments: none.
        """
        self._watch = self._original_data["watch"]
        self._watch_index = self._original_data["watch_index"]
        self._file = self._original_data["file"]
        self._path = self._original_data["path"]
        self._header = self._original_data["header"]
        self._time = self._original_data["time"]
        self._offset = self._original_data["offset"]
        self._comment = self._original_data["comment"]
        self._unix_time = self._original_data["unix_time"]
        self._atomic_clock_error = self._original_data["atomic_clock_error"]
        self._ios_clock_offset = self._original_data["ios_clock_offset"]
        self._offset_shifted = 0
        print("All data reset to as loaded.")
    
    # ---------------------------

    def _calcRate(self):
        xaxis, yaxis = [], []
        for i in range(len(self.offset)-1):
            xaxis.append((self.time[i+1] + self.time[i])/2)
            yaxis.append( (self.offset[i+1] - self.offset[i]) / (self.time[i+1] - self.time[i]) )
        return {"time": np.array(xaxis), "rate": np.array(yaxis), "units": ["days", "s/day"], "start": self.start}
    
    # ---------------------------

    def Smooth(self, size = 3, mode = "reflect", shup = False):
        """
        Smooths the offset data with .median_filter from scipy.
        Arguments: size (integer) and mode (string).
        """
        smoothed_offset = smooth(self.offset, size = size, mode = mode)
        if not smoothed_offset == np.array([]): self._offset = smoothed_offset
        if not shup:
            print(f"The offset was smoothed with median_filer(array, size, mode) from scipy, with size = {size} and mode = {mode}.")
    
    # ---------------------------

    def Plot(self, ax = None, figsize = (5, 3.5), xunit = "days", yunit = "seconds", legend = False, plot_rate = False):
        """
        Returns a graph (Pyplot ax), using the module method plot().
        For more plotting options, use module method multiPlot().
        """
        return plot(timing_run = self, ax = ax, xunit = xunit, yunit = yunit, figsize = figsize, plot_rate = plot_rate)
    
    # ---------------------------

    def ShiftOffset(self, value = 0., shup = False):
        """
        Shifts the offset.
        Arguments: value (scalar).
        See also: .ShiftOffsetReset().
        """
        try: float(value)
        except:
            print("The argument must be a float.")
        self._offset += value
        self._offset_shifted += value
    
    def ShiftTime(self, value = 0):
        """
        Shifts the time axis.
        Arguments: value (scalar).
        See also: .ShiftTimeReset().
        """
        try: float(value)
        except:
            print("The argument must be a float (days).")
        self._time += value
        self._unix_time += value*60*60*24
        self._time_shifted += value
        
    def ShiftOffsetReset(self):
        """
        Resets any shift set to the offset by .ShiftOffset().
        Arguments: none.
        """
        self._offset -= self._offset_shifted
        self._offset_shifted = 0
    
    def ShiftTimeReset(self):
        """
        Resets any shift set to the time axis by .ShiftTime().
        Arguments: none.
        """
        self._time -= self._time_shifted
        self._unix_time -= self._time_shifted*60*60*24
        self._time_shifted = 0
    
    # ---------------------------
    
    def Save2txt(self, file_name = "", shup = False):
        """
        Saves the data as time and offset to a text file readable with e.g. numpy.loadtxt().
        Arguments: file_name (string).
        """
        if not type(file_name) is str:
            print("The argument file_name must be a string. Setting default.")
            file_name = self.file
        if file_name == "":
            file_name = self.file
        for ext in [".csv", ".CSV", ".Csv"]:
            if file_name.endswith(ext): file_name = file_name.strip(ext)
        if not file_name.lower().endswith(".txt"):
            file_name = f"{file_name}.txt"
        #
        with open(file_name, "w") as f:
            f.write(f"# watch    : {self.watch}\n")
            f.write(f"# start    : {self.start}\n")
            f.write(f"# end      : {self.end}\n")
            f.write(f"# duration : {self.duration['duration']}\n")
            f.write(f"# columns  : time from start (days), offset (s), unix time stamp\n")
            for i, t in enumerate(self.time):
                f.write(f"{t:5.2f}\t{self.offset[i]:5.1f}\t{self.unix_time[i]}\n")
        #
        if not shup:
            print(f"Saved data to text file {file_name}")
    
    # ---------------------------

    def Save2csv(self, file_name = "watch_tracker.csv", watch_comment = "", timing_run_comment = "", path = "", shup = False):
        """
        Saves the current data to a WatchTracker formated csv file.
        Arguments: file_name (string), watch_comment (string), timing_run_comment (string), path (string).
        """
        if not type(file_name) is str:
            print("The argument file_name must be a string. Setting default.")
            file_name = self.file
        if file_name == "":
            file_name = self.file
        if not file_name.lower().endswith(".csv"):
            file_name = f"{file_name}.csv"
        #
        if not type(watch_comment) is str:
            print("The argument watch_comment must be a string."); return
        if watch_comment == "": watch_comment = self._header[0][1]
        if not type(timing_run_comment) is str:
            print("The argument timing_run_comment must be a string."); return
        if timing_run_comment == "": timing_run_comment = "myWatchTracker"
        #
        if not type(path) is str:
            print("The argument path must be a string."); return
        #
        if path == "":
            FILE_NAME = file_name
        else:
            if not path.endswith("/"): path = f"{path}/"
            FILE_NAME = f"{path}{file_name}"
        #
        timing_run_name = file_name.replace('_', ' ').strip(".csv")
        first_data_point = self._header[0][4]
        #
        f = open(FILE_NAME, "w")
        f.write('Timing run file\n')
        f.write('Generated by myWatchTracker\n')
        f.write("\n")
        f.write(f"Watch name,{self.watch}\n")
        f.write(f"Watch comment,{watch_comment}\n")
        f.write(f"Timing run name,{timing_run_name}\n")
        f.write(f"Timing run comment,{timing_run_comment}\n")
        f.write(f"First data point,{first_data_point}\n")
        f.write("\n")
        f.write("Days,Offset,Comment,UNIX time,Atomic clock error,iOS clock offset\n")
        for i in range(len(self.time)-1):
            f.write(f"{self._time[i]},{self._offset[i]},{self._comment[i].replace(',', ';')},{self._unix_time[i]},{self._atomic_clock_error[i]},{self._ios_clock_offset[i]}\n")
        f.close()
        #
        if not shup:
            if path == "": additional = ""
            else: additional = f" in {path}"
            print(f"Saved data to {file_name}{additional}.")
    
    # ---------------------------

    def InsertPoint(self, time = None, offset = None, comment = "", shup = False):
        """
        Inserts a data point.
        Arguments: time as float (days), offset at float(seconds), and comment as string (optional).
        """
        try: time, offset = float(time), float(offset)
        except:
            print("Arguments time and offset must be floats (time as days, offset as seconds."); return
        if not type(comment) is str:
            print("Argument comment must be a string. Setting if to default."); comment = "(inserted)"
        if comment == "": comment = "(inserted)"
        #
        index = abs(time - self.time).argmin()
        self._time = np.insert(self._time, index, time)
        self._offset = np.insert(self._offset, index, offset)
        self._comment = np.insert(self._comment, index, comment)
        unix_time = self.unix_time[0] + (time - self.time[0])*(24*60*60)
        self._unix_time = np.insert(self._unix_time, index, unix_time)
        self._atomic_clock_error = np.insert(self._atomic_clock_error, index, 0)
        self._ios_clock_offset = np.insert(self._ios_clock_offset, index, 0)
        if not shup:
            print(f"Inserted a data point at index = {index} with time = {time}, offset = {offset}")
            if not comment == "": print(f"and comment = {comment}.")
        return self.point
    
    # ---------------------------

    def openCSV(self, shup = False):
        """
        Opens the loaded csv file in e.g. Excel.
        Arguments: none.
        """
        call(["open", f"{self.path}/{self.file}"])
    
    # ---------------------------

    def Finder(self): call(["open", "~/"])
    def FinderCWD(self): call(["open", ""])
    def FinderWT(self): call(["open", self.path])

    # ---------------------------







# ============================================================================================================
# ============================================================================================================
# ============================================================================================================
# ============================================================================================================





def concatTimingRuns(timing_runs = [], connect_offset = True, skip_first = False):
    """
    Concatenate a list of timing runs.

    Arguments:
       timing_runs     list    A list of TimingRun objects.
       connect_offset  bool    
       skip_first      bool    Skip the first point in all timing runs except the first.
    """
    if not type(timing_runs) is list:
        print("The argument timing_runs must be a list of TimingRun objects."); return None
    if not len(timing_runs) > 1:
        print("The argument timing_runs must be a list of at least two TimingRun objects."); return None
    for obj in timing_runs:
        try: obj_type = obj._class_type
        except:
            print("There is an object is the list which is not a TimingRun object."); return None
        if not obj_type == "TimingRun":
            print("There is an object is the list which is not a TimingRun object."); return None
    #
    ret_obj = deepcopy(timing_runs[0])
    ret_obj._other_files = []
    ret_obj._point_index = 0
    ret_obj._offset_shifted = 0
    ret_obj._time_shifted = 0
    ret_obj._original_data = {}
    #
    if not skip_first: N1 = 0
    else: N1 = 1
    for i, obj in enumerate(timing_runs[1:]):
        ret_obj._time = np.hstack((ret_obj._time, obj._time[N1:] + ret_obj._time[-1]))
        ret_obj._unix_time = np.hstack((ret_obj._unix_time, obj._unix_time[N1:] + ret_obj._unix_time[-1]))
        #
        if not connect_offset: delta = 0
        else:
            delta = obj._offset[0] - ret_obj._offset[-1]
        ret_obj._offset = np.hstack((ret_obj._offset, obj._offset[N1:] - delta))
        #
        ret_obj._atomic_clock_error = np.hstack((ret_obj._atomic_clock_error, obj._atomic_clock_error[N1:]))
        ret_obj._ios_clock_offset = np.hstack((ret_obj._ios_clock_offset, obj._ios_clock_offset[N1:]))
        ret_obj._comment = np.hstack((ret_obj._comment, obj._comment[N1:]))
    # --- do something more advanced for the next section....
    ret_obj._watch = "|watch|"
    ret_obj._watch_index = -1
    ret_obj._file = "|file|"
    ret_obj._header = ["|watch|", "|watch comment|", "|file comment|", "|?|", ret_obj._header[4]]
    #
    ret_obj._original_data = {"watch": ret_obj.watch,
                            "watch_index": ret_obj._watch_index,
                            "file": ret_obj.file,
                            "path": ret_obj.path,
                            "header": ret_obj._header,
                            "time": ret_obj.time,
                            "offset": ret_obj.offset,
                            "comment": ret_obj.timing_comments,
                            "unix_time": ret_obj.unix_time,
                            "atomic_clock_error": ret_obj.atomic_clock_error,
                            "ios_clock_offset": ret_obj.ios_clock_offset}
    #
    return ret_obj





# ============================================================================================================
# ============================================================================================================
# ============================================================================================================
# ============================================================================================================




def linspaceTime(timing_run = object, n = 0, shup = False):
    """
    """
    print("\nunder construction\n")
    #
    ret_obj = deepcopy(timing_run)
    try: obj_type = timing_run._class_type
    except:
        print("The argument timing_run must be a TimingRun object."); return ret_obj
    if not obj_type == "TimingRun":
        print("The argument timing_run must be a TimingRun object."); return ret_obj
    try: n = abs(int(n))
    except:
        print("The argument n must be a positive integer (>0)."); return ret_obj
    if not n > 0:
        print("The argument n must be a positive integer (>0)."); return ret_obj
    #
    numpnts = len(timing_run.time) * n
    tstart, tstop = timing_run.time[0], timing_run.time[-1]
    new_time = np.linspace(tstart, tstop, numpnts)
    # check if the linear scale is too coarse
    tmp_time = np.zeros(numpnts)
    for t in timing_run.time:
        index = abs(new_time - t).argmin()
        tmp_time[index] += 1
        if tmp_time[index] > 1:
            print("The argument n is too small. Too coarse steps leads -> loss of data."); return ret_obj
    #
    new_offset = np.zeros(numpnts) * np.NaN
    for i, t in enumerate(timing_run.time):
        index = abs(new_time - t).argmin()
        new_offset[index] = timing_run.offset[i]
    # check if there is at least one empty new point between old points
    indices = []
    for i, o in enumerate(new_offset):
        if not np.isnan(o): indices.append(i)
    indices = np.array(indices)
    for i, ii in enumerate(indices):
        if i < len(indices)-1:
            if not indices[i+1] - ii > 1:
                print("The argument n is too small. There are old points that are neighbors. In principle okay but not allowed here. Sorry."); return ret_obj
    #
    new_unix, new_comment, new_ace, new_ico = np.zeros(len(new_time)), [], np.zeros(len(new_time)), np.zeros(len(new_time))
    for i in range(len(new_time)): new_comment.append("inserted")
    #
    for i in range(len(indices)-1):
        i1, i2 = indices[i], indices[i+1]
        print(i,i1)
        dt = new_time[1] - new_time[0]
        k = (new_offset[i2] - new_offset[i1]) / (new_time[i2] - new_time[i1])
        for ii, x in enumerate(range(indices[i], indices[i+1])):
            new_offset[i1 + ii] = new_offset[i1] + k * (ii * dt)
        new_comment[i1] = timing_run._comment[i]
        
    ret_obj._time = new_time
    ret_obj._offset = new_offset
    ret_obj._comments = new_comment

    
    
    # update the dict. also make the unix_time scale. fill out atomic time stuff and ios time error

        #self._time = np.delete(self._time, index)
        #self._offset = np.delete(self._offset, index)
        #self._comment = np.delete(self._comment, index)
        #self._unix_time = np.delete(self._unix_time, index)
        #self._atomic_clock_error = np.delete(self._atomic_clock_error, index)
        #self._ios_clock_offset = np.delete(self._ios_clock_offset, index)
    
    return ret_obj




    








# ============================================================================================================
# ============================================================================================================
# ============================================================================================================
# ============================================================================================================



def plot(timing_run = object, xunit = "days", yunit = "seconds", ax = None, figsize = (5, 3.5), plot_rate = False):
    """
    Plot the data in / from a TiminRun object.

    Arguments:
        timing_run      TiminRun object.
        xunit           string
        yunit           string
        ax              pyplot axis
    """
    #
    return multiPlot(timing_runs = [timing_run], ax = ax, xunit = xunit, yunit = yunit, figsize = figsize, 
                     legend = False, title = f"{timing_run.watch}, {timing_run.start}", fontsize_title = 12,
                     plot_rate = plot_rate)





def multiPlot(timing_runs = [], ax = None, **kwargs):
    """
    Arguments:
        timing_runs        required    a list of timing runs.
        ax                 optional    a pyplot axis 
    Keyword arguments:
        figsize            tuple
        title              string
        xlabel             string
        ylabel             string
        fontsize_title     integer
        fontsize_label     integer
        xunit              string
        yunit              string
        legend             bool
        legend_type        integer
        fontsize_legend    integer
    """
    if not type(timing_runs) is list:
        print("The argument timing_runs must be a list of TimingRun objects."); return None
    if not len(timing_runs) > 0:
        print("The argument timing_runs must be a list of at least two TimingRun objects."); return None
    for obj in timing_runs:
        try: obj_type = obj._class_type
        except:
            print("There is an object is the list which is not a TimingRun object."); return None
        if not obj_type == "TimingRun":
            print("There is an object is the list which is not a TimingRun object."); return None
    # --------------
    accepted_kwargs = ["figsize", "title", "xlabel", "ylabel", "fontsize_title", "fontsize_label", "xunit", "yunit",
                       "legend", "fontsize_legend", "plot_rate"]
    xunits = ["hours", "days", "weeks"]
    yunits = ["seconds", "minutes", "hours"]
    #
    figsize = kwargs.get("figsize", (8,4))
    if not type(figsize) is tuple:
        print("The keyword argument must be a tuple."); figsize = (8,4)
    title = kwargs.get("title", "")
    if not type(title) is str:
        print("The keyword argument title must be a string."); title = ""
    fig = None
    if type(ax) is type(None):
        fig, ax = plt.subplots(figsize = figsize)
    #
    xunit = kwargs.get("xunit", "days")
    if not type(xunit) is str:
        print(f"The keyword argument xunit must be a string ({xunits}). Setting default."); xunit = xunits[1]
    if not xunit in xunits:
        print(f"The keyword argument xunit must be one of {xunits}. Setting default."); xunit = xunits[1]
    yunit = kwargs.get("yunit", "seconds")
    if not type(yunit) is str:
        print(f"The keyword argument yunit must be a string ({yunits}). Setting default."); yunit = yunits[0]
    if not yunit in yunits:
        print(f"The keyword argument yunit must be one of {yunits}. Setting default."); yunit = yunits[0]
    #
    if xunit == xunits[0]: xscaler = 24
    elif xunit == xunits[1]: xscaler = 1
    elif xunit == xunits[2]: xscaler = 1/7
    if yunit == yunits[0]: yscaler = 1
    elif yunit == yunits[1]: yscaler = 1/60
    elif yunit == yunits[2]: yscaler = 1/60/24
    #
    xlabel = kwargs.get("xlabel", "-empty-")
    if not type(xlabel) is str:
        print("The keyword argument xlabel must be a string. Setting default."); xlabel = "-empty-"
    ylabel = kwargs.get("ylabel", "-empty-")
    if not type(ylabel) is str:
        print("The keyword argument ylabel must be a string. Setting default."); ylabel = "-empty-"
    #
    if xlabel == "-empty-":
        if xunit == xunits[0]: xlabel = "Time, hours"
        elif xunit == xunits[1]: xlabel = "Time, days"
        elif xunit == xunits[2]: xlabel = "Time, weeks"
    if ylabel == "-empty-":
        if yunit == yunits[0]: ylabel = "Offset, seconds"
        elif yunit == yunits[1]: ylabel = "Offset, minutes"
        elif yunit == yunits[2]: ylabel = "Offset, hours"
    #
    plot_rate = kwargs.get("plot_rate", False)
    if not type(plot_rate) is bool:
        print("The keyword argument plot_rate must be a bool. Setting it to plot_rate = False"); plot_rate = False
    if plot_rate: ylabel = f"{ylabel.replace('Offset', 'Rate')}/day"
    #
    fontsize_title = kwargs.get("fontsize_title", 16)
    if not type(fontsize_title) is int:
        print("The keyword argument fontsize_title must be an integer."); fontsize_title = 16
    fontsize_label = kwargs.get("fontsize_label", 12)
    if not type(fontsize_label) is int:
        print("The keyword argument fontsize_label must be an integer."); fontsize_label = 12
    #
    if not title == "": ax.set_title(title, fontsize = fontsize_title)
    if not xlabel == "": ax.set_xlabel(xlabel, fontsize = fontsize_label)
    if not ylabel == "": ax.set_ylabel(ylabel, fontsize = fontsize_label)
    #
    legend_type = kwargs.get("legend_type", 0)
    if not type(legend_type) is int:
        print("The keyword argument legend_type must be an integer from 0 to 1. Setting default."); legend_type = 0
    if not legend_type in [0,1]:
        print("The keyword argument legend_type must be an integer from 0 to 1. Setting default."); legend_type = 0
    #
    for tr in timing_runs:
        if legend_type == 0: llabel = f"{tr.start}"
        elif legend_type == 1: llabel = f"{tr.watch}, {tr.start}"
        if not plot_rate:
            ax.plot(tr.time * xscaler, tr.offset * yscaler, label = llabel)
        else:
            rate = tr._calcRate()
            ax.plot(rate["time"] * xscaler, rate["rate"] * yscaler, label = llabel)  
    #
    legend = kwargs.get("legend", True)
    if not type(legend) is bool:
        print("The keyword argument legend must be a bool. Setting delfault."); legend = True
    fontsize_legend = kwargs.get("fontsize_legend", 10)
    if not type(fontsize_legend) is int:
        print("The keyword argument fontsize_legend must be an integer. Setting delfault."); fontsize_legend = 10
    if legend:
        _ = ax.legend(fontsize = fontsize_legend)
    #
    if not type(fig) is type(None): fig.tight_layout()
    #
    if len(kwargs.keys()) > 0:
        for key in kwargs.keys():
            if not key in accepted_kwargs: print(f"Passed keyword argument {key} is not recognized by this method.")
    #
    return ax

    






# ============================================================================================================
# ============================================================================================================
# ============================================================================================================
# ============================================================================================================



def smooth(y = None, size = 3, mode = "reflect"):
    """
    Uses median_filter from scipy.ndimage
       scipy.ndimage.median_filter(input, size=None, footprint=None, output=None, mode='reflect', cval=0.0, origin=0)
    Arguments:
        y       array      not optional
        size    integer    default 3
        mode    string     default 'reflect'

    mode can be 'reflect', 'constant', 'nearest', 'mirror', or 'wrap' where
        reflect  (d c b a | a b c d | d c b a)
        constant (k k k k | a b c d | k k k k)
        nearest  (a a a a | a b c d | d d d d)
        mirror   (d c b | a b c d | c b a)
        wrap     (a b c d | a b c d | a b c d)
    """
    modes = ["reflect", "constant", "nearest", "mirror", "wrap"]
    #
    try: size = abs(int(size))
    except:
        print("The argument size must be a positive integer > 0. Setting default size = 3."); size = 3
    if size < 1:
        print("The argument size must be a positive integer > 0. Setting default size = 3."); size = 3
    if not type(y) is np.ndarray:
        print("The argument y must be a numpy array (1d)."); return np.array([])
    if not len(y) > size:
        print("The size of argument y must be larger than the argument size."); return np.array([])
    if not type(mode) is str:
        print("The argument mode must be a string with one of the following values:")
        print(f"  {modes}")
        print(f"Setting default mode = '{modes[0]}'.")
    if not mode in modes:
        print(f"Possible values for the argument mode are: {modes}.")
        print(f"Setting default mode = '{modes[0]}'.")
    #
    return median_filter(y, size = size, mode = mode)
    






# ===================================================================================
# ===================================================================================
# ===================================================================================
# ===================================================================================




class Files():
    """
    This is an object that handles the files in whatever iCloud folder.
    Used by class File().
    Public methods:
        .Watches()  List the watches found in the WatchTracker folder on iCloud.
        .Watch()    Lists the files associated with a particular watch.
    The attributes are used by the File() class when loading data.
    """
    def __init__(self, path = "_no_path_", shup = False):
        #
        self._class_type = "Files"
        self._path = ''
        self._all_files = []
        self._watches = []
        self._watch_files = []
        self._ok = False
        #
        self._watch_index = None
        self._file_index = None
        #
        if not self._setPath(path): return   
        if not self._getAllFiles(): return
        self._getWatches()
        #
        if len(self._watches) > 0: self._ok = True
        self._watch_index = 0
        self._file_index = 0
        _ = self.file
        #
        if self._ok:
            if not shup: self.Help()
    
    # ----------------
    def Help(self):
        print("myWatchTracker Files\n--------------------")
        print(f"Path:    {self._path}")
        print(f"Watches: {len(self._watches)}")
        print(f"Files:   {len(self._all_files)}")
        print()
        print("properties:")
        print("  .path          get/set   string    path to the file folder")
        print("  .all_files     get       list      list of all files")
        print("  .watches       get       list      list of the watches")
        print("  .watch_index   get/set   integer   index of the selected watch")
        print("  .watch         get       string    name of the selected watch (.watch_index)")
        print("  .files         get       list      files belonging to the selected watch")
        print("  .file_index    get/set   integer   index of the selected file (for the selected watch)")
        print("  .file          get/set   string    file name of the selected file (for the selected watch)")
        print()
        print("methods:")
        print("  .Watches()     Prints to screen a list of all watches, including their indices and the number of files per watch.")
        print("  .Files()       Print a list of the files associated with the watch set by .watch_index.")
        print("  .File()        Show info for the watch and file selected by watch_index and file_index.")
        print("  .CopyFile()    Copies the file selected by watch_index and file_index to the current working directory.")
        print("  .Help()        If you need help understanding what this method does...")
        print()
        print("  .Finder()      Open a Finder window / tab.")
        print("  .FinderCWD()   Open a Finder window / tab for the current working directory.")
        print("  .FinderWT()    Open a Finder window / tab for the current WatchTracker folder.")
        print("  .OpenCSV()     Opens the currently selected csv file (.watch_index & .file_index) in e.g. Excel.")

    # ----------------
    def _setPath(self, path):
        if not path == "_no_path_":
            if os.path.exists(path):
                self._path = path
            else:
                print(f"Path '{path}' does not exist.")
                return False
        else:
            global DEFAULT_PATHS
            for pth in DEFAULT_PATHS:
                if os.path.exists(pth): self._path = pth
            if self._path == "":
                print('None of the default paths are correct for this machine.')
                return False
            return True
    
    # -------------------
    def _getAllFiles(self):
        file_list = os.listdir(self._path)
        if len(file_list) == 0:
            print(f"There are no files in '{self.path}'.")
            return False
        file_list2 = []
        for file in file_list:
            if file.lower().endswith('.csv'): file_list2.append(file)
        if len(file_list2) == 0:
            print(f"There are no csv files in '{self.path}'.")
            return False
        file_list2.sort()
        self._all_files = file_list2
        return True
    
    # -------------------
    def _getWatches(self):
        watches = []
        pairs = []
        for file in self._all_files:
            csv_file = open(self._path + '/' + file, "r")
            reader = csv.reader(csv_file)
            for row in reader:
                if type(row) is list:
                    if len(row) >= 2:
                        if row[0] == 'Watch name':
                            watches.append(row[1])
                            pairs.append([row[1], file])
        watches = np.unique(watches)
        watches.sort()
        watch_files = []
        for watch in watches:
            tmp = []
            for pair in pairs:
                if pair[0] == watch: 
                    tmp.append(pair[1])
            watch_files.append(tmp)
        self._watches = watches
        self._watch_files = watch_files
    
    # properties   ---------------

    @property
    def path(self):
        return self._path
    
    @path.setter
    def path(self, value = ""):
        if not type(value) is str:
            print("The property .path must be a string."); return None
        self.__init__(path = value, shup = False)
    
    @property
    def watches(self):
        return self._watches
    
    @watches.setter
    def watches(self, *args):
        print("The property .watches can not be set."); return None
    
    @property
    def all_files(self):
        return self._all_files
    
    @all_files.setter
    def all_files(self, *args):
        print("The property .all_files can not be set."); return None
    
    @property 
    def watch_index(self):
        return self._watch_index
    
    @watch_index.setter
    def watch_index(self, value):
        try: value = int(value)
        except:
            print(f"The property .watch_index must be an integer between 0 and {len(self._watches)-1}.")
            return None
        if value < 0 or value >= len(self._watches):
            print(f"The property .watch_index must be an integer between 0 and {len(self._watches)-1}.")
            return None
        self._watch_index = value

    @property
    def watch(self):
        return self._watches[self._watch_index]
    
    @watch.setter
    def watch(self, value):
        print("The property .watch can not be set."); return None
    
    @property
    def file_index(self):
        return self._file_index
    
    @file_index.setter      # FINISH THIS!
    def file_index(self, value):
        try: value = int(value)
        except:
            print(f"The property .file_index must be an integer between 0 and {0}.")
            return
        if value < 0 or value >= len(self._watches):
            print(f"The property .file_index must be an integer between 0 and {0}.")
            return
        self._file_index = value

    @property
    def files(self):
        return self._watch_files[self._watch_index]
    
    @files.setter
    def files(self, value):
        print("The property .files can not be set."); return None
    
    @property
    def file(self):
        return self._watch_files[self._watch_index][self._file_index]
    
    @file.setter
    def file(self, value):
        print("The property .file can not be set."); return None
    
    @property
    def ok(self):
        return self._ok
    
    @ok.setter
    def ok(self, value):
        print("The property .ok can not be set."); return None

    # methods ------------------ 

    def Watches(self):
        print("{0}{1:<25}{2}".format('index  ', 'watch', '# files'))
        for i, watch in enumerate(self.watches):
            print("{0:<7}{1:<25}{2}".format(i, watch, len(self._watch_files[i])))
    
    def Watch(self):
        print(f"Watch: {self.watch}")
        print(f"Index: {self.watch_index}")
        print(f"Files: {len(self.files[self.watch_index])}")
    
    def Files(self):
        print(f"Watch: {self._watches[self._watch_index]}")
        print("index  file")
        for i, file in enumerate(self._watch_files[self._watch_index]):
            print(f"{i:<7}{file}")
    
    def File(self, hide_text = False, hide_plot = False):
        TR = TimingRun(watch_index = self.watch_index, file_index = self.file_index, shup = True)
        if not hide_text:
            print(f"file:     {TR.file}")
            print(f"path:     {TR.path}")
            print(f"watch:    {TR.watch}")
            print(f"start:    {TR.start}")
            print(f"duration: {(TR.time[-1]-TR.time[0]):.2f} days")
            print(f"points:   {len(TR.time)}")
        if not hide_plot:
            _ = plot(timing_run = TR, ax = None, figsize = (4,2.5))
        del TR
    
    def CopyFile(self, file_name = "", shup = False):
        """
        Copies a file from iCloud to the current working directory.
        """
        if not type(file_name) is str:
            print("The argument file_name must be a string."); return
        if file_name == "":
            file_name = self.file
        if not file_name.lower().endswith(".csv"):
            file_name = f"{file_name}.csv"
        source_name = f"{self.path}/{self.file}"
        try: shutil_copy(source_name, file_name)
        except Exception as e:
            print(f"Could not copy '{source_name}' to '{file_name}'\n")
            print(e)
            return
        if not shup:
            print(f"Copied '{source_name}'\nto '{file_name}' in the current working directory.")
    

    def Finder(self): call(["open", "~/"])
    def FinderCWD(self): call(["open", ""])
    def FinderWT(self): call(["open", self.path])
    def OpenCSV(self): call(["open", f"{self.path}/{self.file}"])


        








            
            
            
