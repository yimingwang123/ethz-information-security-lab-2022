import os 
import time 
import subprocess
    
def m_p_starter():
    os.system("cd /home/isl/t1  && /home/isl/t1/run_manager.sh ") # | tee  /home/isl/t1/manager.log &")
    os.system("cd /home/isl/t1  && /home/isl/t1/run_peripheral.sh ") # | tee  /home/isl/t1/peripheral.log &")
    os.system("pkill -9 string_parser")
    return 
    
def set_input(input): 
    gdb = subprocess.Popen(["gdb", "--args","python3","/home/isl/t1/sp_server.py"], stdin=subprocess.PIPE) #/home/isl/t1/string_parser"], stdin=subprocess.PIPE)
    time.sleep(2)
    write(gdb,"add-symbol-file /home/isl/.local/lib/stringparser_core.so")
    write(gdb,"set follow-fork-mode child")
    write(gdb,"set breakpoint pending on")
    write(gdb,"break gcm_crypt_and_tag")
    write(gdb,"run")
    time.sleep(2)
    os.system("node --no-warnings /home/isl/t1/remote_party  | tee /home/isl/t1/remote_party.log &")
    write(gdb,"break gcm_crypt_and_tag")
    write(gdb,"continue")
    write(gdb,"print input")
    write(gdb,input)
    write(gdb,"print input")
    write(gdb,"continue 100")
    time.sleep(2)
    gdb.terminate()
    os.system("pkill -9 gdb")
    return 

def write(gdb,message):
    message_str = message + "\n"
    message_str_encoded = message_str.encode()
    gdb.stdin.write(message_str_encoded)
    gdb.stdin.flush() 
    return

def clean():
    os.system("pkill -9 node")
    os.system("pkill -f sp_server.py")
    os.system("pkill -9 gdb")
    time.sleep(2)
    return 

input1 = 'set {char[40]} input = "<mes><action type=\\"key-update\\"/></mes>" '
input2 = 'set {char[40]} input = "redeemToken,token" '

clean()
m_p_starter()
set_input(input1)
set_input(input2)
clean()
os.system("cd /home/isl/t1 && /home/isl/t1/run.sh")



