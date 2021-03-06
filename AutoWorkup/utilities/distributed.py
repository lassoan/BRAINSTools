def load_cluster(modules=[]):
    if len(modules) > 0:
        module_list = []
        for module in modules:
            module_list.append("module load {name}".format(name=module))
        assert len(modules) == len(module_list)
        return '\n'.join(module_list)
    return ''


def source_virtualenv(virtualenv=''):
    if virtualenv is None:
        return ''
    assert virtualenv != ''
    return "source {0}".format(virtualenv)


def prepend_env(environment={}):
    import os
    export_list = []
    for key, value in environment.items():
        export_list.append("export {key}={value}{sep}${key}".format(key=key, value=value, sep=os.pathsep))  # Append to variable
    return '\n'.join(export_list)


def create_global_sge_script(cluster, environment):
    """
    This is a wrapper script for running commands on an SGE cluster
    so that all the python modules and commands are pathed properly

    >>> import os
    >>> nomodules = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TestSuite', 'node.sh.template.nomodules'), 'r')
    >>> create_global_sge_script({'modules':[]}, {'virtualenv':'/path/to/virtualenv', 'env': os.environ}).split('\n')[0]
    True
    >>> create_global_sge_script({'modules':[]}, {'virtualenv':'/path/to/virtualenv', 'env': os.environ}).split('\n')[0] == '#!/bin/bash FAIL'

    """
    import os
    from string import Template
    import sys

    sub_dict = dict(LOAD_MODULES=load_cluster(cluster['modules']),
                    VIRTUALENV=source_virtualenv(environment['virtualenv']),
                    EXPORT_ENV=prepend_env(environment['env']))
    with open(os.path.join(os.path.dirname(__file__), 'node.sh.template')) as fid:
        tpl = fid.read()
    retval = Template(tpl).substitute(sub_dict)
    return retval


def modify_qsub_args(queue, memory, minThreads=1, maxThreads=None, stdout='/dev/null', stderr='/dev/null', hard=True):
    """
    Outputs qsub_args string for Nipype nodes

    >>> modify_qsub_args('test', 200, 5)
    -S /bin/bash -cwd -pe smp 5 -l mem_free=200 -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 200, 5, hard=False)
    -S /bin/bash -cwd -pe smp 5- -l mem_free=200 -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 800, 5, 7)
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=800 -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 800, 5, 7, hard=False)
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=800 -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 1000, 5, 7, stdout='/my/path', stderr='/my/error')
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=1000 -o /my/path -e /my/error test FAIL

    """
    if maxThreads is None:
        if hard:
            format_str = '-S /bin/bash -cwd -pe smp {mint} -l mem_free={mem} -o {stdout} -e {stderr} {queue}'
        else:
            format_str = '-S /bin/bash -cwd -pe smp {mint}- -l mem_free={mem} -o {stdout} -e {stderr} {queue}'
        return format_str.format(mint=minThreads, mem=memory, stdout=stdout, stderr=stderr, queue=queue)
    else:
        format_str = '-S /bin/bash -cwd -pe smp {mint}-{maxt} -l mem_free={mem} -o {stdout} -e {stderr} {queue}'
        return format_str.format(mint=minThreads, maxt=maxThreads, mem=memory, stdout=stdout, stderr=stderr, queue=queue)
