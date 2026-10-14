import os
import subprocess
import time

# Single Video Link for Live Stream
video_link = 'https://drive.google.com/file/d/1-Dr_eOLCMxqP7puqyDtydyKhmduw15SF/view?usp=drivesdk'

# Permanent Left-Side Pulsing Logo ID
logo_id = '1Efg-hEkub7r8kR1yzQHzv4JnTvZnS5xe'

stream_key = os.environ.get('STREAM_KEY')
rtmp_url = f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'


def extract_id(link):
  import re

  match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
  return match.group(1) if match else link.strip()


def download_and_prepare():
  # 1. Install gdown
  subprocess.run(['pip', 'install', 'gdown'])

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

  # 3. Download the Single Video
  file_id = extract_id(video_link)
  output_file = 'video.mp4'
  print('Downloading Single Live Video...')
  subprocess.run([
      'gdown',
      f'https://drive.google.com/uc?id={file_id}',
      '-O',
      output_file,
      '--fuzzy',
  ])

  if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
    print('Error: Video download failed!')
    return False

  # 4. Process Video with Blur Background & Pulsing Logo
  converted_file = 'ready.mp4'
  print('Processing Video with Left-Side Logo Overlay & Blur Background...')

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
  return os.path.exists(converted_file)


def stream_video():
  print('Starting continuous looped live stream for the single video...')
  ffmpeg_cmd = [
      'ffmpeg',
      '-re',
      '-stream_loop',
      '-1',
      '-i',
      'ready.mp4',
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
    print('Stream disconnected. Reconnecting in 5 seconds...')
    time.sleep(5)


if __name__ == '__main__':
  if download_and_prepare():
    stream_video()
