from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException
from pyquery import PyQuery as pq
import time
import os
import requests
import subprocess
import aiohttp
import asyncio



# Chrome 可执行文件路径
chrome_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"  # Windows 示例路径
# 如果需要指定其他路径，请根据实际情况修改

# 命令行参数
chrome_args = [
    chrome_path,
    "--remote-debugging-port=9222",
]

# 启动 Chrome
try:
    process = subprocess.Popen(chrome_args)
    print("Chrome 已启动，远程调试端口为 9222")
except Exception as e:
    print(f"启动 Chrome 时出错: {e}")

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "localhost:9222") #此处端口保持和命令行启动的端口一致
driver = Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)
driver.maximize_window()

counter = 1


async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()  # 检查请求是否成功
            return await response.text()

async def download_mp3(url, save_path):
    """
    异步下载 MP3 文件
    :param url: MP3 文件的 URL
    :param save_path: 保存文件的路径
    """
    save_path = save_path + ".mp3"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # 检查请求是否成功
                with open(save_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(1024)  # 每次读取 1KB
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"文件已下载并保存到: {save_path}")
    except aiohttp.ClientError as e:
        print(f"下载失败: {e}")

async def download_multiple_mp3s(urls, save_dir):
    """
    异步下载多个 MP3 文件
    :param urls: MP3 文件的 URL 列表
    :param save_dir: 保存文件的目录
    """
    global counter
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  # 如果目录不存在，则创建

    tasks = []
    for url in urls:
        file_name = str(counter)
        counter += 1
        save_path = os.path.join(save_dir, file_name)
        tasks.append(download_mp3(url, save_path))

    await asyncio.gather(*tasks)  # 并发执行所有下载任务


def get_root_url():
    with open("url.txt", "r") as f:
        urls = [line.strip() for line in f.readlines()]  # 读取所有行并去除换行符
    return urls[0]

def load_page(url):
    driver.get(url)
    # 拉到底部，但是有新的加载就会退回到三分之二的位置；加载出来后又跳到四分之一的位置
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
    time.sleep(1)   # 等待一段时间，方便查看滚动的效果
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')  # 再继续滚动
    

def get_second_urls():
    html = driver.page_source
    doc = pq(html)
    items = doc('a.style_table-jump__3_9us.style_table-jump-analysis__2Zjop').items()
    audio_urls = []
    with open("second_url.txt", "w") as f:
        for item in items:
            audio_url = item.attr('href')
            if audio_url is not None:
                audio_urls.append(audio_url)
                f.write(audio_url + '\n')

    return audio_urls
async def get_audios(audio_urls):
    audio_urls = ["https://liuxue.koolearn.com" + url for url in audio_urls]
    # audio_urls = audio_urls[:2] 测试使用
    tasks = [fetch_html(url) for url in audio_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    final_results = []
    for url, result in zip(audio_urls, results):
        if isinstance(result, Exception):
            print(f"请求 {url} 失败: {result}")
        else:
            html = result
            doc = pq(html)
            items = doc('div.style_audio__3CZIP.style_audio__21IF7').items()
            for item in items:
                audio_url = item.find("audio").attr("src")
                final_results.append(audio_url)
    save_directory = "E:\XinDongFangToefl\mp3s"
    await download_multiple_mp3s(final_results, save_directory)

if __name__ == '__main__':
    try:
        url = get_root_url()
        load_page(url=url)
        audio_urls = get_second_urls()
        asyncio.run(get_audios(audio_urls))

    except:
        import traceback
        traceback.print_exc()
    finally:
        driver.close()
        time.sleep(5)
        os.system('taskkill /im chromedriver.exe /F')
        os.system('taskkill /im chrome.exe /F')

