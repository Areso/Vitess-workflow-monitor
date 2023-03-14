import pystray
from time import sleep
from time import time
from PIL import Image, ImageDraw
from threading import Thread
from subprocess import Popen
import subprocess
import json


def red_image():
    image = Image.new('RGB', (64, 64), 'red')
    dc = ImageDraw.Draw(image)
    dc.rectangle((0, 0, 64, 64), fill='red')
    return image


def green_image():
    image = Image.new('RGB', (64, 64), 'green')
    dc = ImageDraw.Draw(image)
    dc.rectangle((0, 0, 64, 64), fill='green')
    return image


def get_output_from_cli():
    command = "vtctlclient --server 127.0.0.1:15999 Workflow user.move2vitess21 show"
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    workflow_show2 = (p.communicate())
    workflow_obj = json.loads(workflow_show2[0])
    shards = list(workflow_obj["ShardStatuses"].keys())
    if len(shards_pos) == 0:
        for every_shard in shards:
            shards_pos[every_shard] = []
        print(shards_pos)
    fail_bl = False
    global i
    for every_shard in shards:
        shard_details = workflow_obj["ShardStatuses"][every_shard]
        shard_state   = shard_details["PrimaryReplicationStatuses"][0]["State"]
        shard_gtids   = shard_details["PrimaryReplicationStatuses"][0]["Pos"]
        shards_pos[every_shard].append(shard_gtids.split(','))
        if shard_state == "Error":
            fail_bl = True
        shard_message = shard_details["PrimaryReplicationStatuses"][0]["Message"]
        if fail_bl:
            print(shard_state, shard_message)
            pass
    return fail_bl


def get_short_shardname(shard):
    delimiter_pos = shard.find("/")
    shard_short = shard[:delimiter_pos]
    return shard_short


def check_gtids():
    status = []
    update_icon = False
    for every_shard in list(shards_pos.keys()):
        list_pos = shards_pos[every_shard]
        if (len(list_pos)) >= 11:
            current_state  = list_pos[len(list_pos)-1]
            previous_state = list_pos[len(list_pos)-11]
            the_diff = find_diff(current_state, previous_state)
            shard = get_short_shardname(every_shard)
            status.append({shard: the_diff})
            update_icon = True
    if update_icon:
        printable_status = str(status).replace("[", "").replace("]", "").replace("{", "")
        printable_status = printable_status.replace("}", "").replace("'", "").replace(".0", "")
        icon.menu = pystray.Menu(
                pystray.MenuItem(
                    printable_status, None, enabled=False,
                )
            )
        icon.update_menu()
        print(status)


def find_diff(actual_list, db_list):
    s = set(db_list)
    temp3 = [x for x in actual_list if x not in s]
    flag1 = False
    flag2 = False
    if len(temp3) != 0:
        gtid_start_pos = str(temp3).rfind('-')
        new_gtid       = str(temp3)[gtid_start_pos+1:-2]
        flag1 = True
    s2 = set(actual_list)
    temp4 = [x for x in db_list if x not in s2]
    if len(temp4) != 0:
        gtid_start_pos = str(temp4).rfind('-')
        old_gtid = str(temp4)[gtid_start_pos+1:-2]
        flag2 = True
    if flag1 and flag2:
        try:
            total_diff = round((int(new_gtid)-int(old_gtid))/60, 0)
        except ValueError:
            total_diff = "some err"
    else:
        total_diff = "some err"
    return total_diff


def task():
    global i
    while True:
        anyerrors = get_output_from_cli()
        if anyerrors:
            icon.icon = red_image()
        else:
            icon.icon = green_image()
        sleep(6)  # in seconds
        if i % 10 == 0:
            print("=====")
            icon.visible = True
            check_gtids()
        i += 1


if __name__ == '__main__':
    icon = pystray.Icon(
        name='Vitess Workflow Monitor',
        menu=pystray.Menu(
            pystray.MenuItem(
                "TPS, updated every 60 seconds", None, enabled=False,
            )
        ),
        icon=red_image())
    i = 0
    shards_pos = {}
    workflow_checker_routine = Thread(target=task)
    workflow_checker_routine.start()
    icon_routine = Thread(target=icon.run())
    icon_routine.start()
