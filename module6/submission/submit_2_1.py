import sys
import os

def check_command_ling_arg(arguments):
	if len(sys.argv) != 3:
		print("Number of command line arguments must be 3!")
		exit()
		return False
	return True

def read_command_line_arg(arguments):
	path = sys.argv[1]
	output_id = sys.argv[2]
	return path, output_id

def new_char(guess, char_idx, guess_too_large):
	if not guess_too_large:
		new_char = chr(ord(guess) + char_idx)
	else:	
		new_char = chr(((ord(guess) - ord('a') + char_idx) % 26) + ord('a'))
	return new_char

def find_password_and_status(path):
	password = ""
	status = ""
	traces = os.listdir(path)
	is_guess_correct = False
	password_partial = {}

	for single_trace in traces:
		iteration_idx = 0
		guess_too_large = False
		char_idx = 0

		trace_file = open(path + "/" + single_trace)
		for line in trace_file:
			if "0x4012a8" in line:
				is_guess_correct = True
			if "0x40126f" in line:
				guess_too_large = True
			if "0x401211" in line:
				password_partial[iteration_idx] = single_trace[iteration_idx - 1]
			if "0x401286" in line:
				char_idx += 1
			if "0x401292" in line:
				if char_idx > 0:
					new_char(single_trace[iteration_idx - 1], char_idx - 1, guess_too_large)
					password_partial[iteration_idx] = new_char(single_trace[iteration_idx - 1], char_idx - 1, guess_too_large)
				guess_too_large = False					
				char_idx = 0
				iteration_idx += 1
		trace_file.close()

	for idx in range(0, len(password_partial)):
		if idx+1 in password_partial:
			password += password_partial[idx+1]
		else:
			password += "_"
			is_guess_correct = False

	if is_guess_correct:
		status += ",complete"
	else:
		status += ",partial"

	print(password + status)
	return password + status

def create_output_file(output_id, output):
	output_path = f"/home/isl/t2_1/output/oput_{output_id}"
	output_pathname = os.path.dirname(output_path)
	os.makedirs(output_pathname, exist_ok=True)
	with open(output_path, "w") as output_file:
		output_file.write(output)

check_command_ling_arg(sys.argv)
path, output_id = read_command_line_arg(sys.argv)
output = find_password_and_status(path)
create_output_file(output_id, output)
