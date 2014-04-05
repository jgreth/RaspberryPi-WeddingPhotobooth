#!/usr/bin/env python
import subprocess
import shlex  
    
#Get raspistill process id, needed to tell camera to capture picture
proc1 = subprocess.Popen(shlex.split('ps -ef'),stdout=subprocess.PIPE)
proc2 = subprocess.Popen(shlex.split('grep photoBooth'),stdin=proc1.stdout,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)


proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
out,err=proc2.communicate()

print out

for line in out:
    processId = out.split(" ")
    #print line
    
proc2.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.    