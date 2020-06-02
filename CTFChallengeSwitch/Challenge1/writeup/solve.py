import ffmpeg
# install ffmpeg to your system and then pip3 install ffmpeg-python
import numpy
import cv2
import json

KEY_A = 0b00001000
TIMEDELTA = 0
JSON_FILE = 'capture.json'
# capture.json should be export from Wireshark
VIDEO_FILE = '../attachment/screenrecord.mp4'
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
		_sum = data[1]
		_sumcnt = 1
	_lastid = data[0]
print(time_avg)

# extract frames from the video one by one
TIMEDELTA = 27.4 - time_avg[2]
# In the video, CAPS_LOCK is pressed twice times.
# At 27.4s, the first character 'R' appears 
# that correspond to time_avg[2] when KEY_A was pressed
for t in time_avg:
	t += TIMEDELTA
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