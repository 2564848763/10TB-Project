import os, time, json, hashlib, subprocess, urllib.request, urllib.parse
from pathlib import Path

CFG = {
    "pikpak_user": os.getenv("PIKPAK_USER"),
    "pikpak_pass": os.getenv("PIKPAK_PASS"),
    "pan123_user": os.getenv("PAN123_USER"),
    "pan123_pass": os.getenv("PAN123_PASS"),
    "folders": ["/"], # 直接全量扫描根目录
    "rc_addr": "127.0.0.1:5572"
}

def init_rclone():
    print("🚀 正在使用纯账号密码模式初始化引擎...")
    # 自动把明文密码加密给 Rclone 用
    p_pass = subprocess.run(["rclone", "obscure", CFG['pikpak_pass']], capture_output=True, text=True).stdout.strip()
    w_pass = subprocess.run(["rclone", "obscure", CFG['pan123_pass']], capture_output=True, text=True).stdout.strip()
    
    # 纯享版配置：没有任何 Token
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
    Path("rclone.conf").write_text(conf.strip())
    
    # 后台启动 Rclone API
    subprocess.Popen(["rclone", "rcd", "--rc-no-auth", "--rc-addr", CFG["rc_addr"], "--config", "rclone.conf"])
    time.sleep(10)

def run_transfer():
    src, dst = "pikpak:/", "123pan:/PikPak_Backup"
    print(f"🔍 开始全量扫描...")
    
    # 尝试读取 PikPak 文件列表
    res = subprocess.run(["rclone", "lsjson", "-R", "--files-only", "--config", "rclone.conf", src], capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"❌ 扫描失败！报错信息：{res.stderr[:200]}")
        return
        
    files = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"✅ 扫描成功！共发现 {len(files)} 个文件，开始搬运...")
    
    for f in files:
        orig = f["Path"]
        # 文件名变乱码，防止 123 云盘报错
        safe = hashlib.md5(orig.encode()).hexdigest()[:16] + os.path.splitext(orig)[1]
        params = urllib.parse.urlencode({'srcFs': src, 'srcRemote': orig, 'dstFs': dst, 'dstRemote': safe, '_async': 'true'})
        try:
            urllib.request.urlopen(f"http://{CFG['rc_addr']}/operations/copyfile?{params}")
        except:
            pass
            
    print("🏆 指令发送完毕，请等待后台对拉。")

if __name__ == "__main__":
    init_rclone()
    run_transfer()
