import os, sys, time, json, hashlib, subprocess, urllib.request, urllib.parse
from pathlib import Path

# ==================== ⚙️ 核心配置 ====================
CFG = {
    "pikpak_user": os.getenv("PIKPAK_USER"),
    "pikpak_pass": os.getenv("PIKPAK_PASS"),
    "pan123_user": os.getenv("PAN123_USER"),
    "pan123_pass": os.getenv("PAN123_PASS"),
    "transfers": 5,           # 建议先调低到 5，稳一点
    "buffer_size": "32M",
    "checkpoint_file": "state.json",
    "src_base": "pikpak:",
    "dst_base": "123pan:/PikPak_Backup",
    # 强制加上斜杠，确保路径匹配
    "folders": [f"/{chr(i)}" for i in range(ord('a'), ord('q')+1)], 
    "rc_addr": "localhost:5572"
}

# 自动加密密码的函数
def obscure_password(password):
    if not password: return ""
    res = subprocess.run(["rclone", "obscure", password], capture_output=True, text=True)
    return res.stdout.strip()

def optimize_system():
    print("🛠️ 正在注入 BBR 算法与 TCP 窗口优化...")
    cmds = [
        "sudo sysctl -w net.core.default_qdisc=fq",
        "sudo sysctl -w net.ipv4.tcp_congestion_control=bbr",
        "sudo sysctl -w net.ipv4.tcp_fastopen=3"
    ]
    for c in cmds: subprocess.run(c, shell=True, capture_output=True)

def init_rclone():
    print("🔐 正在加密配置并启动引擎...")
    # 关键：PikPak 和 123 的密码都需要加密，否则 Rclone 容易罢工
    p_pass = obscure_password(CFG['pikpak_pass'])
    w_pass = obscure_password(CFG['pan123_pass'])
    
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
    subprocess.Popen([
        "rclone", "rcd", "--rc-no-auth", "--rc-addr", CFG["rc_addr"], 
        "--config", "rclone.conf", "--daemon"
    ])
    time.sleep(5)
    return True

def process_folder(folder):
    # 确保源路径不带多余的斜杠
    src = f"{CFG['src_base']}{folder}"
    dst = f"{CFG['dst_base']}{folder}"
    print(f"[{time.strftime('%H:%M:%S')}] 🔍 正在深度扫描: {src}")
    
    # 运行扫描
    res = subprocess.run([
        "rclone", "lsjson", "-R", "--files-only", 
        "--config", "rclone.conf", src
    ], capture_output=True, text=True)
    
    # 如果报错了，打印出错误原因
    if res.returncode != 0:
        print(f"❌ 扫描失败 {folder}: {res.stderr.strip()}")
        return

    files = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"✅ 发现 {len(files)} 个文件")
    
    for f in files:
        orig = f["Path"]
        safe = hashlib.md5(orig.encode()).hexdigest()[:16] + os.path.splitext(orig)[1]
        params = urllib.parse.urlencode({'srcFs': src, 'srcRemote': orig, 'dstFs': dst, 'dstRemote': safe, '_async': 'true'})
        try:
            urllib.request.urlopen(f"http://{CFG['rc_addr']}/operations/copyfile?{params}")
        except: pass

if __name__ == "__main__":
    optimize_system()
    if init_rclone():
        for fld in CFG["folders"]:
            process_folder(fld)
    print("🏆 任务结束，请检查 123 云盘")
