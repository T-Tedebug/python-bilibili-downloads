import sys
import subprocess
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
import requests
import json
from datetime import datetime

class BilibiliDownloaderGUI:
    def __init__(self):
        try:
            self.window = tk.Tk()
            self.window.title('B站视频下载器')
            self.window.geometry('600x400')
            
            def handle_error(exc, val, tb):
                messagebox.showerror("错误", str(val))
                self.window.destroy()
            
            self.window.report_callback_exception = handle_error
            
            self.main_frame = ttk.Frame(self.window, padding="10")
            self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            ttk.Label(self.main_frame, text="视频BV号:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.bv_entry = ttk.Entry(self.main_frame, width=40)
            self.bv_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            
            ttk.Label(self.main_frame, text="保存位置:").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.path_entry = ttk.Entry(self.main_frame, width=40)
            self.path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
            self.path_entry.insert(0, os.path.abspath('downloads'))
            
            self.browse_button = ttk.Button(self.main_frame, text="浏览", command=self.browse_path)
            self.browse_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
            
            ttk.Label(self.main_frame, text="清晰度:").grid(row=2, column=0, sticky=tk.W, pady=5)
            self.quality_var = tk.StringVar(value='80')
            self.quality_combo = ttk.Combobox(self.main_frame, textvariable=self.quality_var, width=20)
            self.quality_combo['values'] = ['16', '32', '64', '80', '112', '116', '120']
            self.quality_combo['state'] = 'readonly'
            self.quality_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
            
            quality_tips = {
                '16': '360P',
                '32': '480P',
                '64': '720P',
                '80': '1080P',
                '112': '1080P+',
                '116': '1080P60',
                '120': '4K'
            }
            self.quality_label = ttk.Label(self.main_frame, text=f"当前: {quality_tips.get(self.quality_var.get(), '')}")
            self.quality_label.grid(row=2, column=2, sticky=tk.W, pady=5)
            
            self.quality_combo.bind('<<ComboboxSelected>>', lambda e: self.quality_label.config(
                text=f"当前: {quality_tips.get(self.quality_var.get(), '')}"
            ))
            
            ttk.Label(self.main_frame, text="Cookie:").grid(row=3, column=0, sticky=tk.W, pady=5)
            self.cookie_entry = ttk.Entry(self.main_frame, width=40)
            self.cookie_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            
            self.load_cookie()
            
            self.save_cookie_var = tk.BooleanVar(value=True)
            self.save_cookie_check = ttk.Checkbutton(
                self.main_frame, 
                text="保存 Cookie", 
                variable=self.save_cookie_var
            )
            self.save_cookie_check.grid(row=4, column=0, columnspan=3, pady=5)
            
            self.download_button = ttk.Button(self.main_frame, text="开始下载", command=self.start_download)
            self.download_button.grid(row=5, column=0, columnspan=3, pady=20)
            
            self.progress = ttk.Progressbar(self.main_frame, length=400, mode='determinate')
            self.progress.grid(row=6, column=0, columnspan=3, pady=10)
            
            self.status_text = tk.Text(self.main_frame, height=10, width=50)
            self.status_text.grid(row=7, column=0, columnspan=3, pady=10)
            
            self.crawler = BilibiliCrawler()
            self.crawler.gui = self
            
        except Exception as e:
            messagebox.showerror("初始化错误", str(e))
            sys.exit(1)

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)
    
    def update_status(self, message):
        self.status_text.insert(tk.END, message + '\n')
        self.status_text.see(tk.END)
    
    def update_progress(self, value):
        self.progress['value'] = value
    
    def load_cookie(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'cookie' in config:
                        self.cookie_entry.insert(0, config['cookie'])
        except Exception as e:
            self.update_status(f"加载 Cookie 失败: {str(e)}")
    
    def save_cookie(self):
        if self.save_cookie_var.get():
            try:
                config = {}
                if os.path.exists('config.json'):
                    with open('config.json', 'r', encoding='utf-8') as f:
                        config = json.load(f)
                
                config['cookie'] = self.cookie_entry.get().strip()
                
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.update_status(f"保存 Cookie 失败: {str(e)}")
    
    def start_download(self):
        bv_id = self.bv_entry.get().strip()
        if not bv_id:
            messagebox.showerror("错误", "请输入视频BV号")
            return
        
        if not re.match(r'^BV[a-zA-Z0-9]+$', bv_id):
            messagebox.showerror("错误", "请输入正确的BV号格式")
            return
        
        self.save_cookie()
        
        self.crawler.download_path = self.path_entry.get()
        self.crawler.quality = self.quality_var.get()
        self.download_button.state(['disabled'])
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self.download_thread, args=(bv_id,))
        thread.start()
    
    def download_thread(self, bv_id):
        try:
            if self.crawler.download_video(bv_id):
                self.progress['value'] = 100
                self.update_status("下载完成！")
                messagebox.showinfo("成功", "视频下载完成！")
            else:
                self.update_status("下载失败")
                messagebox.showerror("错误", "下载失败，请查看详细信息")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
            messagebox.showerror("错误", str(e))
        finally:
            self.download_button.state(['!disabled'])

class BilibiliCrawler:
    def __init__(self, download_path='downloads'):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com'
        }
        self.download_path = os.path.abspath(download_path)
        self.quality = '80'
        self.cookie = ''
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        self.gui = None
    
    def update_status(self, message):
        if self.gui:
            self.gui.update_status(message)
    
    def update_progress(self, value):
        if self.gui:
            self.gui.update_progress(value)
    
    def get_headers(self):
        headers = self.headers.copy()
        if hasattr(self.gui, 'cookie_entry'):
            cookie = self.gui.cookie_entry.get().strip()
            if cookie:
                headers['Cookie'] = cookie
                if 'SESSDATA' not in cookie:
                    self.update_status("警告: Cookie 中缺少 SESSDATA，可能无法下载高清视频")
        return headers
    
    def get_video_info(self, bv_id):
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_id}'
        response = requests.get(url, headers=self.get_headers())
        data = response.json()
        
        if data['code'] == 0:
            video_data = data['data']
            return {
                'title': video_data['title'],
                'cid': video_data['cid'],
                'aid': video_data['aid']
            }
        return None

    def get_video_url(self, aid, cid):
        try:
            url = (f'https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn={self.quality}'
                   f'&fnval=4048&fourk=1&fnver=0&session=')
            
            headers = self.get_headers()
            headers.update({
                'Referer': f'https://www.bilibili.com/video/av{aid}',
                'Origin': 'https://www.bilibili.com',
            })
            
            self.update_status(f"正在请求视频地址: {url}")
            response = requests.get(url, headers=headers)
            self.update_status(f"API 响应状态码: {response.status_code}")
            
            try:
                data = response.json()
                self.update_status(f"API 返回代码: {data.get('code')}")
                self.update_status(f"API 返回信息: {data.get('message', '无')}")
            except Exception as e:
                self.update_status(f"解析响应失败: {str(e)}")
                self.update_status(f"原始响应: {response.text[:200]}...")
                return None
            
            if data['code'] == 0:
                accept_quality = data['data'].get('accept_quality', [])
                quality_list = [str(q) for q in accept_quality]
                
                quality_desc = {
                    '16': '360P',
                    '32': '480P',
                    '64': '720P',
                    '80': '1080P',
                    '112': '1080P+',
                    '116': '1080P60',
                    '120': '4K',
                    '125': 'HDR',
                    '126': 'Dolby Vision',
                    '127': '8K'
                }
                available_qualities = [f"{q}({quality_desc.get(q, '未知')})" for q in quality_list]
                self.update_status(f"可用清晰度: {', '.join(available_qualities)}")
                
                if self.quality not in quality_list:
                    self.update_status(f"当前清晰度不可用，自动切换到最高可用清晰度: {quality_list[0]}")
                    self.quality = quality_list[0]
                    return self.get_video_url(aid, cid)
                
                if 'dash' in data['data']:
                    dash = data['data']['dash']
                    video_url = None
                    audio_url = None
                    
                    for video in dash['video']:
                        if str(video['id']) == self.quality:
                            video_url = video['baseUrl']
                            self.update_status(f"找到视频流: {video['id']}({quality_desc.get(str(video['id']), '未知')})")
                            break
                    
                    if dash['audio']:
                        audio_url = dash['audio'][0]['baseUrl']
                        self.update_status("找到音频流")
                    
                    if video_url and audio_url:
                        self.update_status("成功获取视频和音频地址")
                        return {'video': video_url, 'audio': audio_url, 'is_dash': True}
                    else:
                        self.update_status("无法获取完整的视频/音频地址")
                    
                elif 'durl' in data['data']:
                    self.update_status("使用普通格式下载")
                    return {'video': data['data']['durl'][0]['url'], 'is_dash': False}
                else:
                    self.update_status("未找到可用的视频格式")
                
            elif data['code'] == -404:
                self.update_status("视频不存在或已被删除")
            elif data['code'] == -403:
                self.update_status("权限不足，请检查 Cookie 是否正确填写，或是否具有大会员权限")
                self.update_status("提示：请确保 Cookie 中包含 SESSDATA 字段")
            else:
                self.update_status(f"获取视频地址失败: {data.get('message', '未知错误')}")
                self.update_status("请尝试更新 Cookie 或检查视频是否可以正常播放")
            
        except Exception as e:
            self.update_status(f"请求视频地址时发生错误: {str(e)}")
            import traceback
            self.update_status(f"错误详情: {traceback.format_exc()}")
        return None

    def download_file(self, url, filepath, chunk_size=1024*1024):
        response = requests.get(url, headers=self.get_headers(), stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = chunk_size
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for data in response.iter_content(block_size):
                downloaded += len(data)
                f.write(data)
                if total_size:
                    progress = int((downloaded / total_size) * 100)
                    self.update_progress(progress)
                    self.update_status(f'下载进度: {progress}%')

    def download_video(self, bv_id):
        try:
            self.update_status("获取视频信息...")
            video_info = self.get_video_info(bv_id)
            if not video_info:
                self.update_status("获取视频信息失败")
                return False

            title = video_info['title'].replace('/', '_').replace('\\', '_')
            video_dir = os.path.join(self.download_path, title)
            if not os.path.exists(video_dir):
                os.makedirs(video_dir)

            self.update_status(f'开始下载: {title}')
            self.update_status(f'保存位置: {video_dir}')

            urls = self.get_video_url(video_info['aid'], video_info['cid'])
            if not urls:
                self.update_status("获取视频地址失败")
                return False

            if urls.get('is_dash'):
                self.update_status("下载视频流...")
                video_path = os.path.join(video_dir, f'{title}_video.m4s')
                self.download_file(urls['video'], video_path)
                
                self.update_status("下载音频流...")
                audio_path = os.path.join(video_dir, f'{title}_audio.m4s')
                self.download_file(urls['audio'], audio_path)
                
                self.update_status("合并音视频...")
                output_path = os.path.join(video_dir, f'{title}.mp4')
                
                ffmpeg_path = self.get_ffmpeg_path()
                cmd = [
                    ffmpeg_path,
                    '-i', video_path,
                    '-i', audio_path,
                    '-c', 'copy',
                    output_path
                ]
                
                subprocess.run(cmd, check=True)
                
                os.remove(video_path)
                os.remove(audio_path)
                
            else:
                video_path = os.path.join(video_dir, f'{title}.mp4')
                self.download_file(urls['video'], video_path)
            
            self.update_status(f'下载完成: {title}')
            return True

        except Exception as e:
            self.update_status(f'下载失败: {str(e)}')
            return False

    def get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            ffmpeg_path = os.path.join(application_path, 'ffmpeg.exe')
        else:
            ffmpeg_path = 'ffmpeg'
        return ffmpeg_path

def main():
    app = BilibiliDownloaderGUI()
    app.window.mainloop()

if __name__ == '__main__':
    main() 