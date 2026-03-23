import os, sys, time, json, hashlib, subprocess, urllib.request, urllib.parse
from pathlib import Path

# 配置中心
CFG = {
    "pikpak_user": os.getenv("PIKPAK_USER"),
    "pikpak_pass": os.getenv("PIKPAK_PASS"),
    "pan123_user": os.getenv("PAN123_USER"),
    "pan123_pass": os.getenv("PAN123_PASS"),
    "transfers": 10,
    "buffer_size": "64M",
    "checkpoint_file": "state.json",
    "src_base": "pikpak:",
    "dst_base": "123pan:/PikPak_Backup",
    "folders": [f'/{chr(i)}' for i in range(ord('a'), ord('q')+1)],
    "rc_addr": "localhost:5572"
}

# BBR & TCP 网络满血加速
def optimize_system():
    print("🛠️ 正在注入 BBR 算法与 TCP 窗口优化...")
    cmds = [
        "sudo sysctl -w net.core.default_qdisc=fq",
        "sudo sysctl -w net.ipv4.tcp_congestion_control=bbr",
        "sudo sysctl -w net.ipv4.tcp_fastopen=3",
        "sudo sysctl -w net.core.rmem_max=67108864",
        "sudo sysctl -w net.core.wmem_max=67108864",
        "sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 67108864'",
        "sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 67108864'"
    ]
    for c in cmds: subprocess.run(c, shell=True, capture_output=True)
    print("✅ 系统网络已进入满血模式")

class State:
    def __init__(self):
        self.stats = {"done": 0, "failed": 0}
        if Path(CFG["checkpoint_file"]).exists():
            try: self.stats.update(json.load(open(CFG["checkpoint_file"])))
            except: pass
    def save(self):
        with open(CFG["checkpoint_file"], "w") as f: json.dump(self.stats, f)

state = State()

def init_rclone():
    conf = f"[pikpak]\ntype = pikpak\nuser = {CFG['pikpak_user']}\npass = {CFG['pikpak_pass']}\n\n[123pan]\ntype = webdav\nurl = https://webdav.123pan.cn/webdav\nvendor = other\nuser = {CFG['pan123_user']}\npass = {CFG['pan123_pass']}\n"
    Path("rclone.conf").write_text(conf)
    subprocess.Popen(["rclone", "rcd", "--rc-no-auth", "--rc-addr", CFG["rc_addr"], "--config", "rclone.conf", "--transfers", str(CFG["transfers"]), "--daemon"])
    time.sleep(5)

def process_folder(folder):
    src, dst = f"{CFG['src_base']}{folder}", f"{CFG['dst_base']}{folder}"
    res = subprocess.run(["rclone", "lsjson", "-R", "--files-only", "--config", "rclone.conf", src], capture_output=True, text=True)
    files = json.loads(res.stdout) if res.returncode == 0 else []
    for f in files:
        orig = f["Path"]
        safe = hashlib.md5(orig.encode()).hexdigest()[:16] + os.path.splitext(orig)[1]
        params = urllib.parse.urlencode({'srcFs': src, 'srcRemote': orig, 'dstFs': dst, 'dstRemote': safe, '_async': 'true'})
        try:
            urllib.request.urlopen(f"http://{CFG['rc_addr']}/operations/copyfile?{params}")
            state.stats["done"] += 1
        except: state.stats["failed"] += 1
        if state.stats["done"] % 20 == 0:
            print(f"📊 进度：已完成 {state.stats['done']} | 失败 {state.stats['failed']}")
            state.save()

if __name__ == "__main__":
    optimize_system()
    init_rclone()
    for f in CFG["folders"]: process_folder(f)
    state.save()
