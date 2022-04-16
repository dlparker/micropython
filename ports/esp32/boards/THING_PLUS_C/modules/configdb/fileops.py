import os
import uos
import json
config_root = "/configdb_data"

def save_config(root_name, contents):
    found = False
    try:
        uos.stat(config_root)
        found = True
    except OSError as e:
        pass
    if not found:
        os.mkdir(config_root)
        
    # if json is going to fail, do it early
    buff = json.dumps(contents)
    last_name = config_root +"/"+ root_name + ".last"
    cur_name = config_root +"/"+ root_name + ".cur"

    first_time = False
    try:
        uos.stat(cur_name)
    except OSError as e:
        first_time = True
        pass
    try:
        uos.stat(last_name)
        os.remove(last_name)
    except OSError as e:
        pass
    try:
        uos.stat(cur_name)
        os.rename(cur_name, last_name)
    except OSError as e:
        pass
    with open(cur_name, 'w') as f:
        f.write(buff)
    
                            
def load_config(root_name):
    last_name = config_root +"/"+ root_name + ".last"
    cur_name = config_root +"/"+ root_name + ".cur"

    data = None
    try:
        with open(cur_name, 'r') as f:
            data = json.loads(f.read())
    except Exception as e:
        print(f"problem with current config {cur_name}")
        print(e)
        try:
            with open(last_name, 'r') as f:
                data = json.loads(f.read())
            # let's save it since the current one is junk
            save_config(root_name, data)
        except Exception as e2:
            print(f"problem with last config {last_name}")
            print(e2)
    return data

        
    
