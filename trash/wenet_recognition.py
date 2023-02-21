''' wenet_recognition '''

import os
import time
import wave
import wenetruntime as wenet
import json

# audio_path = 'test/test-dang-an-shi-shen-me.wav'
audio_path = 'test/test-something.wav'

model_dir = os.path.join(os.path.dirname(__file__), 'speech_recognition/models/chs')
decoder = wenet.Decoder(model_dir=model_dir, lang='chs')

# if True:
for i in range(10):
    # time.sleep(30)
    t1 = time.time()
    ans = decoder.decode_wav(audio_path)
    ans = json.loads(ans)['nbest'][0]['sentence']
    t2 = time.time()
    print(ans, t2-t1)
