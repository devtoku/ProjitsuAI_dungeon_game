'''
AIの作成は1020行目あたりから始まってます。
❗❗❗というエクスクラメーションマークで囲まれた範囲がそれです。
AIの検証を行うためのコードはゲームループのあとに書いています。
'''

import copy
import random

#ルール文
RULE_TEXT = """
・目的
    敵に見つからないように鍵を見つけてから金庫を見つけ出しスタート位置に戻ることが目的。
    アイテムは視野に入った時にマップに表示される。武器を使って敵を気絶させることも可能。

・操作方法
        W: 上,　 A: 左, 　S:下, 　D: 右
        入力無し:　その場で待機(ターン経過)
        rule　　: ルールを表示する

・プレイヤー
    1ターン1マスだけ上下左右に移動できる。
    視野は上下左右の壁までで、一度見えた場所は記録される。
    ただし、敵の位置と向きは見える。
    移動できる最大数は80ターン、それを超えたらゲームオーバー。
    同じマスで待機することも可能。
    主人公は敵よりも先に行動する。

・敵
    基本は1ターンに1マス移動する。敵は体の向きを90度変えるのにも1ターン使う。
    基本的には決まった通路を一直線に往復している。
    行き止まりでは通路がある方向優先で方向転換(1ターン90度ごと)する。どちらも壁だったり回転する向きに迷った場合は時計回りで回転する。
    敵の視野は前方向の壁まで。
    プレイヤーを見つけた場合：
      プレイヤーが視界にいる間、2マス移動で追いかける。
      プレイヤーが視界にいない場合は、1マス移動で追いかける。
      プレイヤーが最後に視界にいたところまで行き、プレイヤーが逃げた方向を向く。
      プレイヤーを見失った場合は元の警備ルートに戻る。
    気絶した場合はそのマスにずっと待機するが、気絶している敵は踏み越えられる。
    気絶した後にプレイヤーが金庫の機密文書を盗んだ場合、復活する。
    敵同士はぶつからず、すり抜けられる。
    敵同士は連絡を取り合わない。
    気絶から復活しても行動パターンは変わらない。
    敵はプレイヤーよりも後に行動する。

・アイテム
        アイテムがあるマスは通路扱い。
    武器
        持っていると接敵した際、敵を気絶させられる。(1回で壊れる)
        地図上では「W」と表示される。
    金庫
        機密文書が入っているという設定。(鍵付)
        地図上では「B」と表示される。
    鍵
        金庫を開くために必要
        地図上では「K」と表示される。

・勝利条件
　　80ターン以内に金庫の機密文書を持ち、スタート地点まで戻る。
・敗北条件
　　武器を持たずに敵と接触する。
　　または、81ターン以上移動する。
"""
#マップサイズ
MAP_X, MAP_Y = 7, 7

#マップの地形。部屋、壁、入り口
ROOM = 0
WALL = 1
START = 2

#人間の向き
NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

#人間の種類
SPY = 0
ENEMY_1, ENEMY_2 = 1, 2

#アイテムの種類
WEAPON = 0
KEY = 1
SAFE = 2
DOCUMENT = 3

#アイテムの有無
NOT_HAVE = 0
HAVE = 1

#スパイの状態
ALIVE = 0
DEAD = 1

#敵の状態
WAKE_UP = 0
SLEEP = 1
TRACKING = 2
GOING_BACK = 3
GONE = 13

#敵のmov_pow
STOP = 0
WALK = 1
RUN = 2

#ゲームの状態
NOT_CLEARED = 0
CLEARED = 1
FAILED = 2


#敵の初期方向
ENEMY_1_DIRECTION = WEST
ENEMY_2_DIRECITON = SOUTH

#アイテムの発見の状態
NOT_FOUNDED = 0
FOUNDED = 1
USED = 2

#アイテム発見か否かリストの初期状態
ITEM_FOUND_LIST = [NOT_FOUNDED, NOT_FOUNDED, NOT_FOUNDED] #武器、鍵、秘密文書の順

#マップ情報のプレイヤーへの開示の状態
CLOSED = 0
OPEN = 1

#警備兵の最大視野
SIGHT = 7

global_userMap = "" #外部からユーザーマップを呼び出せるようにするためのグローバル変数
other_gameInfo = ""#外部からその他のゲーム情報を呼び出せるようにするためのグローバル変数


#-----デフォルトのためのグローバル変数定義-----
#ターン上限
MAX_TURNS = 80
#初期座標群 (x, y)
START_POSITION = [7, 7]
WEAPON_POSITION = [7, 2]
KEY_POSITION = [1, 6]
SAFE_POSITION = [1, 1]
SPY_POSITION = [7, 7]
ENEMY_1_POSITION = [7, 3]
ENEMY_2_POSITION = [1, 3]

#No.1
#警備員の警備ルート
NORMAL_ROOT_1 = [[1, 3], [2, 3], [3, 3], [4, 3], [5, 3], [6, 3], [7, 3]]
NORMAL_ROOT_2 = [[1, 3], [1, 4], [1, 5], [1, 6], [1, 7]]

#警備兵が通常取りうる向きのリスト
NORMAL_DIR_1 = [EAST, WEST]
NORMAL_DIR_2 = [NORTH, SOUTH]

#マップ情報
MAP_LIST = [[1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 1],
            [1, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 0, 1, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 1, 0, 0, 0, 1, 0, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1]]

#マップの見えてるか見えてないかの情報の初期状態
MAP_OPEN = [[[1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 1, 1],
            [1, 0, 0, 0, 0, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1]]]

#-----------------------------------
#難易度
DIFFICULTY = None

#目的を表す変数
PUR_NAN = 0
PUR_KEY = 1
PUR_BOX = 2
PUR_BACK = 3

#マップを選択する関数
def pick_map():
    global MAX_TURNS, START_POSITION, WEAPON_POSITION, KEY_POSITION, SAFE_POSITION,\
    SPY_POSITION, ENEMY_1_POSITION, ENEMY_2_POSITION, NORMAL_ROOT_1, NORMAL_ROOT_2,\
    NORMAL_DIR_1, NORMAL_DIR_2, ENEMY_1_DIRECTION, ENEMY_2_DIRECITON,\
    MAP_LIST, MAP_OPEN, DIFFICULTY
    print("-" * 50)
    pick_num = None #マップ選択に関する部分
    while True:
        map_existed = ["0", "1", "2", "7"]
        #pick_num = input("【7(VERY_EASY), 0(EASY), 1(NORMAL), 2(HARD)のいずれかを入力してマップを選択】 >>")
        pick_num = "7"
        if pick_num in map_existed:
            print(f"あなたは【{pick_num}番】のマップを選択しました。") 
            break
        else:
            print("存在するマップ番号(0, 1, 2 or 7)を選んでください！")
            continue
    
    if pick_num == "7":
        MAX_TURNS = 80
        #初期座標群
        START_POSITION = [7, 7]
        WEAPON_POSITION = [6, 5]
        KEY_POSITION = [4, 5]
        SAFE_POSITION = [1, 7]
        SPY_POSITION = [7, 7]
        ENEMY_1_POSITION = [1, 2]
        ENEMY_2_POSITION = [1, 6]

        #No.1
        #警備員の警備ルート
        NORMAL_ROOT_1 = [[1, 1], [1, 2], [1, 3]]
        NORMAL_ROOT_2 = [[1, 5], [1, 6], [1, 7]]

        #警備兵が通常取りうる向きのリスト
        NORMAL_DIR_1 = [NORTH, SOUTH]
        NORMAL_DIR_2 = [NORTH, SOUTH]
        #警備兵の初期方向
        ENEMY_1_DIRECTION = SOUTH
        ENEMY_2_DIRECITON = SOUTH

        #マップ情報
        MAP_LIST = [[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 0, 1, 0, 0, 1],
                    [1, 0, 1, 0, 0, 1, 0, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 1, 1, 1, 1, 0, 1, 1, 1],
                    [1, 0, 0, 0, 0, 0, 1, 0, 1],
                    [1, 0, 1, 0, 1, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 1, 0, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]

        #マップの見えてるか見えてないかの情報の初期状態
        MAP_OPEN = [[[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]]
        DIFFICULTY = "VERY_EASY"

    elif pick_num == "0":
        #No.1
        MAX_TURNS = 80
        #初期座標群
        START_POSITION = [7, 7]
        WEAPON_POSITION = [7, 2]
        KEY_POSITION = [1, 6]
        SAFE_POSITION = [1, 1]
        SPY_POSITION = [7, 7]
        ENEMY_1_POSITION = [7, 3]
        ENEMY_2_POSITION = [1, 3]

        #No.1
        #警備員の警備ルート
        NORMAL_ROOT_1 = [[1, 3], [2, 3], [3, 3], [4, 3], [5, 3], [6, 3], [7, 3]]
        NORMAL_ROOT_2 = [[1, 3], [1, 4], [1, 5], [1, 6], [1, 7]]

        #警備兵が通常取りうる向きのリスト
        NORMAL_DIR_1 = [EAST, WEST]
        NORMAL_DIR_2 = [NORTH, SOUTH]
        #警備兵の初期方向
        ENEMY_1_DIRECTION = WEST
        ENEMY_2_DIRECITON = SOUTH


        #マップ情報
        MAP_LIST = [[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 0, 1, 0, 0, 1],
                    [1, 1, 1, 0, 1, 1, 1, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 1, 1, 0, 1, 0, 1, 1],
                    [1, 0, 0, 0, 1, 0, 0, 0, 1],
                    [1, 0, 1, 0, 0, 0, 1, 0, 1],
                    [1, 0, 0, 0, 1, 0, 0, 0, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]

        #マップの見えてるか見えてないかの情報の初期状態
        MAP_OPEN = [[[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 0, 0, 0, 0, 1, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]]
        DIFFICULTY = "EASY"

    elif pick_num == "1":
        #No.2
        MAX_TURNS = 80
        #初期座標群
        START_POSITION = [7, 7]
        WEAPON_POSITION = [3, 7]
        KEY_POSITION = [7, 1]
        SAFE_POSITION = [1, 2]
        SPY_POSITION = [7, 7]
        ENEMY_1_POSITION = [6, 4]
        ENEMY_2_POSITION = [3, 3]

        #No.2
        #警備員の警備ルート
        NORMAL_ROOT_1 = [[1, 4],[2, 4], [3, 4], [4, 4], [5, 4], [6, 4]]
        NORMAL_ROOT_2 = [[3, 1], [3, 2], [3, 3], [3, 4], [3, 5],[3, 6]]

        #警備兵が通常取りうる向きのリスト
        NORMAL_DIR_1 = [EAST, WEST]
        NORMAL_DIR_2 = [NORTH, SOUTH]
        #警備兵の初期方向
        ENEMY_1_DIRECTION = WEST
        ENEMY_2_DIRECITON = SOUTH


        #マップ情報
        MAP_LIST = [[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 1, 1, 0, 0, 0, 1],
                    [1, 0, 1, 0, 0, 0, 1, 0, 1],
                    [1, 0, 1, 0, 1, 0, 1, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 1, 1, 0, 1, 1, 0, 1, 1],
                    [1, 0, 0, 0, 1, 0, 0, 0, 1],
                    [1, 0, 1, 0, 0, 0, 1, 0, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]

        #マップの見えてるか見えてないかの情報の初期状態
        MAP_OPEN = [[[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]]
        DIFFICULTY = "NORMAL"

    elif pick_num == "2":
        MAX_TURNS = 80
        #初期座標群
        START_POSITION = [7, 7]
        WEAPON_POSITION = [1, 7]
        KEY_POSITION = [1, 1]
        SAFE_POSITION = [6, 1]
        SPY_POSITION = [7, 7]
        ENEMY_1_POSITION = [2, 3]
        ENEMY_2_POSITION = [3, 4]

        #警備員の警備ルート
        NORMAL_ROOT_1 = [[1, 3],[2, 3], [3, 3], [4, 3], [5, 3], [6, 3], [7, 3]]
        NORMAL_ROOT_2 = [[3, 3], [3, 4], [3, 5], [3, 6], [3, 7]]

        #警備兵が通常取りうる向きのリスト
        NORMAL_DIR_1 = [EAST, WEST]
        NORMAL_DIR_2 = [NORTH, SOUTH]
        #警備兵の初期方向
        ENEMY_1_DIRECTION = WEST
        ENEMY_2_DIRECITON = SOUTH


        #マップ情報
        MAP_LIST = [[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 1, 0, 0, 1, 0, 0, 1],
                    [1, 0, 1, 1, 0, 1, 0, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 1, 1, 0, 1, 0, 1, 0, 1],
                    [1, 0, 0, 0, 0, 0, 1, 1, 1],
                    [1, 0, 1, 0, 1, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 1, 0, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]

        #マップの見えてるか見えてないかの情報の初期状態
        MAP_OPEN = [[[1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1]]]
        DIFFICULTY = "HARD"

#スパイのクラス
class Spy:
    def __init__(self, start_x, start_y):
        #初期位置の情報
        self.start_x = start_x
        self.start_y = start_y
        #現在地
        self.x = start_x
        self.y = start_y
        #移動力
        self.mov_pow = WALK
        #武器の有無
        self.have_weap = NOT_HAVE
        #鍵の有無
        self.have_key = NOT_HAVE
        #機密文書の有無
        self.have_sec = NOT_HAVE
        # 生死情報
        self.dead_or_alive = ALIVE

    #移動方向のメソッド
    def move_point(self,in_word):
        if in_word == "w" or in_word == "W":#↑
            self.y -= self.mov_pow
        elif in_word == "a" or in_word == "A":#←
            self.x -= self.mov_pow
        elif in_word == "s" or in_word =="S":#↓
            self.y += self.mov_pow
        elif in_word == "d" or in_word == "D":#→
            self.x += self.mov_pow
        elif in_word == "":#入力無し
            pass

#警備員のクラス
class Enemy:
    def __init__(self,id, start_x, start_y, sight, direction, normal_route = None, normal_dir = None):
        self.id = id
        #初期位置
        self.start_x = start_x
        self.start_y = start_y
        #現在位置
        self.x = start_x
        self.y = start_y
        #通常の警備ルート
        self.normal_route = normal_route
        #追跡時の移動履歴
        self.tracking_route = []
        #状態
        self.status = WAKE_UP
        #向き
        self.direction = direction
        #視野(int)
        self.sight = sight
        #スパイが視界内にいるか
        self.spy_in_sight = False
        # スパイを最後に見た位置を記録
        self.spy_last_position = [[0,0,0],[0,0,0]]
        # 向きを変えるときに使うやつ
        self.turn_count = 0
        #通常取りうる向き
        self.normal_dir = normal_dir
        #移動力
        self.mov_pow = WALK
        #
        self.last_pos_dir = None
        #
        self.can_move = False
        
    #警備員の移動方向のメソッド
    def move_point(self):
        #print("ムーブポイントが呼び出されたぞおおおおお！！！！！！", self.id)
        #一回行動分
        if self.direction == NORTH:#↑
            next_room = MAP_LIST[self.y-1][self.x]
            next_room_pos = [self.y-1, self.x]
        elif self.direction == EAST:#→
            next_room = MAP_LIST[self.y][self.x+1]
            next_room_pos = [self.y,self.x+1]
        elif self.direction == SOUTH:#↓
            next_room = MAP_LIST[self.y+1][self.x]
            next_room_pos = [self.y+1,self.x]
        elif self.direction == WEST:#←            
            next_room = MAP_LIST[self.y][self.x-1]
            next_room_pos = [self.y, self.x-1]
        
        #print(f"NEXTROOM:{next_room}")
        if next_room == ROOM:
            if self.status == WAKE_UP and self.turn_count == 1:
                self.change_direction(MAP_LIST)
                self.turn_count += 1
            else:
                self.turn_count = 0
                self.y, self.x = next_room_pos
        elif next_room == WALL:
            self.turn_count +=1
            self.change_direction(MAP_LIST)

        
    #警備員の向きを変えるメソッド
    def change_direction(self, map_list):
        #向きに対する左右の状態の獲得
        direction = self.direction
        enemy_x = self.x
        enemy_y = self.y
        if direction == NORTH:
            enemy_right = map_list[enemy_y][enemy_x+1]
            enemy_left = map_list[enemy_y][enemy_x-1]
        elif direction == EAST:
            enemy_right = map_list[enemy_y+1][enemy_x]
            enemy_left = map_list[enemy_y-1][enemy_x]
        elif direction == SOUTH:
            enemy_right = map_list[enemy_y][enemy_x-1]
            enemy_left = map_list[enemy_y][enemy_x+1]
        elif direction == WEST:
            enemy_right = map_list[enemy_y-1][enemy_x]
            enemy_left = map_list[enemy_y+1][enemy_x]

        #左右の状態を確認する。
        #右が部屋の場合、右を向く
        if (enemy_left==WALL and enemy_right == ROOM):
            direction += 1
            self.direction = direction % 4
        #左が部屋の場合、左を向く
        elif(enemy_left== ROOM and enemy_right == WALL):
            direction -= 1
            self.direction = direction % 4
        #上記以外は時計周り
        else:
            direction += 1
            self.direction = direction % 4
        
    
    #警備員の状態を変えるメソッド
    def change_status(self, spy):
        self.sight_to_spy(spy)
        #スパイを未発見の場合
        if self.status == WAKE_UP:
            #スパイを発見した場合
            if self.spy_in_sight == True:
                self.status = TRACKING
                self.mov_pow = RUN
            #それ以外
            else:
                self.mov_pow = WALK
        
        #スパイを発見している場合
        elif self.status == TRACKING:
            if  self.spy_in_sight == False:
                self.mov_pow = WALK
            else:
                self.mov_pow = RUN


        # elif self.status == GOING_BACK:
        #     for i in self.normal_route:
        #         if [self.x,self.y] == i:
        #             self.status = WAKE_UP
    
    def sight_to_spy(self, spy):
        mov_list = [[0, -1], [1, 0], [0, 1], [-1, 0]]  #上右下左の順
        for i in range(4):
            if self.direction != i:
                continue
            self.sight = 0
            for j in range(SIGHT):
                if (8 > (self.x + mov_list[i][0] * j) > 0) and \
                    (8 > (self.y + mov_list[i][1] * j) > 0):
                    if MAP_LIST[self.y+mov_list[i][1]*j][self.x+mov_list[i][0]*j] == WALL: 
                        self.spy_in_sight = False
                        break
                    elif (spy.x, spy.y) == (self.x+mov_list[i][0]*j, self.y+mov_list[i][1]*j):
                        # self.sight += 1  あったほうがいいのでは?(菅)
                        self.spy_in_sight = True
                        break
                else:
                    self.spy_in_sight = False
                    break
                self.sight += 1

###関数定義

#現在のユーザー用マップを表示する関数
def print_user_map(spy, enemy1, enemy2, user_map):
    global global_userMap
    enemy_direction_moji = ["↑", "→", "↓", "←"]  #上右下左なので注意
    global_userMap = "" #外部からユーザーマップを呼び出せるようにするためのグローバル変数
    print_moji = None
    print("\n-------------------------------------------------------------------------")
    update_user_map(spy, user_map)       #ユーザー用マップを更新する関数の呼び出し
    for i in range(9):
        for j in range(9):
            if [j, i] == [spy.x, spy.y]:#主人公
                print_moji = '\033[35m'+"●"+'\033[0m'
            elif [j, i] == [enemy1.x, enemy1.y]:
                if [j, i] == [enemy2.x, enemy2.y]: #敵1と敵2が重なっている場合
                    if enemy1.status == TRACKING or enemy2.status == TRACKING:
                        print_moji = '\033[31m'+"*"+'\033[0m'
                    else:
                        print_moji = '\033[32m'+"*"+'\033[0m'
                else:
                    if enemy1.status == TRACKING: 
                        print_moji = '\033[31m'+enemy_direction_moji[enemy1.direction]+'\033[0m'  
                    elif enemy1.status == SLEEP:
                        print_moji = '\033[34m'+enemy_direction_moji[enemy1.direction]+'\033[0m'
                    else:
                        print_moji = '\033[32m'+enemy_direction_moji[enemy1.direction]+'\033[0m'
            elif [j, i] == [enemy2.x, enemy2.y]:
                if enemy2.status == TRACKING:
                    print_moji = '\033[31m'+enemy_direction_moji[enemy2.direction]+'\033[0m'
                elif enemy2.status == SLEEP:
                    print_moji = '\033[34m'+enemy_direction_moji[enemy2.direction]+'\033[0m'
                else:
                    print_moji = '\033[32m'+enemy_direction_moji[enemy2.direction]+'\033[0m'
            elif user_map[i][j] == OPEN: 
                if ([i, j] == WEAPON_POSITION) and \
                    (ITEM_FOUND_LIST[0] == NOT_FOUNDED):  
                        print_moji = '\033[33m'+'W'+'\033[0m'        #武器
                elif ([i, j] == KEY_POSITION) and \
                    (ITEM_FOUND_LIST[1] == NOT_FOUNDED):
                    print_moji = '\033[33m'+'K'+'\033[0m'          #鍵
                elif ([i, j] == SAFE_POSITION) and \
                    (ITEM_FOUND_LIST[2] == NOT_FOUNDED):
                    print_moji = '\033[33m'+'B'+'\033[0m'   #機密文書
                elif [i, j]  == START_POSITION:
                    print_moji = "S"           #スタート地点
                elif MAP_LIST[i][j] == ROOM:
                    print_moji = " "           #通路
                elif MAP_LIST[i][j] == WALL:
                    print_moji = "■"           #壁
                else:
                    print("エラー:ユーザー用マップを表示する関数でエラー")
            elif user_map[i][j] == CLOSED:
                print_moji = "@"               #まだ開示していないところ
            else:
                print("エラー:ユーザー用マップを表示する関数でエラー")
            global_userMap += print_moji
            global_userMap += " "
        if i == 0:
            global_userMap += "　　　\"W\":武器,　\"k\":鍵,　\"B\":金庫　\"*\":敵同士の重複時"
        if i == 1:
            global_userMap += "　　　空白:通路,　\"■\"壁,　\"●\":主人公,　矢印:敵,　\"@\":未開示 "
        global_userMap += "\n"
    print(global_userMap)

#ターン数を加算する関数
def add_turns(current_turn):
    current_turn += 1
    return current_turn

#その他のゲーム情報を表示する関数
def print_game_information(current_turn, spy, enemy1, enemy2): #引数は、現在のターン数、スパイ・敵のインスタンス
    global other_gameInfo, purpose
    other_gameInfo = ""
    enemy_direction_moji = ["↑", "→", "↓", "←"]
    print("難易度:",DIFFICULTY)
    other_gameInfo += "難易度:"+DIFFICULTY
    print("ターン数:", current_turn+1,"/", MAX_TURNS, end="")
    other_gameInfo += "ターン数:"+str(current_turn+1)+"/"+str(MAX_TURNS)
    print("       所持アイテム:", end="")
    other_gameInfo += "       所持アイテム:"
    if spy.have_weap == HAVE:
        print("武器　", end="")
        other_gameInfo += "武器　"
    if spy.have_key == HAVE:
        print("鍵　", end="")
        other_gameInfo += "鍵　"
    if spy.have_sec == HAVE:
        print("機密文書　", end="")
        other_gameInfo += "機密文書　"
    print()
    other_gameInfo += "\n"
    if (enemy1.status == WAKE_UP) or (enemy1.status == GOING_BACK):
        print("敵1の状態：通常  ", end="")
        other_gameInfo += "敵1の状態：通常  "
    elif enemy1.status == SLEEP:
        print("敵1の状態：", '\033[34m'+'気絶  '+'\033[0m', end="")
        other_gameInfo += "敵1の状態："+'\033[34m'+'気絶  '+'\033[0m'
    else:
        print("敵1の状態：",'\033[31m'+'追跡  '+'\033[0m', end="")
        other_gameInfo += "敵1の状態："+'\033[31m'+'追跡  '+'\033[0m'
    print(f"敵1の向き:{enemy_direction_moji[enemy1.direction]}   敵1の位置(x, y):{enemy1.x}, {enemy1.y}  ")
    if (enemy2.status == WAKE_UP) or (enemy2.status == GOING_BACK):
        print("敵2の状態：通常  ", end="")
        other_gameInfo += "敵2の状態：通常  "
    elif enemy2.status == SLEEP:
        print("敵2の状態：", '\033[34m'+'気絶  '+'\033[0m', end="")
        other_gameInfo += "敵2の状態："+'\033[34m'+'気絶  '+'\033[0m'
    else:
        print('敵2の状態：', '\033[31m'+'追跡  '+'\033[0m', end="")
        other_gameInfo += '敵2の状態：'+'\033[31m'+'追跡  '+'\033[0m'
    print(f"敵2の向き:{enemy_direction_moji[enemy2.direction]}   敵2の位置(x, y):{enemy2.x}, {enemy2.y}  ")
    other_gameInfo += f"敵2の向き:{enemy_direction_moji[enemy2.direction]}   敵2の位置(x, y):{enemy2.x}, {enemy2.y}  "
    print()
    other_gameInfo += "\n"
    
    #次すること表示
    if spy.have_key == NOT_HAVE:
        print("< 鍵を探そう！ >")
        other_gameInfo += "< 鍵を探そう！ >"
        purpose = PUR_KEY
    elif spy.have_key == HAVE and spy.have_sec == NOT_HAVE:
        print("< 金庫を探そう！ >")
        purpose = PUR_BOX
        other_gameInfo += "< 金庫を探そう！ >"
    elif spy.have_sec == HAVE:
        print("< スタート地点に戻ろう！ >")
        purpose = PUR_BACK
        other_gameInfo += "< スタート地点に戻ろう！ >"
    print("PURPOSE: ", purpose)


#スパイの行動選択をする関数       これだけ呼び出せば下の関数2つは呼び出さなくていい
def player_move(spy, enemy_1, enemy_2): #引数はマップとスパイのインスタンス
    while True:
        input_word = key_input(spy, enemy_1, enemy_2)
        successful_or_not = update_spy_position(spy, input_word)
        #移動先が壁ではなかった場合
        if successful_or_not == True:
            break
        #移動先が壁だった場合はループから抜けない
        print("移動先が壁です。キー入力をやり直してください。")

#キー入力をする関数
def key_input(spy, enemy_1, enemy_2):
    global MAX_TURNS
    char = ""
    char_allowed = ["w", "W", "a", "A", "s", "S", "d", "D", ""]
    while True:
        char = input("input w(↑), a(←), s(↓), d(→), \"rule\", or no character(skip this turn). And Push ENTER. >>")
        # "移動方向を入力してください。w(↑)、a(←)、s(↓)、d(→)、Enter(移動なし)、rule(ルール確認)>>"
        if char in char_allowed:
            break
        elif char == "rule" or char == "RULE":
            print(RULE_TEXT)
            print("-"*50)
            print(global_userMap)
            print(other_gameInfo)
        
        elif "!turn" in char:
            MAX_TURNS += int(char[5:])
            print(f"HELL YEAH!!! CHEATING IS HERE! NOW MAX TURNS IS {MAX_TURNS} !!!")
        
        elif char == "!weapon_get":
            spy.have_weap = HAVE
            print("YOU GET THE EXCALIBUR!!!!")
        elif char == "!kill":
            print("AIN'T THIS REALLY SHITTY? IS IT REALLY ANY FUN AT ALL? YEEEEES!")
            #spy.have_sec = HAVE
            enemy_1.status, enemy_1.can_move = SLEEP, False
            enemy_2.status, enemy_2.can_move = SLEEP, False
        else:
            print("You have an air head! Input an available key.")
    return char

#スパイの座標（現在地）を更新する関数
def update_spy_position(spy, in_word): #引数はマップとスパイのインスタンス、キー入力文字
    move_list_L = [[0, -1], [-1, 0], [0, 1], [1, 0]]
    move_x_L = 0
    move_y_L = 0
    if in_word == "w" or in_word == "W":
        move_x_L, move_y_L = move_list_L[0]
    elif in_word == "a" or in_word == "A":
        move_x_L, move_y_L = move_list_L[1]
    elif in_word == "s" or in_word =="S":
        move_x_L, move_y_L = move_list_L[2]
    elif in_word == "d" or in_word == "D":
        move_x_L, move_y_L = move_list_L[3]

    #移動先が壁だった場合
    if MAP_LIST[spy.y + move_y_L][spy.x + move_x_L] == WALL:
        return False
    else:
        #移動先が壁ではなかった場合
        spy.move_point(in_word)
        return True

#スパイと警備兵の衝突判定とそのときの処理をする関数
def spy_security_facing(spy, enemy): #引数はスパイと敵のインスタンス
    if (spy.x == enemy.x) and (spy.y == enemy.y):
        if spy.have_weap == HAVE:
            enemy.status = SLEEP
            print('\033[31m'+f'敵{enemy.id}を気絶させました!'+'\033[0m')
            spy.have_weap = USED
        else:
            if not enemy.status == SLEEP:
                spy.dead_or_alive = DEAD

#アイテム発見時の処理をする関数
def find_item(spy, enemy_1, enemy_2, found_list):
    if [spy.y, spy.x] == WEAPON_POSITION:
        if found_list[0] == NOT_FOUNDED:
            found_list[0] = FOUNDED
            spy.have_weap = HAVE
            print('\033[31m'+'武器をゲットしました!'+'\033[0m')
    elif [spy.y, spy.x] == KEY_POSITION:
        if spy.have_key != USED:
            found_list[1] = FOUNDED
            spy.have_key = HAVE
            print('\033[31m'+'鍵をゲットしました!'+'\033[0m')
    elif [spy.y, spy.x]== SAFE_POSITION:
        if spy.have_key == HAVE:
            spy.have_key = USED
            found_list[2] = FOUNDED
            spy.have_sec = HAVE
            print('\033[31m'+'機密文書をゲットしました!'+'\033[0m')
            if enemy_1.tracking_route != []:
                enemy_1.status = GOING_BACK
                enemy_1.mov_pow = WALK
            else:
                enemy_1.status = WAKE_UP
                enemy_1.mov_pow = WALK
            if enemy_2.tracking_route != []:
                enemy_2.status = GOING_BACK
                enemy_1.mov_pow = WALK
            else:
                enemy_2.status = WAKE_UP
                enemy_2.mov_pow = WALK
        else:
            if spy.have_key == USED and spy.have_sec == HAVE:
                print('\033[31m'+'文書をすでに所持しています。'+'\033[0m')
            else:
                print('\033[31m'+'鍵を持っていないので金庫を開けられません。'+'\033[0m')

#警備兵の行動決定をする関数  
def decide_security_move(spy, enemy):
    #通常時 or 追跡時 
    enemy.change_status(spy)
    rsp = record_spys_position(spy, enemy)
    
    if enemy.status == WAKE_UP and enemy.can_move == True:
        for _ in range(enemy.mov_pow):
            enemy.move_point()
            enemy.change_status(spy)
        
            enemy.can_move = False

    elif enemy.status == TRACKING and enemy.can_move == True:
        if enemy.tracking_route == []:
            enemy.tracking_route.append([enemy.x, enemy.y, enemy.direction])
        if rsp == None:
            for _ in range(enemy.mov_pow):
                enemy.move_point()
                enemy.tracking_route.append([enemy.x, enemy.y, enemy.direction])
                enemy.change_status(spy)
                if [spy.x, spy.y] == [enemy.x, enemy.y]:
                    spy_security_facing(spy, enemy)
                    break

                if [enemy.x, enemy.y] == [enemy.spy_last_position[0][0], enemy.spy_last_position[0][1]]:
                    enemy.sight_to_spy(spy)
                    if enemy.spy_in_sight:
                        continue
                    else:
                        break

                enemy.can_move = False
        else:
            if [enemy.x, enemy.y] == [enemy.spy_last_position[0][0], enemy.spy_last_position[0][1]]:#スパイを見たところまで来たら
                enemy.direction = rsp 
                enemy.sight_to_spy(spy)
                if enemy.spy_in_sight:
                    enemy.tracking_route.append([enemy.x, enemy.y, enemy.direction])
                else:
                    enemy.status = GOING_BACK
                    enemy.mov_pow = WALK
                enemy.spy_last_position = [[spy.x,spy.y,False],[spy.x,spy.y,False]]
                enemy.can_move = False

            else: #まだスパイを見た位置まで行っていないなら
                # if [enemy.spy_last_position[0], enemy.spy_last_position[1]] == 
                for _ in range(enemy.mov_pow):
                    enemy.move_point()
                    enemy.tracking_route.append([enemy.x, enemy.y, enemy.direction])
                    enemy.change_status(spy)
                    if [spy.x, spy.y] == [enemy.x, enemy.y]:
                        spy_security_facing(spy, enemy)
                        break

                    if [enemy.x, enemy.y] == [enemy.spy_last_position[0][0], enemy.spy_last_position[0][1]]:
                        enemy.sight_to_spy(spy)
                        if enemy.spy_in_sight:
                            continue
                        else:
                            break
                enemy.can_move = False


    #帰還時
    elif enemy.status == GOING_BACK and enemy.can_move == True:
        '''元の警備ルートにいるかも調べる
        ステータスを通常に戻す条件を融通しないとエラーが起こるかも。
        '''
        for x,y in enemy.normal_route:
            if enemy.can_move == True:
                if enemy.x == x and enemy.y == y:
                    if enemy.id == 1:
                        if (enemy.direction == NORMAL_DIR_1[0] or enemy.direction == NORMAL_DIR_1[1]):
                            enemy.tracking_route = []
                            enemy.status = WAKE_UP
                            #
                            enemy.move_point()
                            enemy.change_status(spy)
                            enemy.can_move = False
                        else:
                            enemy.tracking_route = []
                            # enemy.status = WAKE_UP
                            enemy.change_direction(MAP_LIST)
                            enemy.can_move = False
                    elif enemy.id== 2:
                        if (enemy.direction == NORMAL_DIR_2[0] or enemy.direction == NORMAL_DIR_2[1]):
                            enemy.tracking_route = []
                            enemy.status = WAKE_UP
                            # 
                            enemy.move_point()
                            enemy.change_status(spy)
                            enemy.can_move = False
                            # 
                        else:
                            enemy.tracking_route = []
                            # enemy.status = WAKE_UP
                            enemy.change_direction(MAP_LIST)
                            enemy.can_move = False

        if (enemy.tracking_route != []) and (enemy.status != WAKE_UP) and enemy.can_move==True:    
            back_x, back_y, direction = enemy.tracking_route.pop(-1)
            enemy.x = back_x
            enemy.y = back_y
            enemy.direction = (direction+2) % 4
            enemy.can_move = False
    
    elif enemy.can_move == False:
        print("can_moveがFalseです。")
    elif enemy.status == SLEEP:
        print("気絶してます")

    #それ以外
    else:
        print("警備兵の行動が不可解です。")
        print("このメッセージが見られるのはおかしいよ。")
    
    enemy.sight_to_spy(spy)
    if enemy.spy_in_sight:
        enemy.spy_last_position[1][2] = True
    else:
        enemy.spy_last_position[1][2] = False


#スパイの位置情報を記録させる関数
#スパイを最後に見た位置を記録する(毎ターン呼び出してほしい(警備兵の行動決定関数の中で?))
def record_spys_position(spy, enemy):
    if (enemy.spy_last_position[0][2] == True) and (enemy.spy_last_position[1][2] == False):
        x = enemy.spy_last_position[1][0] - enemy.spy_last_position[0][0]
        y = enemy.spy_last_position[1][1] - enemy.spy_last_position[0][1]
        dir_list = [[-1,0], [0,1], [1,0], [0,-1]]
        for i in range(len(dir_list)):
            if [y, x] == dir_list[i]:
                return i # NORTH, EAST, SOUTH, WEST
    else:
        if enemy.spy_in_sight == True:
            enemy.spy_last_position[0] = enemy.spy_last_position[1]
            enemy.spy_last_position[1] = [spy.x, spy.y, True] 
        else:
            enemy.spy_last_position[0] = enemy.spy_last_position[1]
            enemy.spy_last_position[1] = [spy.x, spy.y, False]
        return None

#ユーザー用のマップを更新する関数
def update_user_map(spy, user_map_list): #引数はスパイのインスタンス、ユーザー用マップのリストの変数
    mov_list = [[0,-1],[-1,0],[0,1],[1,0]] #上左下右
    #スパイの座標の上下左右を一直線に調べて壁まで開示する
    for i in range(4):
        for j in range(9):
            if (8 > (spy.x + mov_list[i][0] * j) > 0) and \
                (8 > (spy.y + mov_list[i][1] * j) > 0):
                user_map_list[spy.y+mov_list[i][1]*j][spy.x+mov_list[i][0]*j] = OPEN
                if MAP_LIST[spy.y+mov_list[i][1]*j][spy.x+mov_list[i][0]*j] == WALL:
                    break
            else:
                break

#オブジェクトの生死を判定する関数
def is_alive(somebody):
    if somebody.dead_or_alive == ALIVE:
        return False
    else:
        return True
            
#ゲームを終了させる関数
def end_game(spy, enemy_1, enemy_2, user_map, flag):
    update_user_map(spy, user_map)    #ユーザー用マップを更新する
    print_user_map(spy, enemy_1, enemy_2, user_map)  #ユーザー用マップを画面に出力
    print("\n", '\033[31m'+"--------ゲーム終了--------"+'\033[0m')
    if flag  == CLEARED: #ゲームに勝利した場合
        print("ゲームに勝利しました!おめでとうございます!")
    elif flag == FAILED: #ゲームに敗北した場合
        print("ゲームに敗北しました...。　敗北要因:", end="")
        if spy.dead_or_alive == DEAD: #スパイが死んだことが敗北要因の場合
            print("主人公が死亡した。")
        else:  #ターン制限を超えたことが敗北要因の場合
            print("ターン制限を越えて移動した。")
    else:
        print("end_game関数でエラー")
    print("========================================================================\n\n")
    #quit()                                #ゲームループを抜ける

#スパイがゲームクリア条件を満たしているかを確認する関数
def can_spy_clear(spy):
    if [spy.x, spy.y] == START_POSITION and spy.have_sec == HAVE:
        return True
    else:
        return False

#ターン数の上限に達したかを判定する
def reach_turn_limit(turn):
    if turn >= MAX_TURNS:
        return True
    else:
        return False

'''
AIの作成START❗❗❗❗❗❗❗❗❗❗❗❗❗❗
'''
purpose = PUR_NAN
houmon_list = [[0 for _ in range(9)] for _ in range(9)]
OK = 0
NG = 1

'''
def ai_stop(spy_next_x, spy_next_y, enemy_sight_map):
    if enemy_sight_map[spy_next_y][spy_next_x] == OK:
        return True
    else:
        return False
'''
def ai_move(spy, enemy_1, enemy_2, sight_map):
    global houmon_list
    ai_map = copy.deepcopy(MAP_LIST)
    for y in range(len(MAP_LIST)):
        for x in range(len(MAP_LIST[0])):
            if sight_map[y][x] == CLOSED:
                ai_map[y][x] = WALL
    
    houmon_list[spy.y][spy.x] += 1
    '''
    enemy_sight_list = [[OK for _ in range(9)] for _ in range(9)]
    for enemy in [enemy_1, enemy_2]:
        enemy_sight_list[enemy.y][enemy.x] = NG
        if enemy.direction == NORTH:
            enemy_sight_list[:enemy.y][enemy.x] = NG
    '''

    '''
    目的ごとに処理を変更している。
    アイテムを見つけた際や、スタート位置に戻ればクリアできる場面では、一直線にその場所を目指す。
    それ以外の、次の目的地を見つけられていない場面では、訪れていない場所を優先して訪れるようにした。
    '''

    if purpose == PUR_KEY and spy.have_key == NOT_HAVE and\
        sight_map[KEY_POSITION[0]][KEY_POSITION[1]] == OPEN:
        # [y, x]
        next_pos = Search(ai_map, [spy.y, spy.x], [KEY_POSITION[0], KEY_POSITION[1]])
        print("NEXTPOSITION!", next_pos)
        spy.x = next_pos[1]
        spy.y = next_pos[0]

    elif purpose == PUR_BOX and spy.have_sec == NOT_HAVE and\
        sight_map[SAFE_POSITION[0]][SAFE_POSITION[1]] == OPEN:
        # [y, x]
        next_pos = Search(ai_map, [spy.y, spy.x], [SAFE_POSITION[0], SAFE_POSITION[1]])
        print("NEXTPOSITION!", next_pos)
        spy.x = next_pos[1]
        spy.y = next_pos[0]
    elif purpose == PUR_BACK and spy.have_sec == HAVE:
        # [y, x]
        next_pos = Search(ai_map, [spy.y, spy.x], [START_POSITION[0], START_POSITION[1]])
        print("NEXTPOSITION!", next_pos)
        spy.x = next_pos[1]
        spy.y = next_pos[0]
    else:
        '''
        もともとランダム移動が実装されていた場所。
        ランダムだと一度通った道に行ったり、きたみちを引き返したりと、効率が悪すぎるため、変更。
        houmon_listという、自分がそのマスに何度訪れたかを記録するリストを作成。
        次に移動するマスは、訪れた回数が最も小さいものの中から選ぶようにした。
        こうすることで、クリア率が2から3倍に改善された。
        '''
        next_pos_list = [[spy.x, spy.y - 1], [spy.x, spy.y + 1],\
            [spy.x - 1, spy.y], [spy.x + 1, spy.y]]
        new_pos_list = []
        houmon_count = 99999
        for pos in next_pos_list:
            if houmon_list[pos[1]][pos[0]] < houmon_count:
                houmon_count = houmon_list[pos[1]][pos[0]]
                new_pos_list = [pos]
            elif houmon_list[pos[1]][pos[0]] == houmon_count:
                new_pos_list.append(pos)
            else:
                pass
        
        while True:
            next_pos = random.choice(new_pos_list)
            if ai_map[next_pos[1]][next_pos[0]] != WALL:
                spy.x, spy.y = next_pos[0], next_pos[1]
                break
            else:
                continue
        '''
        import numpy
        print(numpy.asarray(houmon_list))
        '''

#幅優先探索で目的地までの経路を計算
class Node:
    def __init__(self, par, x, y, d):
        self.parent = par
        self.position = [x, y]
        self.depth = d

def Search(maze_list, start_xy_list, goal_xy_list):
    maze = maze_list
    maze_start = start_xy_list
    maze_goal = goal_xy_list

    #Create start and goal.
    start = Node(None, maze_start[0], maze_start[1], 0)
    goal = Node(None, maze_goal[0], maze_goal[1], 0)
    #Create list queue and list visited.
    queue = []
    visited = []
    #Add "Start node" to a queue list.
    queue.append(start)
    now_count = 1

    while queue:#Loop
        now_count += 1
        print("NOW LOADING...", now_count)
        #4-a
        node_now = queue.pop(0)
        visited.append(node_now)
        x = node_now.position[0]
        y = node_now.position[1]
        #4-b
        if node_now.position == goal.position:
            #print("Cleared!")
            goal.parent = node_now.parent
            goal.depth = node_now.depth
            break

        #4-c
        next_node_list = [] #次に行ける場所のリスト
        for i in [[x+1, y], [x-1, y], [x, y+1], [x, y-1]]:
            next_x , next_y = i[0], i[1]
            try:
                if next_x < 0 or next_y < 0:
                    continue
                else:
                    if maze[next_x][next_y] == 0:
                        next_node_list.append(i)
                    else: pass
            except:pass
        #print(node_now.position, next_node_list)
        
        #4-d
        #d-i
        for i in next_node_list:
            ix, iy = i[0], i[1]
            next_node = Node(node_now, ix, iy, node_now.depth)
            #d-ii, iii
            if next_node not in visited:
                next_node.depth = node_now.depth + 1
            else: continue
            #d-iv
            if next_node not in queue:
                queue.append(next_node)
            else: continue
    #Cost経路コストを表示
    cost = goal.depth
    #print("Path Cost: {}".format(cost))
    #Root経路を表示
    iam = goal
    rootList = []

    while True:
        rootList.append(iam.position)
        if iam.parent == None:
            break
        iam = iam.parent
    rootList.reverse()

    return rootList[1]

'''
AIの作成OWARI❗❗❗❗❗❗❗❗❗❗❗❗❗❗
'''

#検証用
CLEAR_ONCE :bool = False
clear_count = 0

###ゲームループ
def game_loop():
    global CLEAR_ONCE, clear_count
    #dungeon = Dungeon(MAP_LIST)#Dungeonクラスから実際にダンジョンを作成
    now_turn = 0#現在のターンを0に初期化。ループのはじめに1加算するため0でよし
    #has_enemy_wakeup = False
    game_flag = NOT_CLEARED#ゲームの現在の状態を示すフラグ。これを利用してループ終了時にクリア判定を行う。
    print(RULE_TEXT)  #ルール文を表示する。
    pick_map() #マップ選択
    spy = Spy(START_POSITION[0], START_POSITION[1])#Spyを作成
    enemy_1 = Enemy(1,ENEMY_1_POSITION[0],ENEMY_1_POSITION[1], 6, ENEMY_1_DIRECTION, NORMAL_ROOT_1, NORMAL_DIR_1)#敵（警備兵）を作成
    enemy_2 = Enemy(2,ENEMY_2_POSITION[0],ENEMY_2_POSITION[1], 4, ENEMY_2_DIRECITON, NORMAL_ROOT_2, NORMAL_DIR_2)
    user_map = copy.deepcopy(MAP_OPEN)[0]  #出力用のマップを作成する。
    for y in range(9):
        for x in range(9):
            if MAP_LIST[y][x] == WALL:
                houmon_list[y][x] = 99999
    
    while True:
        enemy_1.can_move = True
        enemy_2.can_move = True
        print_user_map(spy, enemy_1, enemy_2, user_map)
        print_game_information(now_turn, spy, enemy_1, enemy_2)
        now_turn = add_turns(now_turn)
        
        if reach_turn_limit(now_turn):#現在のターンが80を超えたらブレイクしてフラグを失敗に
            game_flag = FAILED
            break

        #player_move(spy, enemy_1, enemy_2)#スパイの行動選択

        ai_move(spy, enemy_1, enemy_2, user_map) #AIに行動決定させる

        enemy_1.change_status(spy)
        enemy_2.change_status(spy)
        find_item(spy, enemy_1, enemy_2, ITEM_FOUND_LIST) 
        spy_security_facing(spy, enemy_1)#警備兵がいるかどうか？
        spy_security_facing(spy, enemy_2)
        if is_alive(spy):#スパイが死んでしまったらブレイクしてフラグを失敗に
            game_flag = FAILED
            break
        if can_spy_clear(spy):#スパイが初期位置にいるか？
            game_flag = CLEARED
            CLEAR_ONCE = True
            clear_count += 1
            break
        #find_item(spy, enemy_1, enemy_2, ITEM_FOUND_LIST)#アイテムを発見したかどうかの処理
        #警備兵の行動決定
        decide_security_move(spy, enemy_1)
        decide_security_move(spy, enemy_2)
        spy_security_facing(spy, enemy_1)#警備兵がいるかどうか？
        spy_security_facing(spy, enemy_2)
        if is_alive(spy):#スパイが死んでしまったらブレイクしてフラグを失敗に
            game_flag = FAILED
            break
        #print("USERMAP", user_map)
        if ITEM_FOUND_LIST[1] == FOUNDED:
            pass
    
    end_game(spy, enemy_1, enemy_2, user_map, game_flag)

game_count = 1
game_num = 100
def testing_ai():
    global game_count
    print(f"❗現在のゲーム数は❗【{game_count}回】です。")
    for _ in range(game_num):
        '''if CLEAR_ONCE == True:
            print("#####CLEAR!!!!!#####")
            break'''
        game_loop()
        game_count += 1
    print(f"テスト終了❗AIは{game_num}回プレイして、{clear_count}回クリアしました。")
    print(f"成功率は{clear_count / game_num * 100}%です。")
    print(f"失敗率は{100.0 - (clear_count / game_num * 100)}%です。")

testing_ai()