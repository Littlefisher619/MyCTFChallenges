# Introduction
[My Switch Game](https://github.com/Littlefisher619/MyCTFChallenges/tree/master/CTFChallengeSwitch/Challenge2) and [Switch Pro Controller](https://github.com/Littlefisher619/MyCTFChallenges/tree/master/CTFChallengeSwitch/Challenge1) are the challenges for the game [RCTF2020](https://ctftime.org/event/1045) hosted by ROIS.

* My Switch Game: `Reserve`+`Misc`

* Switch Pro Controller: `Misc`

*[Here for Chinese solution](https://github.com/Littlefisher619/MyCTFChallenges/blob/master/CTFChallengeSwitch/solution_zhcn.md)*
# References

Traffic

* https://github.com/spacemeowx2/RemoteSwitchController/blob/dev/splatoon-bot/src/controller.ts

* https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering/blob/master/bluetooth_hid_notes.md

Switch Emulator

* https://emulation.gametechwiki.com/index.php/Nintendo_Switch_emulators
* https://github.com/Ryujinx/Ryujinx

Switchbrew Dev

* https://www.switchbru.com/appstore/#/
* https://github.com/switchbrew/libnx
* https://switchbrew.org/wiki/Setting_up_Development_Environment
* https://github.com/switchbrew/switch-examples/tree/master/templates/application

Debugger:

* https://github.com/reswitched/Mephisto

# Switch Pro Controller(Challenge1)

Switch Pro Controller is connect to Windows with Steam installed through USB. Open the friend chat window, and then press the left stick three times to launch Steam's screen keyboard. Starting screen recording and Wireshark to capture the packets. You should get flag by the video file and the pcapng file.

Attachment: `capture.pcappng` `screenrecord.mp4`

Description: none

Flag: RCTF{5witch_1s_4m4z1ng_m8dw65}

Solve.py：

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



# My Switch Game(Challenge2)

Develop a console-based snake game on switch. Playing game with switch controller which BT traffic is relayed by a script running on ubuntu. In order to solve it, you should do reserve engineering on game's .nro file and analysis the traffic. And the source code of snake game is based on https://github.com/CompSciOrBust/Cpp-Snake-NX/

Attachment: `snake.nro` `log.log`

Hint: flag's format is RCTF{xxx} and length of "RCTF{xxx}" is 32.

Description: Relay bt traffic and capture by https://github.com/mart1nro/joycontrol/blob/master/scripts/relay_joycon.py

Flag: RCTF{ddzljsqpaw6h31an5tgeaz75t0}

Solution:

1. Reserve engineering(IDAPython plugin：[nxo64](https://github.com/reswitched/loaders)/[SwitchIDAProLoader](https://github.com/pgarba/SwitchIDAProLoader))：

   * Flag is generated by random number and the `seed` is determined by `nTail*4 + dir - 1`

     We can found an encrypted array that including flag's format. To decrypt, `xor` with `0x44`.

     `flag[:5]` and `flag[-1]` is `RCTF{}`, other chars on flag is generated char by char with the seed above: `flagchar = flagalphabet[rand() % strlen(flagalphabet)]`

     By the way, the generation of the coordinate of the next score is ahead of the generation of flagchar.

     ```
     fruitX = rand() % width;
     fruitY = rand() % height;
     ```
     
   * In `log.log`, we can found there are some `RUMBLE_DATA` packets in output reports. After filtering, there are 32 rumble packets in total that corresponds to flag's length. So we can assume that when the snake scores a point, vibration packet was sent to Switch Pro Controller.

     We can also validate the assumption by reserve engineering.

   * The snake is controlled by Direction Keys on the Controller.

   * Get the random number generation algorithm whose implement is depends on the complier.

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

     **We also can emulate running environment and use emulator to generate random numbers with the seed we assigned. The solution we provided was chose this method.**

2. Building Environment

   * Emulators: [Yuzu](https://yuzu-emu.org/)、[Ryujinx](https://ryujinx.org/)
* Development: https://switchbrew.org/wiki/Setting_up_Development_Environment
   
3. Analysis the log file

   We can make use of this script and do some modification:

   https://github.com/mart1nro/joycontrol/blob/master/scripts/parse_capture.py

   According to the time when the Switch Pro Controller receive the rumble packet to find the last direction before the snake scores. And then `seed` can be calculated. We can print all the seeds we got. 

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

4. Emulation & GetFLAG

   There is a great and easy demo to help you develop quickly.

   https://github.com/switchbrew/switch-examples/tree/master/templates/application

   Write some code to generate random coordinates and flag chars by the given seeds.

   There we get the flag.

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

   



