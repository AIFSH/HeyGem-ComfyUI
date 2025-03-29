'''
合成接口：http://127.0.0.1:8383/easy/submit

// 请求参数
{
  "audio_url": "{audioPath}", // 音频路径
  "video_url": "{videoPath}", // 视频路径
  "code": "{uuid}", // 唯一key
  "chaofen": 0, // 固定值
  "watermark_switch": 0, // 固定值
  "pn": 1 // 固定值
}
进度查询：http://127.0.0.1:8383/easy/query?code=${taskCode}

get 请求，参数taskCode是上面合成接口入参中的code
'''
import os
import time
import json
import uuid
import shutil
import requests
import tempfile
import torchaudio
import folder_paths
from tqdm import tqdm
from pathlib import Path
from comfy.utils import ProgressBar
input_dir = folder_paths.get_input_directory()
heygem_dir = os.path.join(input_dir,"heygem")
os.makedirs(heygem_dir,exist_ok=True)
output_dir = folder_paths.get_output_directory()
class HeyGemNode:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required":{
                "audio_url":("AUDIO",),
                "video_url":("VIDEO",),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    #RETURN_NAMES = ("image_output_name",)

    FUNCTION = "gen_video"

    #OUTPUT_NODE = False

    CATEGORY = "AIFSH/HeyGem"

    def gen_video(self,audio_url,video_url):
        tmp_dir = os.path.join(heygem_dir,"temp")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir,exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".wav",delete=False,dir=tmp_dir) as input_wav:
            waveform = audio_url['waveform'][0]
            torchaudio.save(input_wav.name,waveform,audio_url['sample_rate'])
        taskCode = f"{uuid.uuid4()}"
        video_name =  Path(video_url).name
        shutil.copyfile(video_url,os.path.join(tmp_dir,video_name))
        data = {
            "audio_url": Path(input_wav.name).name, # 音频路径
            "video_url": video_name, # 视频路径
            "code": taskCode,# 唯一key
            "chaofen": 0, # 固定值
            "watermark_switch": 0, # 固定值
            "pn": 1 # 固定值
        }
        data = json.dumps(data)
        post_response = requests.post(url="http://127.0.0.1:8383/easy/submit",data=data)
        print(post_response.status_code)
        print(post_response.text)
        get_response = requests.get(url=f"http://127.0.0.1:8383/easy/query?code={taskCode}")
        comfy_bar = ProgressBar(50)
        tq_bar = tqdm(desc="HeyGem...")
        status = json.loads(get_response.content)["data"]["status"]
        while status==1:
            get_response = requests.get(url=f"http://127.0.0.1:8383/easy/query?code={taskCode}")
            content = json.loads(get_response.content)
            #print(content)
            status = content["data"]["status"]
            time.sleep(5)
            tq_bar.update(1)
            comfy_bar.update(1)
        res_viedo = os.path.join(tmp_dir,f"{taskCode}-r.mp4")
        audio_file = input_wav.name
        final_video = os.path.join(output_dir,f"{taskCode}-r.mp4")
        cmd = f"ffmpeg -i {res_viedo} -i {audio_file} -vcodec copy -acodec copy {final_video}"
        os.system(cmd)
        return (final_video, )

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "HeyGemNode": HeyGemNode
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "HeyGemNode": "HeyGemNode@关注微信公众号“超级面爸”"
}
