
import json


def get_cpu_usage(server):
    # call zabbix API

    resp = {
        "server": server,
        "cpu": 4,
        "threshold": 90,
        "duration": 900
    }

    return json.dumps(resp)

def get_power_usage(rack):
    # call zabbix API
    resp = {
        "rack": rack,
        "power": 500,  
    }
    return json.dumps(resp)