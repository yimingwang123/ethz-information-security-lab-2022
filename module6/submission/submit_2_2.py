import sys
import os
import string
import shutil


def check_command_ling_arg(arguments):
	if len(sys.argv) != 2:
		print("Number of command line arguments must be 1!")			
		exit()
		return False
	return True	

def read_command_line_arg(arguments):
	path = sys.argv[1]
	return path

def create_trace(guess, ch):
	os.chdir("/home/isl/pin-3.11-97998-g7ecce2dac-gcc-linux-master/source/tools/SGXTrace")
	output_path = f"/home/isl/t2_2/traces/trace_{ch}"
	output_pathname = os.path.dirname(output_path)
	os.makedirs(output_pathname, exist_ok=True)
	os.system(f"../../../pin -t ./obj-intel64/SGXTrace.so -o {output_path} -trace 1 -- ~/t2_2/password_checker_2 {guess}")	

def find_letter_positions(password_partial, ch):
	trace_path = f"/home/isl/t2_2/traces/trace_{ch}"
	iteration_idex = 0

	trace_file = open(trace_path)
	for line in trace_file:
		if "0x401d83" in line:
			password_partial[iteration_idex] = ch
		if "0x401d97" in line:
			iteration_idex += 1
	trace_file.close()
	return password_partial

def create_output_file(output_id, output):
	output_path = f"/home/isl/t2_2/output/oput_{output_id}"
	output_pathname = os.path.dirname(output_path)
	os.makedirs(output_pathname, exist_ok=True)
	with open(output_path, "w") as output_file:
		output_file.write(output)

def find_password_partial():
	password_partial = {}
	for ch in list(string.ascii_lowercase):
		guess = ch * 31
		create_trace(guess, ch)
		password_partial = find_letter_positions(password_partial, ch)	
	return password_partial

def password_gen(password_partial):
	password = ""
	for idx in range(1, max(password_partial.keys())+1):
		password += password_partial[idx]
	return password

def output_gen(password):
	status = ",complete"
	output = password+status
	print(output) 
	return output

check_command_ling_arg(sys.argv)
path = read_command_line_arg(sys.argv)
password_partial = find_password_partial()
password = password_gen(password_partial)
output = output_gen(password)
create_output_file(path, output)
shutil.rmtree("/home/isl/t2_2/traces")











