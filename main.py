import datetime
import json
import ssl

import requests
import urllib3
import websocket

import asyncio
from aioconsole import ainput

urllib3.disable_warnings()


class SignSystem:
    def __init__(self):
        res = requests.post('https://192.168.2.9/login/', {'username': 'zhanghaoran', 'password': '123456'}, verify=False)
        self.session_cookie = res.cookies.get('django_session')
        self.websocket_url = "wss://192.168.2.9/ws/"
        self.ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        # noinspection PyArgumentList
        self.ws.settimeout(timeout=1)
        self.al_signin_sys = False
        self.connect_server()
        self.al_signin_usr = self.al_signin_sys
        self.can_run = True

    def connect_server(self):
        # 建立 WebSocket 连接
        self.ws.connect(self.websocket_url, header=[f"Cookie: django_session={self.session_cookie}", "clientVersion: 1.1.1"])  # header的参数必须写成list形式（源码里面有解释）
        user_info = self.receive_from_server('user_info')
        self.get_signin_stats()

    def send_to_server(self, message_type, receive_reply=True) -> (bool, dict):
        message2type = {'server_time': 'systemTime', 'sign_in': 'signIn', 'sign_out': 'signOut', 'user_info': 'userUpdate', 'message_box': 'showMessageBox',
                        'send_message': 'sendMessage'}
        message_to_server = json.dumps({'type': message2type[message_type]})
        try:
            # 测试连接是否被中断
            self.ws.send(json.dumps({"type": "systemTime"}))
            self.ws.recv()
        except (ConnectionAbortedError, websocket.WebSocketConnectionClosedException):
            self.connect_server()  # reconnect
        finally:
            self.ws.send(message_to_server)

        if receive_reply:
            return self.receive_from_server(message_type)
        else:
            return False, ''

    def receive_from_server(self, message_type: str) -> (bool, dict):
        message2type = {'server_time': 'systemTime', 'sign_in': 'signIn', 'sign_out': 'signOut', 'user_info': 'userUpdate', 'message_box': 'showMessageBox',
                        'send_message': 'sendMessage'}
        time_out_count = 3
        while time_out_count > 0:
            try:
                return_info = json.loads(self.ws.recv())
                if return_info.get('type') == message2type[message_type]:
                    if message_type == 'user_info' and return_info.get('message').get('data').get('name') != '张浩然':
                        continue
                    if return_info.get('message').get('result'):
                        return True, return_info
                    else:
                        return False, return_info
            except (ConnectionAbortedError, websocket.WebSocketConnectionClosedException):
                self.connect_server()
            except websocket.WebSocketTimeoutException:
                time_out_count -= 1
        else:
            return False, 'timeout!'

    def get_signin_stats(self):
        now_hour = datetime.datetime.now().hour
        which_noon = 'morning' if now_hour < 12 else 'afternoon' if now_hour < 18 else 'night'
        self.al_signin_sys = False
        flag, userinfo = self.send_to_server('user_info')
        if flag:
            sign_time_noon = userinfo.get('message').get('data').get(which_noon)
        else:
            return False
        if sign_time_noon:
            if sign_time_noon[-1] == '-':
                self.al_signin_sys = True
        return True

    def sign_in(self):
        flag, _ = self.send_to_server('sign_in')
        if not flag:
            print(_)
        return flag

    def sign_out(self):
        flag, _ = self.send_to_server('sign_out')
        if not flag:
            print(_)
        return flag

    def sign_auto(self):
        print('自动签到、签退系统，仅供辅助签入签出，请勿刷时长！！！')
        while True:
            choose = input(f'[{"×" if self.al_signin_sys else "1"}] 手动签入\t [{"×" if not self.al_signin_sys else "2"}] 手动签出\t [3] 开始自动签入签出\n')
            if choose == '1' and not self.al_signin_sys:
                if self.sign_in():
                    print('成功签入！')
                    self.al_signin_usr = True
                    self.al_signin_sys = True
                else:
                    print('失败，请手动操作！')
            if choose == '2' and self.al_signin_sys:
                if self.sign_out():
                    print('成功签出！')
                    self.al_signin_usr = False
                    self.al_signin_sys = False
                else:
                    print('失败，请手动操作！')
            if choose == '3':
                if not self.al_signin_usr:
                    print('请先签入！')
                    continue

                # 启动两个任务，分别是自动签入签出和非阻塞read
                self.can_run = True
                loop = asyncio.get_event_loop()
                tasks = [loop.create_task(self.get_input()), loop.create_task(self.auto_sign_inout())]
                loop.run_until_complete(asyncio.wait(tasks))

    async def get_input(self):
        print('正在执行自动签入签出，按q退出！')
        while True:
            info = await ainput()
            if info.lower() == 'q':
                self.can_run = False
                break

    async def auto_sign_inout(self):
        """
        在时间点自动签入签出

        采用异步方式，主要为了非阻塞的输入。在0点、12点、18点时候自动签入签出
        :return:
        """
        # 定义特定时间点和对应操作的映射关系
        time_mapping = {
            '00:00': False,
            '11:59': True,
            '12:00': False,
            '17:59': True,
            '18:00': False,
            '23:58': True,  # 历史遗留问题，不让23:59签出，我也不知道为什么
        }

        # 根据当前时间执行对应的操作
        while True:
            # 获取当前时间的小时和分钟
            current_time = datetime.datetime.now().strftime('%H:%M')
            if self.al_signin_usr and current_time in time_mapping and self.al_signin_sys == time_mapping[current_time]:
                if time_mapping[current_time]:
                    # out
                    flag = self.sign_out()
                    if flag:
                        print(f'{current_time}签出成功！')
                    else:
                        print(f'{current_time}签出失败，请手动操作！')
                else:
                    # in
                    flag = self.sign_in()
                    if flag:
                        print(f'{current_time}签入成功！')
                    else:
                        print(f'{current_time}签入失败，请手动操作！')
                self.al_signin_sys = not self.al_signin_sys  # 反转flag
            else:
                await asyncio.sleep(1)
            if not self.can_run:
                break


if __name__ == '__main__':
    t = SignSystem()
    t.sign_auto()
