import os
import re
import subprocess
import time

# Complete sequence of all 13 videos (Google Drive File IDs or Links)
video_links = [
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 1. Intro
    '1-Dr_eOLCMxqP7puqyDtydyKhmduw15SF',  # 2. Main
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 3. Second Intro
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 4. Short 4
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 5. Short 5
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 6. Short 6
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 7. Short 7
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 8. Short 8
    '1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb',  # 9. Short 9
    '1bpQ_kKdPl32hMrElYNTHfkDH5NstC-pF',  # 10. Highlight Short
    '1cvKVIDrGDTSEg_eD-Zj02cJxB3bYuAhg',  # 11. Vibe Big Video
    '1rd1m5XDps6soYDPbXAQJ5A8av5uISycJ',  # 12. Extra Video
    '1H-VSfWm6ZiruBx3ZHbaLBGtCXr6lScrD',  # 13. Ending Video
]

# Permanent Left-Side Pulsing Logo ID
logo_id = '1Efg-hEkub7r8kR1yzQHzv4JnTvZnS5xe'

stream_key = os.environ.get('STREAM_KEY')
rtmp_url = f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'


def extract_id(link_or_id):
  match = re.search(r'/d/([a-zA-Z0-9_-]+)', link_or_id)
  if match:
    return match.group(1)
  return link_or_id.strip()


def download_and_prepare():
  downloaded_files = []

  # 1. Install gdown if not available
  subprocess.run(['pip', 'install', 'gdown', 'ffmpeg-python'])

  # 2. Download Logo
  logo_file = 'logo.png'
  clean_logo_id = extract_id(logo_id)
  print('Downloading Left-Side Banner Logo...')
  subprocess.run([
      'gdown',
      f'https://drive.google.com/uc?id={clean_logo_id}',
      '-O',
      logo_file,
      '--fuzzy',
  ])

  # 3. Download and process videos
  for i, link in enumerate(video_links):
    file_id = extract_id(link)
    if not file_id:
      continue
    output_file = f'video_{i}.mp4'
    print(f'Downloading Video {i+1}...')
    subprocess.run([
        'gdown',
        f'https://drive.google.com/uc?id={file_id}',
        '-O',
        output_file,
        '--fuzzy',
    ])

    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
      converted_file = f'ready_{i}.mp4'
      print(f'Processing Video {i+1} with Left-Side Logo Overlay & Blur...')

      if os.path.exists(logo_file) and os.path.getsize(logo_file) > 1000:
        ffmpeg_filter = (
            '[0:v]scale=1920:1080,boxblur=r=20:p=1[bg];'
            '[0:v]scale=-1:1080:force_original_aspect_ratio=decrease[fg];'
            '[bg][fg]overlay=(W-w)/2:(H-h)/2[base];'
            '[1:v]scale=220:-1[scaled_logo];'
            "[scaled_logo]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='a(X,Y)*(0.6+0.4*sin(T*3))'[pulsing_logo];"
            '[base][pulsing_logo]overlay=40:40,format=yuv420p[v]'
        )
        convert_cmd = [
            'ffmpeg',
            '-y',
            '-i',
            output_file,
            '-i',
            logo_file,
            '-filter_complex',
            ffmpeg_filter,
            '-map',
            '[v]',
            '-c:v',
            'libx264',
            '-preset',
            'ultrafast',
            '-r',
            '30',
            '-c:a',
            'aac',
            '-b:a',
            '128k',
            '-ar',
            '44100',
            converted_file,
        ]
      else:
        ffmpeg_filter = (
            '[0:v]scale=1920:1080,boxblur=r=20:p=1[bg];'
            '[0:v]scale=-1:1080:force_original_aspect_ratio=decrease[fg];'
            '[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]'
        )
        convert_cmd = [
            'ffmpeg',
            '-y',
            '-i',
            output_file,
            '-filter_complex',
            ffmpeg_filter,
            '-map',
            '[v]',
            '-c:v',
            'libx264',
            '-preset',
            'ultrafast',
            '-r',
            '30',
            '-c:a',
            'aac',
            '-b:a',
            '128k',
            '-ar',
            '44100',
            converted_file,
        ]

      subprocess.run(convert_cmd)
      if os.path.exists(converted_file):
        downloaded_files.append(converted_file)

  if downloaded_files:
    with open('playlist.txt', 'w') as f:
      for file in downloaded_files:
        f.write(f"file '{file}'\n")
    return True
  return False


def stream_playlist():
  print('Starting continuous auto-reconnecting live stream...')
  ffmpeg_cmd = [
      'ffmpeg',
      '-re',
      '-f',
      'concat',
      '-safe',
      '0',
      '-stream_loop',
      '-1',
      '-i',
      'playlist.txt',
      '-c:v',
      'libx264',
      '-preset',
      'veryfast',
      '-b:v',
      '3000k',
      '-maxrate',
      '3000k',
      '-bufsize',
      '6000k',
      '-pix_fmt',
      'yuv420p',
      '-g',
      '60',
      '-c:a',
      'aac',
      '-b:a',
      '128k',
      '-ar',
      '44100',
      '-f',
      'flv',
      rtmp_url,
  ]

  while True:
    process = subprocess.Popen(ffmpeg_cmd)
    process.wait()
    print('Stream disconnected or restarted. Reconnecting in 5 seconds...')
    time.sleep(5)


if __name__ == '__main__':
  if download_and_prepare():
    stream_playlist()
