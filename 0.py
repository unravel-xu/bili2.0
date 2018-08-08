from config_loader import ConfigLoader
from task import RaffleHandler, Task
import os
import sys
from user import User
import asyncio
from printer import Printer
import connect
import bili_console
import threading
from cdn import Host
from super_user import SuperUser

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()
fileDir = os.path.dirname(os.path.realpath('__file__'))
file_color = f'{fileDir}/config/color.toml'
file_user = f'{fileDir}/config/user.toml'
file_bili = f'{fileDir}/config/bili.toml'
file_ip = f'{fileDir}/config/ips.toml'
cfg = ConfigLoader(file_color, file_user, file_bili, file_ip)

dict_user = cfg.read_user()
dict_bili = cfg.read_bili()
dict_color = cfg.read_color()
dict_ip = cfg.read_ip()
Printer(dict_color, dict_user['print_control']['danmu'], dict_user['platform']['platform'])


task_control = dict_user['task_control']
if len(dict_user['users']) < 10:
    users = [User(i, user_info, dict_bili, task_control, False) for i, user_info in enumerate(dict_user['users'])]
else:
    host = Host(dict_ip['list_ips'])
    loop.run_until_complete(host.proxies_filter())
    users = [User(i, user_info, dict_bili, task_control, True) for i, user_info in enumerate(dict_user['users'])]


danmu_connection = connect.connect(dict_user['other_control']['default_monitor_roomid'])
list_raffle_connection = [connect.RaffleConnect(i) for i in range(1, 5)]
list_raffle_connection_task = [i.run() for i in list_raffle_connection]

var_super_user = SuperUser(users[0])
raffle = RaffleHandler(users, var_super_user, loop)
normal_task = Task(users, var_super_user, loop)


queue = asyncio.Queue()
var_console = bili_console.Biliconsole(loop, queue, var_super_user, users)
console_thread = threading.Thread(target=var_console.controler)
console_thread.start()

tasks = [
    raffle.join_raffle(),
    # normal_task.heartbeat(),
    danmu_connection.run(),
    normal_task.run(),
    var_console.run()
]


loop.run_until_complete(asyncio.wait(tasks + list_raffle_connection_task))
console_thread.join()
