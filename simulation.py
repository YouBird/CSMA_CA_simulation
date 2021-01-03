# -*- coding: utf-8 -*-
"""
Spyderエディタ

これは一時的なスクリプトファイルです
"""

#coding: utf-8
import numpy as np
import time
import matplotlib.pyplot as plt
import math
import random

"""
@@@シミュレーター方針@@@
基本的にフラッグ参照や変更はクラス関数機能内で終わらせる
通信可否はフラッグ一本で管理(Do_not_transmit_Flag)
イベント時間とタイムスロットはメインで直接管理
CW減算は関数で、呼び出しはイベント処理部(メインループ)で管理
"""


"""
疑問点
APは各端末の試行回数を読み込み可能か
無線LANは送信試行回数を読み込み可能か
そもそも観測可能な情報は何か
再送回数は多分間接的な観測もできない
データパケットなり、送信総容量とか

"""

"""
直接的なパラメータ郡
条件を直接変更するときに直接弄るような変数
秒数はマイクロセカンド
容量はバイト固定
"""
TRANSMIT_TIME = 1100#[bpms]
SLOT_TIME = 20#[μs]　以下単位無しパラメータは基本μs
SIFS = 10
DIFS = 50
PREAMBLE_LENGTH = 18#[byte]
PLCP_HEADER_SIZE = 6#[byte]
DATA_FLAME_SIZE = 1430#[byte]
ACK_FLAME_SIZE = 14#[byte]
CW_MIN = 31#[タイムスロット]
CW_MAX = 1023#[タイムスロット]
RETRY_MAX = 7#[回]
SELFISH_RANGE = 32#セルフィッシュ端末が衝突時に生成する乱数の最大値　

TERMINAL_COUNTS = 5#端末数

"""
計算したパラメータ郡
パラメータ同士を計算したあとの「半ば固定数の変数」を入れてる
例:Ack送信に要する時間、データ送信に要する時間
"""
ACK_TRANSMIT_TIME = math.ceil(ACK_FLAME_SIZE / TRANSMIT_TIME) #Ack伝送時間
EIFS = math.ceil(SIFS + DIFS + ACK_TRANSMIT_TIME)
ALL_DATA_SIZE = PREAMBLE_LENGTH + PLCP_HEADER_SIZE + DATA_FLAME_SIZE
DATA_TRANSMIT_TIME = math.ceil(ALL_DATA_SIZE / TRANSMIT_TIME) #データ伝送時間
JUDGE_TIME = 10#実質固定だけど一応ここに
"""
各種フラッグ
論理値型
"""
Do_not_transmit_Flag = False#Falseで送信可能
Success_transmittion = False

"""
待ち時間専用のグローバル変数
"""
waiting_time = 0

"""
疑似遅延関数管理用の変数
ローカルだと都合が悪いのでグローバルに
"""
First_call = True


def waiting(time: int) -> None:
    """
    引数時間だけ、ただ待つ関数
    疑似遅延関数
    """
    global First_call
    global waiting_time

    if First_call:
        Do_not_transmit_Flag = True
        waiting_time = time
        First_call = False
        #print("waiting in First Call")
    else:
        if waiting_time > 0:
            waiting_time = waiting_time - 1
            #print("waiting in decreace")
        else:
            waiting_time = 0
            First_call = True
            Do_not_transmit_Flag = False
            #print("waiting in end")

class Terminal():

    def __init__(self):
        self.collision_window_minimum = CW_MIN
        self.CW = random.randint(1,self.collision_window_minimum)
        self.waiting_timeslot_count: int = 0
        self.try_transmit_flag = False
        self.collisions_count = 0
        self.temp_retry_count = 0
        self.transmit_sucsess_count = 0
        self.list_terminal_status = []
        self.selfish_flag = False

    def CW_dicreas(self):
        if self.CW >= 1:
            self.CW -= 1
            self.waiting_timeslot_count += 1
            self.list_terminal_status.append("W")
            #print("Waiting")
            #print(self.CW)
        else:
            pass

    def random_collision_window(self):
        self.collisions_count += 1
        if self.collisions_count > 7:
            self.CW = 1
            self.collisions_count = 0
            return 0
        self.collision_window_minimum = (self.collision_window_minimum + 1) * 2 ** self.collisions_count - 1
        if self.collision_window_minimum >= CW_MAX:
            self.collision_window_minimum = CW_MAX
        self.CW = random.randint(1, self.collision_window_minimum)
        self.list_terminal_status.append("C")
        #print("Collision")

    def transmit_DATA(self):
        Success_transmittion = True
        self.transmit_sucsess_count += 1
        self.CW = CW_MIN
        self.list_terminal_status.pop(-1)#末尾のWは余計なので削除
        self.list_terminal_status.append("S")
        self.collisions_count = 0
        #print("Success")
        waiting(DATA_TRANSMIT_TIME)
    

class Selfish_Terminal(Terminal):
    
    def __init__(self):
        super().__init__()
        self.selfish_flag = True
        self.collision_window_minimum = SELFISH_RANGE
    
    def random_collision_window(self):
        
        self.collision_window_minimum = 32
        self.CW = random.randint(1,self.collision_window_minimum)
        self.list_terminal_status.append("C")
        self.collisions_count += 1
        
    def transmit_DATA(self):
        Success_transmittion = True
        self.transmit_sucsess_count += 1
        self.CW = CW_MIN
        self.list_terminal_status.pop(-1)#末尾のWは余計なので削除
        self.list_terminal_status.append("S")
        self.collisions_count = 0
        #print("Success")
        waiting(DATA_TRANSMIT_TIME)


class Access_point:

    def __init__(self):
        pass

    def transmit_Ack(self):
        Success_transmittion = False
        waiting(ACK_TRANSMIT_TIME)


if __name__ == "__main__":
    start = time.time()
    TIME_SLOTS = 500000#500000μs
    try_terminal_count = 0

    #端末数3 とりあえず手動作成　完成時はfor文で生成するつもりで
    access_point = Access_point()
    terminal_1 = Terminal()
    terminal_2 = Terminal()
    terminal_3 = Terminal()
    #selfish_terminal = Selfish_Terminal()
   
    terminals = []
    for terminal in range(200):
        terminals.append(Terminal())
        
    #terminals.append(selfish_terminal)
    list_terminal_status = []
    try_terminals = []#送信試行端末リスト
    
    #for i in range(200):
    time_slot_time = 0


    for time_slot in range(int(TIME_SLOTS/SLOT_TIME)):#全観測時間内
        for slot_times_time in range(SLOT_TIME):

            if Do_not_transmit_Flag == False:#送信可能なら以下

                if Success_transmittion == True:#直前に送信成功ならAck送信
                    access_point.transmit_Ack()

                else:#データ送信できるかも
                    for terminal in terminals:#減算アンド送信端末を探索
                        if terminal.CW == 0:
                            terminal.try_transmit_flag = True
                            try_terminals.append(terminal)

                    if len(try_terminals) >= 2:#2台以上なら衝突
                        for collision_terminal in try_terminals:#衝突したらCWをランダムで生成
                            collision_terminal.random_collision_window()
                        waiting(EIFS)
                    elif len(try_terminals) == 1:#送信成功
                        try_terminals[0].transmit_DATA()
                    else:#0台　何もしない
                        pass
                    try_terminals.clear()
                    

            else:#送信不可能なら待つだけ
                waiting(waiting_time)
            
        for terminal in terminals:
            terminal.CW_dicreas()

            #タイムスロット内ここまで


        #観測時間終了
    #for terminal in terminals:
    #    print(terminal.list_terminal_status)
  
    print(terminals[-1].list_terminal_status)
    elapsed_time = time.time() - start
    print ("実行時間:{0}".format(elapsed_time) + "[sec]")

        
    """
    path_w = "aaaaa"　#←絶対パス入力
    
    with open(path_w, mode = "w") as f:
        
        f.write(str()+"回目の実行です")
        f.write()
    """
