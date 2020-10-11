import os
import time
import resource
import subprocess
from glob import glob

# Maximal time for execution of subprocesses (in secs).
TIME_LIMIT = 1 # 1 second
# Maximal virtual memory for subprocesses (in bytes).
MAX_VIRTUAL_MEMORY = 64 * 1024 * 1024 # 64 MB

def limit_virtual_memory():
    # The tuple below is of the form (soft limit, hard limit). Limit only
    # the soft part so that the limit can be increased later (setting also
    # the hard limit would prevent that).
    # When the limit cannot be changed, setrlimit() raises ValueError.
    resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, resource.RLIM_INFINITY))

def launch_process(code_file, test_file):
    with open(test_file, "r") as input_file:
        process = subprocess.Popen(['python3', code_file], 
            stdin=input_file,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            preexec_fn=limit_virtual_memory,
            text = True)
    return process

def run_code_on_test(code_file, test_file):
    process = launch_process(code_file, test_file)
    stdout, stderr = '', 'Something went wrong. Contact administrator and report about that.'
    try:
        process.wait(TIME_LIMIT)
        stdout, stderr = process.communicate()
    except subprocess.TimeoutExpired:
        process.kill()
        return '', 'Time Limit Exception'
    return stdout, stderr

def run_code_on_tests(code_file, task, debug=False):
    tests = sorted(glob("tests/" + task + "/input/*.txt"))
    for i, test_file in enumerate(tests):
        stdout, stderr = run_code_on_test(code_file, test_file)
        output = stdout.strip(" ").strip("\n")
        if stderr != '':
            return i, len(tests), '`' + stderr + '`'
        with open(test_file.replace("input", "output"), "r") as reference_file:
            reference = reference_file.read().strip(" ").strip("\n")
        if reference != output:
            message = '`Wrong answer!`  \n'
            if i == 0:
                message += f'очікуваний вихід програми:  \n**{reference}**  \n'
                message += f'отриманий вихід програми:  \n**{output}**  \n'
            return i, len(tests), message
    
    return len(tests), len(tests), ''


if __name__== '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('task', type=str)
    parser.add_argument('--code', type=str, default=None)
    args = parser.parse_args()
    task = args.task
    code = f'tests/{task}/{task}.py' if args.code is None else args.code
    result = run_code_on_tests(code, task, debug=True)
    print(result)