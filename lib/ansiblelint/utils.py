import os
import glob
import imp
import ansible.utils


def load_plugins(directory):
    result = []
    fh = None

    for pluginfile in glob.glob(os.path.join(directory, '[A-Za-z]*.py')):

        pluginname = os.path.basename(pluginfile.replace('.py', ''))
        try:
            fh, filename, desc = imp.find_module(pluginname, [directory])
            mod = imp.load_module(pluginname, fh, filename, desc)
            obj = getattr(mod, pluginname)()
            result.append(obj)
        finally:
            if fh:
                fh.close()
    return result


def tokenize(line):
    result = list()
    tokens = line.lstrip().split(" ")
    if tokens[0] == '-':
        tokens = tokens[1:]
    if tokens[0] == 'action:':
        tokens = tokens[1:]
    command = tokens[0].replace(":", "")

    args = list()
    kwargs = dict()
    for arg in tokens[1:]:
        if "=" in arg: 
            kv = arg.split("=",1) 
            kwargs[kv[0]] = kv[1]
        else:
            args.append(arg)
    return (command, args, kwargs)

def _playbook_items(pb_data):
    if isinstance(pb_data, dict):
        return pb_data.items()
    elif not pb_data:
        return []
    else:
        return [item for play in pb_data for item in play.items()]

def find_children(playbook):
    if not os.path.exists(playbook):
        return []
    results = []
    basedir = os.path.dirname(playbook)
    pb_data = ansible.utils.parse_yaml_from_file(playbook)
    items = _playbook_items(pb_data)
    for item in _playbook_items(pb_data):
        for child in play_children(basedir, item):
            results.append({
                'path': ansible.utils.path_dwim(basedir, child['path']),
                'type': child['type']
            })
    return results


def play_children(basedir, item):
    delegate_map = { 
            'tasks': _taskshandlers_children,
            'include': _include_children,
            'roles': _roles_children,
            'dependencies': _roles_children,
            'handlers': _taskshandlers_children,
    }
    (k,v) = item
    if k in delegate_map:
        return delegate_map[k](basedir, k,v)
    else:
        return []

def _include_children(basedir, k, v):
    return [{ 'path': ansible.utils.path_dwim(basedir, v), 'type': 'tasks' }]

def _taskshandlers_children(basedir, k, v):
    return [{ 'path': ansible.utils.path_dwim(basedir, th['include']),
              'type': 'tasks' }
            for th in v if 'include' in th.items()]

def _roles_children(basedir, k, v):
    results = []
    for role in v: 
        if isinstance(role, dict):
            results.extend(_look_for_role_files(basedir, role['role']))
        else:
            results.extend(_look_for_role_files(basedir, role))
    
    return results

def _rolepath(basedir, role):
    if os.path.isabs(role):
        return role
    # if included from a playbook
    pbrolepath = ansible.utils.path_dwim(basedir, os.path.join('roles', role))
    if os.path.exists(pbrolepath):
        return pbrolepath
    # if included from roles/meta/main.yml
    gpdir = os.path.normpath(os.path.join(basedir, '..', '..'))
    if os.path.basename(gpdir) == 'roles':
        rolepath = os.path.join(gpdir, role)
        return rolepath
    return basedir


def _look_for_role_files(basedir, role):
    results = []
    for th in ['tasks', 'handlers', 'meta']: 
        thpath = os.path.join(_rolepath(basedir, role), th, 'main.yml')
        if os.path.exists(thpath):
            results.append({ 'path': thpath, 'type': th })
    return results

def rolename(filepath):
    idx = filepath.find('roles/')
    if idx < 0:
        return ''
    role = filepath[idx+6:]
    role = role[:role.find('/')]
    return role
