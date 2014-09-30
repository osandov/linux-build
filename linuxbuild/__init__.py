import subprocess


def _prompt_yes_no(prompt, default='yes'):
    """
    Prompt yes or no to a question.
    """

    if default is None:
        default = ''
        prompt_yn = '[y/n]'
    elif default == 'yes':
        prompt_yn = '[Y/n]'
    elif default == 'no':
        prompt_yn = '[y/N]'
    else:
        raise ValueError('invalid default')
    while True:
        answer = input('%s %s ' % (prompt, prompt_yn)).strip().lower()
        if not answer:
            answer = default
        if answer.startswith('y'):
            return True
        elif answer.startswith('n'):
            return False


def _echo_call(args):
    """
    Make a subprocess.check_call and print the command being run.
    """

    print(' '.join(args))
    subprocess.check_call(args)
