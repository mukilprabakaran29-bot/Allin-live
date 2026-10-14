import os
import re
import subprocess

# Complete sequence of all 13 videos
video_links = [
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 1. Intro
    (
        'https://drive.google.com/file/d/1-Dr_eOLCMxqP7puqyDtydyKhmduw15SF/view?usp=drivesdk'
    ),  # 2. Main
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 3. Second Intro
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 4. Short 4
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 5. Short 5
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 6. Short 6
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 7. Short 7
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 8. Short 8
    (
        'https://drive.google.com/file/d/1hkKADV8rIPaL-I89-ZzQMgUQuBTE7ECb/view?usp=drivesdk'
    ),  # 9. Short 9
    (
        'https://drive.google.com/file/d/1bpQ_kKdPl32hMrElYNTHfkDH5NstC-pF/view?usp=drivesdk'
    ),  # 10. Highlight Short
    (
        'https://drive.google.com/file/d/1cvKVIDrGDTSEg_eD-Zj02cJxB3bYuAhg/view?usp=drivesdk'
    ),  # 11. Vibe Big Video
    (
        'https://drive.google.com/file/d/1rd1m5XDps6soYDPbXAQJ5A8av5uISycJ/view?usp=drivesdk'
    ),  # 12. Extra Video
    (
        'https://drive.google.com/file/d/1H-VSfWm6ZiruBx3ZHbaLBGtCXr6lScrD/view?usp=drivesdk'
    ),  # 13. Ending Video
]

# Permanent Left-Side Pulsing Logo Link
logo_link = 'https://drive.google.com/file/d/1Efg-hEkub7r8kR1yzQHzv4JnTvZnS5xe/view?usp=drivesdk'

stream_key = os.environ.get('STREAM_KEY')
rtmp_url = f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'


def extract_id(link):
  match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
  return match.group(1) if match else None


def download_and_prepare():
  downloaded_files = []

  # 1. Download Logo
  logo_id = extract_id(logo_link)
  logo_file = 'logo.png'
  if logo_id:
    print('Downloading Left-Side Banner Logo...')
    cmd_logo = [
        'yt-dlp',
        '-o',
        logo_file,
        f'https://drive.google.com/uc?id={logo_id}',
    ]
    subprocess.run(cmd_logo)

  # 2. Download and process videos
  for i, link in enumerate(video_links):
    file_id = extract_id(link)
    if not file_id:
      continue
    output_file = f'video_{i}.mp4'
    print(f'Downloading Video {i+1}...')
    cmd = [
        'yt-dlp',
        '-o',
        output_file,
        f'https://drive.google.com/uc?id={file_id}',
    ]
    subprocess.run(cmd)

    if os.path.exists(output_file):
      converted_file = f'ready_{i}.mp4'
      print(f'Processing Video {i+1} with Left-Side Logo Overlay & Blur...')

      if os.path.exists(logo_file):
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
      downloaded_files.append(converted_file)

  if downloaded_files:
    with open('playlist.txt', 'w') as f:
      for file in downloaded_files:
        f.write(f"file '{file}'\n")
    return True
  return False


def stream_playlist():
  print(
      'Starting continuous live stream with automated sizing, left-side logo,'
      ' and ending video sequence...'
  )
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
  subprocess.run(ffmpeg_cmd)


if __name__ == '__main__':
  if download_and_prepare():
    stream_playlist()
