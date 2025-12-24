import pyaudio

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = p.get_device_count()

print("Available Audio Devices:")
for i in range(0, numdevices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    # Check if the device is an input device (microphone)
    if (device_info.get('maxInputChannels')) > 0:
        print(f"  Input Device Index {i} - {device_info.get('name')}")
