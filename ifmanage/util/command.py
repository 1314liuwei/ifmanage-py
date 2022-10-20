from subprocess import PIPE, Popen


def popen(command, shell=None, input=None, timeout=None, env=None, stdout=PIPE, stderr=PIPE, decode='utf-8'):
    """
    popen is a wrapper helper aound subprocess.Popen
    with it default setting it will return a tuple (out, err)
    out: the output of the program run
    err: the error code returned by the program

    it can be affected by the following flags:
    shell:   do not try to auto-detect if a shell is required
             for example if a pipe (|) or redirection (>, >>) is used
    input:   data to sent to the child process via STDIN
             the data should be bytes but string will be converted
    timeout: time after which the command will be considered to have failed
    env:     mapping that defines the environment variables for the new process
    stdout:  define how the output of the program should be handled
              - PIPE (default), sends stdout to the output
              - DEVNULL, discard the output
    stderr:  define how the output of the program should be handled
              - None (default), send/merge the data to/with stderr
              - PIPE, popen will append it to output
              - STDOUT, send the data to be merged with stdout
              - DEVNULL, discard the output
    decode:  specify the expected text encoding (utf-8, ascii, ...)
             the default is explicitely utf-8 which is python's own default

    usage:
    get both stdout and stderr: popen('command', stdout=PIPE, stderr=STDOUT)
    discard stdout and get stderr: popen('command', stdout=DEVNUL, stderr=PIPE)
    """

    use_shell = shell
    stdin = None
    if shell is None:
        use_shell = False
        if ' ' in command:
            use_shell = True
        if env:
            use_shell = True

    if input:
        stdin = PIPE
        input = input.encode() if type(input) is str else input

    p = Popen(command, stdin=stdin, stdout=stdout, stderr=stderr, env=env, shell=use_shell)

    pipe = p.communicate(input, timeout)

    pipe_out = b''
    if stdout == PIPE:
        pipe_out = pipe[0]

    pipe_err = b''
    if stderr == PIPE:
        pipe_err = pipe[1]

    str_out = pipe_out.decode(decode).replace('\r\n', '\n').strip()
    str_err = pipe_err.decode(decode).replace('\r\n', '\n').strip()
    return p.returncode, str_out, str_err,


def cmd(command, flag='', shell=None, input=None, timeout=None, env=None, stdout=PIPE, stderr=PIPE, decode='utf-8',
        raising=None, message='', expect=None):
    """
    A wrapper around popen, which returns the stdout and
    will raise the error code of a command

    raising: specify which call should be used when raising
             the class should only require a string as parameter
             (default is OSError) with the error code
    expect:  a list of error codes to consider as normal
    """
    if expect is None:
        expect = [0]
    code, decoded, _ = popen(command, stdout=stdout, stderr=stderr, input=input, timeout=timeout, env=env,
                             shell=shell, decode=decode, )
    if code not in expect:
        feedback = message + '\n' if message else ''
        feedback += f'failed to run command: {command}\n'
        feedback += f'returned: {decoded}\n'
        feedback += f'exit code: {code}'
        if raising is None:
            # error code can be recovered with .errno
            raise OSError(code, feedback)
        else:
            raise raising(feedback)
    return decoded

def is_systemd_service_active(service):
    """
    Test is a specified systemd service is activated.
    Returns True if service is active, false otherwise.
    Copied from: https://unix.stackexchange.com/a/435317
    """
    tmp = cmd(f'systemctl show --value -p ActiveState {service}')
    return bool((tmp == 'active'))