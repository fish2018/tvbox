# -*- coding: utf-8 -*-
# !/usr/bin/env python3
from requests_html import HTMLSession
import pprint
import random
import string
import time
import hashlib
import json
import git  # gitpython
import re
import base64
import requests
import asyncio
import aiohttp
from requests.adapters import HTTPAdapter, Retry
import os
import subprocess
import ssl
import shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urljoin
import commentjson
ssl._create_default_https_context = ssl._create_unverified_context
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

global pipes
pipes = set()

class GetSrc:
    def __init__(self, username=None, token=None, url=None, repo=None, num=10, target=None, timeout=3, signame=None, mirror=None, jar_suffix=None, site_down=True):
        self.jar_suffix = jar_suffix if jar_suffix else 'jar'
        self.site_down = site_down # 是否下载site里的文件到本地
        self.mirror = int(str(mirror).strip()) if mirror else 1
        self.mirror_proxy = 'https://ghp.ci/https://raw.githubusercontent.com'
        self.num = int(num)
        self.sep = os.path.sep
        self.username = username
        self.token = token
        self.timeout=timeout
        self.url = url.replace(' ','').replace('，',',') if url else url
        self.repo = repo if repo else 'tvbox'
        self.target = f'{target.split(".json")[0]}.json' if target else 'tvbox.json'
        self.headers = {"user-agent": "okhttp/3.15 Html5Plus/1.0 (Immersed/23.92157)"}
        self.s = requests.Session()
        self.signame = signame
        retries = Retry(total=3, backoff_factor=1)
        self.s.mount('http://', HTTPAdapter(max_retries=retries))
        self.s.mount('https://', HTTPAdapter(max_retries=retries))
        self.size_tolerance = 15 # 线路文件大小误差在15以内认为是同一个
        self.main_branch = 'main'
        self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        self.cnb_slot = f'https://cnb.cool/{self.username}/{self.repo}/-/git/raw/{self.main_branch}'

        self.registry = 'cnb.cool'
        self.gitusername = 'cnb'
        self.repo = repo
        self.token = token
        self.branch = 'main'

        self.gh1 = [
            'https://ghp.ci/https://raw.githubusercontent.com',
            'https://gh.xxooo.cf/https://raw.githubusercontent.com',
            'https://ghproxy.net/https://raw.githubusercontent.com',
            'https://github.moeyy.xyz/https://raw.githubusercontent.com',
            'https://gh-proxy.com/https://raw.githubusercontent.com',
            'https://ghproxy.cc/https://raw.githubusercontent.com',
            'https://raw.yzuu.cf',
            'https://raw.nuaa.cf',
            'https://raw.kkgithub.com',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com',
            'https://gh.llkk.cc/https://raw.githubusercontent.com',
            'https://gh.ddlc.top/https://raw.githubusercontent.com',
            'https://gh-proxy.llyke.com/https://raw.githubusercontent.com',
            'https://slink.ltd',
            'https://cors.zme.ink',
            'https://git.886.be'
        ]
        self.gh2 = [
            "https://fastly.jsdelivr.net/gh",
            "https://jsd.onmicrosoft.cn/gh",
            "https://gcore.jsdelivr.net/gh",
            "https://cdn.jsdmirror.com/gh",
            "https://cdn.jsdmirror.cn/gh",
            "https://jsd.proxy.aks.moe/gh",
            "https://jsdelivr.b-cdn.net/gh",
            "https://jsdelivr.pai233.top/gh"
        ]

        # 定义 drpy2 文件列表
        self.drpy2 = False
        self.drpy2_files = [
            "cat.js", "crypto-js.js", "drpy2.min.js", "http.js", "jquery.min.js",
            "jsencrypt.js", "log.js", "pako.min.js", "similarity.js", "uri.min.js",
            "cheerio.min.js", "deep.parse.js", "gbk.js", "jinja.js", "json5.js",
            "node-rsa.js", "script.js", "spider.js", "模板.js", "quark.min.js"
        ]

    async def download_drpy2_files(self):
        """
        异步下载 drpy2 文件到 self.repo/api/drpy2
        """
        # 创建 drpy2 目录
        api_drpy2_dir = os.path.join(self.repo, "api/drpy2")
        if not os.path.exists(api_drpy2_dir):
            os.makedirs(api_drpy2_dir)
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=60, connect=15)
        ) as session:
            tasks = []
            for filename in self.drpy2_files:
                local_path = os.path.join(api_drpy2_dir, filename)
                if os.path.exists(local_path):
                    # print(f"文件已存在，跳过: {local_path}")
                    continue
                json_url = f"https://github.moeyy.xyz/https://raw.githubusercontent.com/fish2018/lib/main/js/dr_py/{filename}"

                async def download_task(json_url=json_url, local_path=local_path, filename=filename):
                    retries = 3
                    for attempt in range(retries):
                        try:
                            async with session.get(json_url) as response:
                                response.raise_for_status()
                                content = await response.read()
                                with open(local_path, "wb") as f:
                                    f.write(content)
                                # print(f"下载成功: {filename}")
                                return True
                        except Exception as e:
                            # print(f"下载 {json_url} 失败 (尝试 {attempt + 1}/{retries}): {e}")
                            if attempt < retries - 1:
                                await asyncio.sleep(1)
                            else:
                                print(f"下载 {json_url} 最终失败")
                                return False

                tasks.append(download_task())

            if tasks:
                # print(f"开始下载 {len(tasks)} 个 drpy2 文件")
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                pass
                # print("所有 drpy2 文件已存在，无需下载")
    def file_hash(self, filepath):
        with open(filepath, 'rb') as f:
            file_contents = f.read()
            return hashlib.sha256(file_contents).hexdigest()
    def remove_duplicates(self, folder_path):
        folder_path = Path(folder_path)
        jar_folder = f'{folder_path}/jar'
        excludes = {'.json', '.git', 'jar', '.idea', 'ext', '.DS_Store', '.md'}
        files_info = {}

        # 把jar目录下所有文件后缀都改成新的self.jar_suffix
        self.rename_jar_suffix(jar_folder)

        # 存储文件名、大小和哈希值
        for file_path in folder_path.iterdir():
            if file_path.is_file() and file_path.suffix not in excludes:
                file_size = file_path.stat().st_size
                file_hash = self.file_hash(file_path)
                files_info[file_path.name] = {'path': str(file_path), 'size': file_size, 'hash': file_hash}

        # 保留的文件列表
        keep_files = []
        # 按文件大小排序，然后按顺序处理
        for file_name, info in sorted(files_info.items(), key=lambda item: item[1]['size']):
            if not keep_files or abs(info['size'] - files_info[keep_files[-1]]['size']) > self.size_tolerance:
                keep_files.append(file_name)
                # 删除jar目录下除了{self.jar_suffix}的文件
                # self.remove_all_except_jar(jar_folder)
            else:
                # 如果当前文件大小在容忍范围内，删除当前文件和对应的jar文件
                os.remove(info['path'])
                self.remove_jar_file(jar_folder, file_name.replace('.txt', f'{self.jar_suffix}'))

        keep_files.sort()
        return keep_files
    def rename_jar_suffix(self,jar_folder):
        # 遍历目录中的所有文件和子目录
        for root, dirs, files in os.walk(jar_folder):
            for file in files:
                # 构造完整的文件路径
                old_file = os.path.join(root, file)
                # 构造新的文件名，去除原有的后缀，加上 self.jar_suffix
                new_file = os.path.join(root, os.path.splitext(file)[0] + f'.{self.jar_suffix}')
                # 重命名文件
                os.rename(old_file, new_file)
                # print(f"文件已重命名: {old_file} -> {new_file}")
    def remove_all_except_jar(self, jar_folder):
        # 列出文件夹中的所有文件
        for file_name in os.listdir(jar_folder):
            # 构建完整的文件路径
            full_path = os.path.join(jar_folder, file_name)
            # 检查是否为文件
            if os.path.isfile(full_path):
                # 获取文件的扩展名
                _, file_extension = os.path.splitext(file_name)
                # 如果扩展名不是self.jar_suffix，则删除文件
                if file_extension != f'.{self.jar_suffix}':
                    self.remove_jar_file(jar_folder, file_name)
    def remove_jar_file(self, jar_folder, file_name):
        # 构建jar文件的路径
        jar_file_path = os.path.join(jar_folder, file_name)
        # 如果jar文件存在，则删除它
        if os.path.isfile(jar_file_path):
            os.remove(jar_file_path)
    def remove_emojis(self, text):
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   "\U00002500-\U00002BEF"  # chinese char
                                   "\U00010000-\U0010ffff"
                                   "\u200d"  # zero width joiner
                                   "\u20E3"  # combining enclosing keycap
                                   "\ufe0f"  # VARIATION SELECTOR-16
                                   "]+", flags=re.UNICODE)
        text = text.replace('/', '_').replace('多多', '').replace('┃', '').replace('线路', '').replace('匚','').strip()
        return emoji_pattern.sub('', text)
    def json_compatible(self, str):
        # 兼容错误json
        # res = str.replace(' ', '').replace("'",'"').replace('//"', '"').replace('//{', '{').replace('key:', '"key":').replace('name:', '"name":').replace('type:', '"type":').replace('api:','"api":').replace('searchable:', '"searchable":').replace('quickSearch:', '"quickSearch":').replace('filterable:','"filterable":').strip()
        res = str.replace('//"', '"').replace('//{', '{').replace('key:', '"key":').replace('name:', '"name":').replace('type:', '"type":').replace('api:','"api":').replace('searchable:', '"searchable":').replace('quickSearch:', '"quickSearch":').replace('filterable:','"filterable":').strip()
        return res
    def ghproxy(self, str):
        u = 'https://github.moeyy.xyz/'
        res = str.replace('https://ghproxy.net/', u).replace('https://ghproxy.com/', u).replace('https://gh-proxy.com/',u).replace('https://mirror.ghproxy.com/',u).replace('https://gh.xxooo.cf/',u).replace('https://ghp.ci/',u).replace('https://gitdl.cn/',u)
        return res
    def set_hosts(self):
        # 设置github.com的加速hosts
        try:
            response = requests.get('https://hosts.gitcdn.top/hosts.json')
            if response.status_code == 200:
                hosts_data = response.json()
                # 遍历JSON数据，找到"github.com"对应的IP
                github_ip = None
                for entry in hosts_data:
                    if entry[1] == "github.com":
                        github_ip = entry[0]
                        break
                if github_ip:
                    # 读取现有的/etc/hosts文件
                    with open('/etc/hosts', 'r+') as file:
                        hosts_content = file.read()
                        # 检查是否已经存在对应的IP
                        if github_ip not in hosts_content:
                            # 将新的IP添加到文件末尾
                            file.write(f'\n{github_ip} github.com')
                            print(f'IP address {github_ip} for github.com has been added to /etc/hosts.')
                        else:
                            print(f'IP address for github.com is already in /etc/hosts.')
                else:
                    print('No IP found for github.com in the provided data.')
            else:
                print('Failed to retrieve data from https://hosts.gitcdn.top/hosts.json')
        except Exception as e:
            pass
    def picparse(self, url):
        r = self.s.get(url, headers=self.headers, timeout=self.timeout, verify=False)
        pattern = r'([A-Za-z0-9+/]+={0,2})'
        matches = re.findall(pattern, r.text)
        decoded_data = base64.b64decode(matches[-1])
        text = decoded_data.decode('utf-8')
        return text

    async def js_render(self, url):
        # 获取 JS 渲染页面源代码
        timeout = self.timeout * 4
        if timeout > 15:
            timeout = 15
        browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-setuid-sandbox',
        ]
        from requests_html import AsyncHTMLSession

        session = AsyncHTMLSession(browser_args=browser_args)
        try:
            r = await session.get(
                f'http://lige.unaux.com/?url={url}',
                headers=self.headers,
                timeout=timeout,
                verify=False,
            )
            # 等待页面加载完成并渲染 JavaScript
            await r.html.arender(timeout=timeout)
            return r.html
        finally:
            await session.close()
    async def site_file_down(self, files, url):
        """
        异步函数，用于同时下载和更新 ext、jar 和 api 文件。

        参数:
            files: 包含一个或两个文件路径的列表，例如 ['api.json', 'output.json']
            url: 基础 URL，用于构造完整的下载 URL
        """
        # 设置 ext、jar 和 api 的保存目录
        ext_dir = f"{self.repo}/ext"
        jar_dir = f"{self.repo}/jar"
        api_dir = f"{self.repo}/api"
        api_drpy2_dir = f"{self.repo}/api/drpy2"
        for directory in [ext_dir, jar_dir, api_dir, api_drpy2_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        # 获取文件路径并读取 api.json
        file = files[0]
        file2 = files[1] if len(files) > 1 else ''

        with open(file, 'r', encoding='utf-8') as f:
            try:
                api_data = commentjson.load(f)
                sites = api_data["sites"]
                print(f"总站点数: {len(sites)}")
            except Exception as e:
                # print(f"解析 {file} 失败: {e}")
                return

        # 使用 aiohttp 创建会话并收集下载任务
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=60, connect=15)
        ) as session:
            tasks = []
            for site in sites:
                for field in ["ext", "jar", "api"]:
                    repo_dir_name = field
                    if field in site:
                        value = site[field]
                        if isinstance(value, str):
                            clean_value = value.split(';')[0].rstrip('?')
                            if field == "ext":
                                if not clean_value.endswith((".js", ".txt", ".json")):
                                    continue
                            elif field == "api":
                                if os.path.basename(clean_value).lower() in ["drpy2.min.js","quark.min.js"]:
                                    self.drpy2 = True
                                    # 替换 api 字段
                                    site[field] = f"{self.cnb_slot}/{api_drpy2_dir}/{os.path.basename(clean_value).lower()}"
                                    continue
                                if not clean_value.endswith(".py"):
                                    continue

                            # 默认下载逻辑（ext、jar 和 api 的 .py 文件）
                            filename = os.path.basename(clean_value)
                            if './' in value:
                                path = os.path.dirname(url)
                                json_url = value.replace('./', f'{path}/')
                            else:
                                json_url = urljoin(url, value)
                            local_path = os.path.join(f"{self.repo}/{repo_dir_name}", filename)

                            async def download_task(site=site, json_url=json_url, local_path=local_path,
                                                    filename=filename, field=field, repo_dir_name=repo_dir_name):
                                retries = 3
                                for attempt in range(retries):
                                    try:
                                        async with session.get(json_url) as response:
                                            response.raise_for_status()
                                            if os.path.exists(local_path):
                                                site[field] = f'{self.cnb_slot}/{repo_dir_name}/{filename}'
                                                return True
                                            content = await response.read()
                                            with open(local_path, "wb") as f:
                                                f.write(content)
                                            site[field] = f'{self.cnb_slot}/{repo_dir_name}/{filename}'
                                            return True
                                    except Exception as e:
                                        # print(f"下载 {json_url} 失败 (尝试 {attempt + 1}/{retries}): {e}")
                                        if attempt < retries - 1:
                                            await asyncio.sleep(1)
                                        else:
                                            # print(f"下载 {json_url} 最终失败")
                                            return False

                            tasks.append(download_task())

            if tasks:
                # print(f"总下载任务数: {len(tasks)}")
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                pass
                # print("没有找到符合条件的 ext、jar 或 api 文件需要下载")

        # 将更新后的数据写回文件
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, indent=4, ensure_ascii=False)

        if file2 and os.path.basename(file2):
            with open(file2, 'w', encoding='utf-8') as f:
                json.dump(api_data, f, indent=4, ensure_ascii=False)
    def get_jar(self, name, url, text):
        if not os.path.exists(f'{self.repo}/jar'):
            os.makedirs(f'{self.repo}/jar')
        name = f'{name}.{self.jar_suffix}'
        pattern = r'\"spider\":(\s)?\"([^,]+)\"'
        matches = re.search(pattern, text)
        try:
            jar = matches.group(2).replace('./', f'{url}/').split(';')[0]
            jar = jar.split('"spider":"')[-1]
            if name==f'{self.repo}.{self.jar_suffix}':
                name = f"{jar.split('/')[-1]}"
            print('jar地址: ', jar)
            timeout = self.timeout * 4
            if timeout > 15:
                timeout = 15
            r = self.s.get(jar, timeout=timeout, verify=False)
            if r.status_code != 200:
                raise f'【jar下载失败】{name} jar地址: {jar} status_code:{r.status_code}'
            with open(f'{self.repo}/jar/{name}', 'wb') as f:
                f.write(r.content)
            jar = f'{self.cnb_slot}/jar/{name}'
            text = text.replace(matches.group(2), jar)
        except Exception as e:
            print(f'【jar下载失败】{name} jar地址: {jar} error:{e}')
        return text
    async def download(self, url, name, filename, cang=True):
        file_list = []
        for root, dirs, files in os.walk(self.repo):
            for file in files:
                file_list.append(file)
        if filename in file_list:
            print(f'{filename}：已经存在，无需重复下载')
            return
        if 'agit.ai' in url:
            print(f'下载异常：agit.ai失效')
            return
        # 下载单线路
        item = {}
        try:
            path = os.path.dirname(url)
            r = self.s.get(url, headers=self.headers, allow_redirects=True, timeout=self.timeout, verify=False)
            if r.status_code == 200:
                print("开始下载【线路】{}: {}".format(name, url))
                if 'searchable' not in r.text:
                    r = self.js_render(url)
                    if not r.text:
                        r = self.picparse(url)
                        if 'searchable' not in r:
                            raise
                        r = self.get_jar(name, url, r)
                        with open(f'{self.repo}{self.sep}{filename}', 'w+', encoding='utf-8') as f:
                            f.write(r)
                            return
                if 'searchable' not in r.text:
                    raise
                with open(f'{self.repo}{self.sep}{filename}', 'w+', encoding='utf-8') as f:
                    try:
                        if r.content.decode('utf8').startswith(u'\ufeff'):
                            str = r.content.decode('utf8').encode('utf-8')[3:].decode('utf-8')
                        else:
                            str = r.content.decode('utf-8').replace('./', f'{path}/')
                    except:
                        str = r.text
                    finally:
                        r = self.ghproxy(str.replace('./', f'{path}/'))

                    r = self.get_jar(name, url, r)
                    f.write(r)
                    pipes.add(name)
                try:
                    if self.site_down:
                        await self.site_file_down([f'{self.repo}{self.sep}{filename}'], url)
                except Exception as e:
                    print(f'下载ext中的json失败: {e}')
        except Exception as e:
            print(f"【线路】{name}: {url} 下载错误：{e}")
        # 单仓时写入item
        if os.path.exists(f'{self.repo}{self.sep}{filename}') and cang:
            item['name'] = name
            item['url'] = f'{self.cnb_slot}/{filename}'
            items.append(item)
    async def down(self, data, s_name):
        '''
        下载单仓
        '''
        newJson = {}
        global items
        items = []
        urls = data.get("urls") if data.get("urls") else data.get("sites")
        for u in urls:
            name = u.get("name").strip()
            name = self.remove_emojis(name)
            url = u.get("url")
            url = self.ghproxy(url)
            filename = '{}.txt'.format(name)
            if name in pipes:
                print(f"【线路】{name} 已存在，无需重复下载")
                continue
            await self.download(url, name, filename)
        newJson['urls'] = items
        newJson = pprint.pformat(newJson, width=200)
        print(f'开始写入单仓{s_name}')
        with open(f'{self.repo}{self.sep}{s_name}', 'w+', encoding='utf-8') as f:
            content = str(newJson).replace("'", '"')
            f.write(json.loads(json.dumps(content, indent=4, ensure_ascii=False)))
    def all(self):
        # 整合所有文件到all.json
        newJson = {}
        items = []
        files = self.remove_duplicates(self.repo)
        for file in files:
            item = {}
            item['name'] = file.split('.txt')[0]
            item['url'] = f'{self.cnb_slot}/{file}'
            items.append(item)
        newJson['urls'] = items
        newJson = pprint.pformat(newJson, width=200)
        print(f'开始写入all.json')
        with open(f'{self.repo}{self.sep}all.json', 'w+', encoding='utf-8') as f:
            content = str(newJson).replace("'", '"')
            f.write(json.loads(json.dumps(content, indent=4, ensure_ascii=False)))
    async def batch_handle_online_interface(self):
        # 下载线路，处理多url场景
        print(f'--------- 开始私有化在线接口 ----------')
        urls = self.url.split(',')
        for url in urls:
            # 解析URL
            parsed_url = urlparse(url)
            # 获取查询参数
            query_params = parse_qs(parsed_url.query)
            # 提取'signame'参数的值
            signame_value = query_params.get('signame', [''])[0]
            item = url.split('?&signame=')
            self.url = item[0]
            self.signame = signame_value if signame_value else None
            print(f'当前url: {self.url}')
            await self.storeHouse()
        await self.clean_directories()

    async def clean_directories(self):
        # Step 1: 删除 api/drpy2 目录（如果 self.drpy2 为假）
        if not self.drpy2:
            drpy2_path = f"{self.repo}/api/drpy2"
            if os.path.exists(drpy2_path):
                await asyncio.to_thread(shutil.rmtree, drpy2_path)

        # Step 2: 检查并删除空的 api 和 ext 目录
        directories = [f"{self.repo}/api", f"{self.repo}/ext"]
        for dir_path in directories:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                if not os.listdir(dir_path):  # 目录为空
                    await asyncio.to_thread(shutil.rmtree, dir_path)
    def git_clone(self):
        self.domain = f'https://{self.gitusername}:{self.token}@{self.registry}/{self.username}/{self.repo}.git'
        if os.path.exists(self.repo):
            subprocess.call(['rm', '-rf', self.repo])
        try:
            print(f'开始克隆：git clone https://{self.registry}/{self.username}/{self.repo}.git')
            git.Repo.clone_from(self.domain, to_path=self.repo, depth=1)
        except Exception as e:
            print(222222, e)
    def get_local_repo(self):
        # 打开本地仓库，读取仓库信息
        repo = git.Repo(self.repo)
        config_writer = repo.config_writer()
        config_writer.set_value('user', 'name', self.username)
        config_writer.set_value('user', 'email', self.username)
        # 设置 http.postBuffer
        config_writer.set_value('http', 'postBuffer', '73400320')
        config_writer.release()
        # 获取远程仓库的引用
        remote = repo.remote(name='origin')
        # 获取远程分支列表
        remote_branches = remote.refs
        # 遍历远程分支，查找主分支
        for branch in remote_branches:
            if branch.name == 'origin/master' or branch.name == 'origin/main':
                self.branch = branch.name.split('/')[-1]
                break
        # print(f"仓库{self.repo} 主分支为: {self.main_branch}")
        return repo
    def reset_commit(self,repo):
        # 重置commit
        try:
            os.chdir(self.repo)
            # print('开始清理git',os.getcwd())
            repo.git.checkout('--orphan', 'tmp_branch')
            repo.git.add(A=True)
            repo.git.commit(m="update")
            repo.git.execute(['git', 'branch', '-D', self.branch])
            repo.git.execute(['git', 'branch', '-m', self.branch])
            repo.git.execute(['git', 'push', '-f', 'origin', self.branch])
        except Exception as e:
            print('git清理异常', e)
    def git_push(self, repo):
        # 推送并重置commit计数
        # 推送
        print(f'开始推送：git push https://{self.registry}/{self.username}/{self.repo}.git')
        try:
            repo.git.add(A=True)
            repo.git.commit(m="update")
            repo.git.push()
            self.reset_commit(repo)
        except Exception as e:
            try:
                repo.git.execute(['git', 'push', '--set-upstream', 'origin', self.branch])
                self.reset_commit(repo)
            except Exception as e:
                print('git推送异常', e)
    async def storeHouse(self):
        '''
        生成多仓json文件
        '''
        await self.download_drpy2_files()

        newJson = {}
        items = []

        # 解析最初链接
        try:
            res = self.s.get(self.url, headers=self.headers, verify=False, timeout=self.timeout).content.decode('utf8')
            if '404 Not Found' in res:
                print(f'{self.url} 请求异常')
                return
        except Exception as e:
            if 'Read timed out' in str(e) or 'nodename nor servname provided, or not known' in str(e):
                print(f'{self.url} 请求异常：{e}')
                return
            html = await self.js_render(self.url)
            res = html.text.replace(' ', '').replace("'", '"')
            if 'Read timed out' in str(e) or 'nodename nor servname provided, or not known' in str(e):
                print(f'{self.url} 请求异常：{e}')
                return
            if not res:
                res = self.picparse(self.url).replace(' ', '').replace("'", '"')

        # 线路
        if 'searchable' in str(res):
            filename = self.signame + '.txt' if self.signame else f"{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.txt"
            path = os.path.dirname(self.url)
            print("【线路】 {}: {}".format(self.repo, self.url))
            try:
                with open(f'{self.repo}{self.sep}{filename}', 'w+', encoding='utf-8') as f, open(
                        f'{self.repo}{self.sep}{self.target}', 'w+', encoding='utf-8') as f2:
                    r = self.ghproxy(res.replace('./', f'{path}/'))
                    r = self.get_jar(filename.split('.txt')[0], url, r)
                    # json容错处理
                    r = self.json_compatible(r)
                    f.write(r)
                    f2.write(r)
            except Exception as e:
                print(333333333, e)
            try:
                if self.site_down:
                    await self.site_file_down([f'{self.repo}{self.sep}{filename}',f'{self.repo}{self.sep}{self.target}'], self.url)
            except Exception as e:
                pass
            return

        # json容错处理
        res = self.json_compatible(res)
        # 移除注释
        datas = ''
        for d in res.splitlines():
            if d.find(" //") != -1 or d.find("// ") != -1 or d.find(",//") != -1 or d.startswith("//"):
                d = d.split(" //", maxsplit=1)[0]
                d = d.split("// ", maxsplit=1)[0]
                d = d.split(",//", maxsplit=1)[0]
                d = d.split("//", maxsplit=1)[0]
            datas = '\n'.join([datas, d])
        # 容错处理，便于json解析
        datas = datas.replace('\n', '')
        res = datas.replace(' ', '').replace("'", '"').replace('\n', '')
        if datas.startswith(u'\ufeff'):
            try:
                res = datas.encode('utf-8')[3:].decode('utf-8').replace(' ', '').replace("'", '"').replace('\n', '')
            except Exception as e:
                res = datas.encode('utf-8')[4:].decode('utf-8').replace(' ', '').replace("'", '"').replace('\n', '')

        # 多仓
        elif 'storeHouse' in datas:
            res = json.loads(str(res))
            srcs = res.get("storeHouse") if res.get("storeHouse") else None
            if srcs:
                i = 1
                for s in srcs:
                    if i > self.num:
                        break
                    i += 1
                    item = {}
                    s_name = s.get("sourceName")
                    s_name = self.remove_emojis(s_name)
                    s_name = f'{s_name}.json'
                    s_url = s.get("sourceUrl")
                    print("【多仓】 {}: {}".format(s_name, s_url))
                    try:
                        if self.s.get(s_url, headers=self.headers).status_code >= 400:
                            continue
                    except Exception as e:
                        print('地址无法响应: ',e)
                        continue
                    try:
                        if self.s.get(s_url, headers=self.headers).content.decode('utf8').lstrip().startswith(u'\ufeff'):
                            data = self.s.get(s_url, headers=self.headers).content.decode('utf-8')[1:]
                        else:
                            data = self.s.get(s_url, headers=self.headers).content.decode('utf-8')
                    except Exception as e:
                        try:
                            data = self.s.get(s_url, headers=self.headers).content.decode('utf8')
                            data = data.encode('utf-8').decode('utf-8')
                        except Exception as e:
                            continue
                    datas = ''
                    for d in data.splitlines():
                        if d.find(" //") != -1 or d.find("// ") != -1 or d.find(",//") != -1 or d.startswith("//"):
                            d = d.split(" //", maxsplit=1)[0]
                            d = d.split("// ", maxsplit=1)[0]
                            d = d.split(",//", maxsplit=1)[0]
                            d = d.split("//", maxsplit=1)[0]
                        datas = '\n'.join([datas, d])

                    try:
                        if datas.lstrip().startswith(u'\ufeff'):
                            datas = datas.encode('utf-8')[1:]
                        await self.down(json.loads(datas), s_name)
                    except Exception as e:
                        try:
                            data = self.s.get(s_url, headers=self.headers).text
                        except Exception as e:
                            continue
                        datas = ''
                        for d in data.splitlines():
                            datas += d.replace('\n', '').replace(' ', '').strip()
                        datas = datas.encode('utf-8')
                        if 'DOCTYPEhtml' in str(datas):
                            continue
                        datas = re.sub(r'^(.*?)\{', '{', datas.decode('utf-8'), flags=re.DOTALL | re.MULTILINE)
                        await self.down(json.loads(datas), s_name)
                    item['sourceName'] = s_name.split('.json')[0]
                    item['sourceUrl'] = f'{self.cnb_slot}/{s_name}'
                    items.append(item)
                newJson["storeHouse"] = items
                newJson = pprint.pformat(newJson, width=200)
                with open(f'{self.repo}{self.sep}{self.target}', 'w+', encoding='utf-8') as f:
                    print(f"开始写入{self.target}")
                    f.write(json.dumps(json.loads(str(newJson).replace("'", '"')), sort_keys=True, indent=4, ensure_ascii=False))
        # 单仓
        else:
            try:
                res = json.loads(str(res))
            except Exception as e:
                if 'domainnameisinvalid' in res:
                    print(f'该域名无效，请提供正常可用接口')
                    return
                html = await self.js_render(self.url)
                res = html.text.replace(' ', '').replace("'", '"')
                if not res:
                    res = self.picparse(self.url).replace(' ', '').replace("'", '"')
                try:
                    res = json.loads(str(res))
                except Exception as e:
                    # print(111111, e, res)
                    pass
            s_name = self.target
            s_url = self.url
            print("【单仓】 {}: {}".format(s_name, s_url))
            try:
                await self.down(res, s_name)
            except Exception as e:
                if 'searchable' in str(res):
                    filename = self.signame + '.txt' if self.signame else f"{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.txt"
                    print("【线路】 {}: {}".format(filename, self.url))
                    try:
                        await self.download(self.url, filename.split('.txt')[0], filename, cang=False)
                    except Exception as e:
                        print('下载异常', e)
    def replace_urls_gh1(self, content):
        # 适用于https://ghp.ci/https://raw.githubusercontent.com|https://raw.yzuu.cf类型
        # 使用正则表达式查找并替换链接
        def replace_match(match):
            username = match.group(2)
            repo_name = match.group(3)
            path = match.group(4)
            # 构建新的URL
            new_url = f"{self.mirror_proxy}/{username}/{repo_name}/{self.main_branch}"
            if path:
                new_url += path
            return new_url
        return self.pattern.sub(replace_match, content)
    def replace_urls_gh2(self, content):
        # 适用于https://gcore/jsdelivr.net/gh类型
        # 替换函数
        def replace_match(match):
            return f'{self.mirror_proxy}/{match.group(2)}/{match.group(3)}{match.group(5)}'
        # 执行替换
        return self.pattern.sub(replace_match, content)
    def mirror_proxy2new(self):
        # 把文本文件中所有镜像代理路径替换掉
        if self.mirror < 20:
            # gh1 适用于https://ghp.ci/https://raw.githubusercontent.com|https://raw.yzuu.cf类型
            # 自动转换提供的域名列表为正则表达式所需的格式
            patterns = [re.escape(proxy) for proxy in self.gh2]
            # 组合成一个正则表达式
            self.pattern = re.compile(r'({})/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(/.*)?'.format('|'.join(patterns)))
            # 遍历文件夹中的所有文件
            for root, dirs, files in os.walk(self.repo):
                for file in files:
                    if file.endswith('.txt') or file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # 替换文件中的URL
                        new_content = self.replace_urls_gh1(content)
                        for i in self.gh1:
                            new_content = new_content.replace(i,self.mirror_proxy)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
        elif self.mirror > 20:
            # gh2适用于https://gcore.jsdelivr.net/gh类型
            if self.jar_suffix not in ['html','js','css','json','txt']:
                return
            # 自动转换提供的域名列表为正则表达式所需的格式
            patterns = [re.escape(proxy) for proxy in self.gh1]
            # 组合成一个正则表达式
            self.pattern = re.compile(r'({})/(.+?)/(.+?)/(master|main)(/|/.*)'.format('|'.join(patterns)))
            # 遍历文件夹中的所有文件
            for filename in os.listdir(self.repo):
                file_path = os.path.join(self.repo, filename)
                # 检查是否是文件而不是文件夹
                if os.path.isfile(file_path) and (filename.endswith('.txt') or filename.endswith('.json')):
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        # 替换文件中的URL
                        new_content = self.replace_urls_gh2(content)
                        for i in self.gh2:
                            new_content = new_content.replace(i,self.mirror_proxy)
                        # 写回文件
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
    def mirror_init(self):
        # gh1
        if self.mirror == 1:
            self.mirror_proxy = 'https://ghp.ci/https://raw.githubusercontent.com'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 2:
            self.mirror_proxy = 'https://gh.xxooo.cf/https://raw.githubusercontent.com'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 3:
            self.mirror_proxy = 'https://ghproxy.net/https://raw.githubusercontent.com'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 4:
            self.mirror_proxy = 'https://github.moeyy.xyz/https://raw.githubusercontent.com'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 5:
            self.mirror_proxy = 'https://gh-proxy.com/https://raw.githubusercontent.com'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 6:
            self.mirror_proxy = 'https://ghproxy.cc/https://raw.githubusercontent.com'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 7:
            self.mirror_proxy = 'https://raw.yzuu.cf'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
            # self.registry = 'hub.yzuu.cf'
        elif self.mirror == 8:
            self.mirror_proxy = 'https://raw.nuaa.cf'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 9:
            self.mirror_proxy = 'https://raw.kkgithub.com'
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}/{self.main_branch}'
        elif self.mirror == 10:
            self.mirror_proxy = 'https://gh.con.sh/https://raw.githubusercontent.com'
        elif self.mirror == 11:
            self.mirror_proxy = 'https://gh.llkk.cc/https://raw.githubusercontent.com'
        elif self.mirror == 12:
            self.mirror_proxy = 'https://gh.ddlc.top/https://raw.githubusercontent.com'
        elif self.mirror == 13:
            self.mirror_proxy = 'https://gh-proxy.llyke.com/https://raw.githubusercontent.com'

        # gh2
        elif self.mirror == 21:
            self.mirror_proxy = "https://fastly.jsdelivr.net/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'
        elif self.mirror == 22:
            self.mirror_proxy = "https://jsd.onmicrosoft.cn/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'
        elif self.mirror == 23:
            self.mirror_proxy = "https://gcore.jsdelivr.net/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'
        elif self.mirror == 24:
            self.mirror_proxy = "https://cdn.jsdmirror.com/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'
        elif self.mirror == 25:
            self.mirror_proxy = "https://cdn.jsdmirror.cn/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'
        elif self.mirror == 26:
            self.mirror_proxy = "https://jsd.proxy.aks.moe/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'
        elif self.mirror == 27:
            self.mirror_proxy = "https://jsdelivr.b-cdn.net/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'
        elif self.mirror == 28:
            self.mirror_proxy = "https://jsdelivr.pai233.top/gh"
            self.slot = f'{self.mirror_proxy}/{self.username}/{self.repo}'

    def run(self):
        start_time = time.time()
        self.git_clone()
        asyncio.run(self.batch_handle_online_interface())
        repo = self.get_local_repo()
        self.all()
        self.mirror_proxy2new()
        self.git_push(repo)
        end_time = time.time()
        print(f'耗时: {end_time - start_time} 秒\n\n#################影视仓APP配置接口########################\n\n{self.cnb_slot}/all.json\n{self.cnb_slot}/{self.target}')


if __name__ == '__main__':
    token = 'xxx'
    username = 'fish2018'
    repo = 'test'
    # url = 'https://github.moeyy.xyz/https://raw.githubusercontent.com/wwb521/live/main/video.json?signame=18'
    # url = 'https://github.moeyy.xyz/https://raw.githubusercontent.com/supermeguo/BoxRes/main/Myuse/catcr.json?signame=v18'
    # url = 'http://box.ufuzi.com/tv/qq/%E7%9F%AD%E5%89%A7%E9%A2%91%E9%81%93/api.json?signame=duanju'
    # url = 'https://肥猫.com?signame=肥猫'
    url = 'https://tvbox.catvod.com/xs/api.json?signame=xs'
    site_down = True # 将site中的文件下载本地化
    GetSrc(username=username, token=token, url=url, repo=repo, mirror=4, num=10, site_down=site_down).run()
