import sys
import subprocess
import os
import shutil

def install_package(package):
    try:
        print(f'正在安装 {package}...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f'{package} 安装完成')
    except subprocess.CalledProcessError as e:
        print(f'安装 {package} 失败: {e}')
        sys.exit(1)

try:
    import PyInstaller.__main__
except ImportError:
    install_package('pyinstaller')
    import PyInstaller.__main__

current_dir = os.path.dirname(os.path.abspath(__file__))

ffmpeg_path = os.path.join(current_dir, 'ffmpeg.exe')
if not os.path.exists(ffmpeg_path):
    print('错误: 找不到 ffmpeg.exe')
    print('请下载 ffmpeg.exe 并放置在脚本同目录下')
    sys.exit(1)

dist_dir = os.path.join(current_dir, 'dist')
if not os.path.exists(dist_dir):
    os.makedirs(dist_dir)

PyInstaller.__main__.run([
    'bilibili_crawler.py',
    '--name=B站视频下载器',
    '--onefile',
    '--noconsole',
    '--add-data=ffmpeg.exe;.',
    '--hidden-import=requests',
    '--hidden-import=tkinter',
    '--hidden-import=json',
    '--hidden-import=threading',
    '--hidden-import=subprocess',
    '--hidden-import=datetime',
    '--hidden-import=re',
    '--hidden-import=os',
    '--hidden-import=sys',
    '--workpath=build',
    '--distpath=dist',
    '--clean',
])

print('正在复制 ffmpeg.exe 到输出目录...')
try:
    shutil.copy2(ffmpeg_path, os.path.join(dist_dir, 'ffmpeg.exe'))
    print('ffmpeg.exe 复制完成')
except Exception as e:
    print(f'复制 ffmpeg.exe 失败: {e}')
    print('请手动将 ffmpeg.exe 复制到程序所在目录')

print('\n打包完成！')
print('请确保以下文件在同一目录：')
print('1. B站视频下载器.exe')
print('2. ffmpeg.exe') 