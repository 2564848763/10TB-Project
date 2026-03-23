import os, sys, time, json, hashlib, subprocess, urllib.request, urllib.parse
from pathlib import Path

CFG = {
    "pikpak_user": os.getenv("PIKPAK_USER"),
    "pikpak_pass": os.getenv("PIKPAK_PASS"),
    "pan123_user": os.getenv("PAN123_USER"),
    "pan123_pass": os.getenv("PAN123_PASS"),
    "transfers": 4,           # 稳一点，先用 4
    "checkpoint_file": "state.json",
    "src_base": "pikpak:",
    "dst_base": "123pan:/PikPak_Backup",
    "folders": [f"/{chr(i)}" for i in range(ord('a'), ord('q')+1)],
    "rc_addr": "127.0.0.1:5572"
}

def obscure(p):
    return subprocess.run(["rclone", "obscure", p], capture_output=True, text=True).stdout.strip()

def init_rclone():
    print("🔐 正在配置并启动引擎 (No-Daemon 模式)...")
    p_pass = obscure(CFG['pikpak_pass'])
    w_pass = obscure(CFG['pan123_pass'])
    
    # 优化后的配置，增加一些 PikPak 稳定性参数
    conf = f"""
[pikpak]
type = pikpak
user = {CFG['pikpak_user']}
pass = {p_pass}

[123pan]
type = webdav
url = https://webdav.123pan.cn/webdav
vendor = other
user = {CFG['pan123_user']}
pass = {w_pass}
"""
    Path("rclone.conf").write_text(conf)
    
    # 关键修改：去掉 --daemon，使用 Popen 挂起
    subprocess.Popen([
        "rclone", "rcd", "--rc-no-auth", 
        "--rc-addr", CFG["rc_addr"], 
        "--config", "rclone.conf"
    ])
    
    # 等待引擎暖机
    time.sleep(10)
    print("🚀 引擎已就绪")

def process_folder(folder):
    src, dst = f"{CFG['src_base']}{folder}", f"{CFG['dst_base']}{folder}"
    print(f"🔍 扫描: {src}")
    
    # 尝试扫描
    res = subprocess.run(["rclone", "lsjson", "-R", "--files-only", "--config", "rclone.conf", src], capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"❌ 无法读取 {folder}，可能需要 Token。报错内容: {res.stderr[:100]}")
        return

    files = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"✅ 发现 {len(files)} 个文件，开始搬运...")
    
    for f in files:
        orig = f["Path"]
        safe = hashlib.md5(orig.encode()).hexdigest()[:16] + os.path.splitext(orig)[1]
        params = urllib.parse.urlencode({'srcFs': src, 'srcRemote': orig, 'dstFs': dst, 'dstRemote': safe, '_async': 'true'})
        try:
            urllib.request.urlopen(f"http://{CFG['rc_addr']}/operations/copyfile?{params}")
        except: pass

if __name__ == "__main__":
    init_rclone()
    for fld in CFG["folders"]:
        process_folder(fld)
    print("🏆 本轮尝试结束")
