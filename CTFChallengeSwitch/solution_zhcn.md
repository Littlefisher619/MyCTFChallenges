# 简介
[My Switch Game](https://github.com/Littlefisher619/MyCTFChallenges/tree/master/CTFChallengeSwitch/Challenge2) 和 [Switch Pro Controller](https://github.com/Littlefisher619/MyCTFChallenges/tree/master/CTFChallengeSwitch/Challenge2) 是由ROIS举办的 [RCTF2020](https://ctftime.org/event/1045) 赛事中的两个题目。

# 出题资料

通信协议

* https://github.com/spacemeowx2/RemoteSwitchController/blob/dev/splatoon-bot/src/controller.ts

* https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering/blob/master/bluetooth_hid_notes.md

模拟器

* https://emulation.gametechwiki.com/index.php/Nintendo_Switch_emulators
* https://github.com/Ryujinx/Ryujinx

Switchbrew Dev

* https://www.switchbru.com/appstore/#/
* https://github.com/switchbrew/libnx
* https://switchbrew.org/wiki/Setting_up_Development_Environment
* https://github.com/switchbrew/switch-examples/tree/master/templates/application

Debugger:

* https://github.com/reswitched/Mephisto

# Switch Pro Controller

Switch手柄连接到装有Steam的Windows，打开Steam好友聊天窗口，通过按左摇杆三下启动屏幕键盘，启动屏幕录制和Wireshark抓包，并输入flag。选手根据录制的视频和USB数据包还原出flag。flag遵循RCTF{...}的格式。

附件: `capture.pcappng` `screenrecord.mp4`

描述: 没有

Flag: RCTF{5witch_1s_4m4z1ng_m8dw65}

Solve.py

```python
import ffmpeg
# install ffmpeg to your system and then pip3 install ffmpeg-python
import numpy
import cv2
import json

KEY_A = 0b00001000
TIMEDELTA = 3
JSON_FILE = 'easy.json'
VIDEO_FILE = 'easy.mp4'
# Timedelta can be calculated by when the first packet that 
# means KEY_A pressed appears and when the first character
# appears on the textbox in the video
# It help us locate the KEY_A-Pressed frames in the video.

f = open(JSON_FILE, 'r', encoding='utf-8')
packets = json.loads(f.read())
f.close()

# filter the packets which means A is pressed and extract time and frameNo
buf = []
for packet in packets[735:]:
	layers = packet['_source']['layers']
	packetid = int(layers['frame']['frame.number'])
	time = float(layers['frame']['frame.time_relative'])
	try:
		capdata = bytearray.fromhex(layers["usb.capdata"].replace(':', ' '))
		if capdata[3] & KEY_A == KEY_A:
			buf.append([packetid, time])
			print(packetid, time, [bin(data)[2:] for data in capdata[3:6]])
	except KeyError:
		pass

print(buf)

# seperate sequences from filtered packets and calculate the average time for each sequence
time_avg = []
_lastid = buf[0][0]-2
_sum = 0
_sumcnt = 0
_cnt = 0

for data in buf:
	_cnt += 1
	if data[0]-_lastid==2 and _cnt!=len(buf):
		_sum+=data[1]
		_sumcnt+=1
	else:
		time_avg.append(_sum/_sumcnt)
		_sum = 0
		_sumcnt = 0
	_lastid = data[0]
print(time_avg)

# extract frames from the video one by one
for t in time_avg:
	out, err = (
		ffmpeg.input(VIDEO_FILE, ss=t)
			  .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
			  .run(capture_stdout=True)
	)

	image_array = numpy.asarray(bytearray(out), dtype="uint8")
	image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
	cv2.imshow('time={}'.format(t), image)

	cv2.moveWindow('time={}'.format(t), 0, 0)
	if cv2.waitKey(0) == 27:
		break
	else:
		cv2.destroyAllWindows()
```



# My Switch Game

开发一个Switch平台上的控制台贪吃蛇游戏，基于Switch Homebrew进行开发，通过手柄控制游戏操作并进行抓包。解题需要逆向游戏软件的源代码并分析通信数据包，知道用户操作和程序代码的执行过程，以还原出flag。

贪吃蛇游戏的源码是基于这个项目编写的：https://github.com/CompSciOrBust/Cpp-Snake-NX/

附件：`snake.nro` `log.log`

描述信息：Relay bt traffic and capture by https://github.com/mart1nro/joycontrol

Hint: flag's format is RCTF{xxx} and length of "RCTF{xxx}" is 32.

Flag: RCTF{ddzljsqpaw6h31an5tgeaz75t0}

解题思路：

1. 逆向工程（需要用到IDA插件：[nxo64](https://github.com/reswitched/loaders)/[SwitchIDAProLoader](https://github.com/pgarba/SwitchIDAProLoader)）：

   * 通过逆向游戏软件得知flag的seed生成规则：`seed = nTail*4 + dir - 1`

     找到一个通过`xor 0x44`加密的数组，存储着flag的格式信息

     得出前五个字符和最后一个字符是RCTF{}，其他flag的字符的生成是逐字符的，且基于贪吃蛇的长度以及贪吃蛇得分前最后的方向：`flagchar = flagalphabet[rand() % strlen(flagalphabet)]`

     另外，下一个得分点出现的位置是在flagchar生成前进行生成，

     ```
     fruitX = rand() % width;
     fruitY = rand() % height;
     ```

   * 通过分析数据包得知Output reports存在RUMBLE_DATA，即Switch控制手柄振动的数据，而且经过剔除后刚好是32个。因为除了吃到分数之外，没有理由会振动手柄，因此可以断定贪吃蛇吃到分的时候，手柄会振动。根据它来确定贪吃蛇吃到分的时候的方向。

   * 通过逆向游戏软件得知贪吃蛇的方向由手柄上的方向键控制

   * 通过逆向得出游戏的随机数生成算法，以便于进行随机数攻击（不同编译器的rand()实现是不同的）

     ```c
     unsigned __int64 rand()
     {
       __int64 v0; // x0
       unsigned __int64 v1; // x1
     
       v0 = sub_710007F0A0();
       v1 = 6364136223846793005LL * *(_QWORD *)(v0 + 232) + 1;
       *(_QWORD *)(v0 + 232) = v1;
       return (v1 >> 32) & 0x7FFFFFFF;
     }
     ```

     **也可以使用同样的编译器，写一个专门用于根据我们给定的seed来生成随机数的游戏软件，并在模拟器里运行，下面的解题步骤将采用这种办法。**

2. 搭建解题环境

   * Switch模拟器：[Yuzu](https://yuzu-emu.org/)、[Ryujinx](https://ryujinx.org/)
   * 编译环境：https://switchbrew.org/wiki/Setting_up_Development_Environment

3. 解析log，照着题目描述里的那个github project里的解析log的脚本改一下：https://github.com/mart1nro/joycontrol/blob/master/scripts/parse_capture.py

   根据手柄发送振动的数据包的时间，在此时间之前找到贪吃蛇得分前最后的方向，再计算seed，输出一下所有计算得到的seed

   ```python
   import argparse
   import struct
   
   from joycontrol.report import InputReport, OutputReport, SubCommand
   import math
   DIR = {
       0b00001000: ('LEFT', 1),
       0b00000100: ('RIGHT',2),
       0b00000010: ('UP',   3),
       0b00000001: ('DOWN', 4)
   }
   RUMBLE = [4, 180, 1, 78, 4, 180, 1, 78]
   
   """ joycontrol capture parsing example.
   
   Usage:
       parse_capture.py <capture_file>
       parse_capture.py -h | --help
   """
   
   
   def _eof_read(file, size):
       """
       Raises EOFError if end of file is reached.
       """
       data = file.read(size)
       if not data:
           raise EOFError()
       return data
   
   def get_rumble_timestamps():
       rumble_timestamps = [i[0] for i in output_reports if i[1].get_rumble_data() == RUMBLE]
       return rumble_timestamps
   
   def get_dir_inputs():
       dir_inputs = [(i[0], i[1].data[6]) for i in input_reports if i[1].data[6] & 0b00001111 != 0]
       return dir_inputs
   
   if __name__ == '__main__':
       parser = argparse.ArgumentParser()
       parser.add_argument('capture_file')
       args = parser.parse_args()
   
       # list of time, report tuples
       input_reports = []
       output_reports = []
   
       with open(args.capture_file, 'rb') as capture:
           try:
               start_time = None
               while True:
                   # parse capture time
                   time = struct.unpack('d', _eof_read(capture, 8))[0]
                   
                   if start_time is None:
                       start_time = time
   
                   # parse data size
                   size = struct.unpack('i', _eof_read(capture, 4))[0]
                   # parse data
                   data = list(_eof_read(capture, size))
   
                   if data[0] == 0xA1:
                       report = InputReport(data)
                       # normalise time
                       input_reports.append((time, report))
                   elif data[0] == 0xA2:
                       report = OutputReport(data)
                       # normalise time
                       output_reports.append((time, report))
                   else:
                       raise ValueError(f'Unexpected data.')
           except EOFError:
               pass
   
       dir_input_list = get_dir_inputs()
       rumble_timestamps = get_rumble_timestamps()
       print(dir_input_list)
       print(rumble_timestamps)
   
       tailcnt = cursor = 0
       seeds = []
       # The last direction of before snake scoring a point can be found by the timestamp when the rumble packet was sent.
       for timestamp in rumble_timestamps:
           while cursor < len(dir_input_list) and dir_input_list[cursor][0] <= timestamp:
               cursor += 1
           lastdir_before_rumble = dir_input_list[cursor-1][1]
   
           # In order to get the formula to calculate seed, you should do reserve engineering on game nro file.
           seed = tailcnt*4 + DIR[lastdir_before_rumble][1] - 1
           seeds.append(str(seed))
   
           tailcnt += 1
   
       print(len(seeds), seeds)
       open('seeds.txt', 'w').write(' '.join(seeds))
   
       # now plz place seeds.txt to switch emulator's /sdcard folder
       # and then run the rand.nro file you complied just now to generate random numbers
       # You should press a key on your keyboard correspond to 'A' in Pro Controller.
       # At the end, flag will put into flag.txt
   
   
       # For Ryujinx, /sdcard can be accessed by clicking Open Ryujinx Folder under the File menu in the GUI.
       #              And key 'Z' on keyboard corresponds to 'A' in Pro Controller.
   
   ```

4. 根据这个最简单的Template：https://github.com/switchbrew/switch-examples/tree/master/templates/application

   编写用于生成随机数的C代码，编译并于模拟器上运行，顺便计算flag

   ```c
   const int width = 77;
   const int height = 41;
   const char* flagalphabet = "0123456789abcdefghijklmnopqrstuvwxyz_";
   const char* flagformat="RCTF{}";
   const int flaglen = 32;
   void solve(){
       FILE *seeds = fopen("seeds.txt", "r"),
            *flag = fopen("flag.txt", "w");
       if(seeds==NULL || flag==NULL){
           puts("failed to open file");
           return;
       }
   
       int seed, x, y, flagchar;
       puts("======Solving...");
       for(int i=0;i<flaglen;i++){
           if(i!=0){
               fscanf(seeds,"%d",&seed);
               srand(seed);
               x = rand() % width, y = rand() % height;
               if(i < strlen(flagformat) - 1)
                   flagchar = flagformat[i];
               else if(i == flaglen - 1)
                   flagchar = flagformat[strlen(flagformat) - 1];
               else flagchar = flagalphabet[rand() % strlen(flagalphabet)];
           }else x=-1, y=-1, flagchar = flagformat[0];
           printf("[Seed=%d] (%d, %d) %c\n", seed, x, y, flagchar);
           fputc(flagchar, flag);
       }
       fclose(seeds);
       fclose(flag);
   
   }
   ```

   



_
