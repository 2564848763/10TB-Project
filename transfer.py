name: GDrive to 123Pan SA Transfer

on:
  workflow_dispatch:

jobs:
  transfer-data:
    runs-on: ubuntu-latest
    timeout-minutes: 350
    steps:
      - name: 开启 BBR 网络优化
        run: |
          sudo sysctl -w net.core.default_qdisc=fq
          sudo sysctl -w net.ipv4.tcp_congestion_control=bbr

      - name: 安装 Rclone
        run: curl https://rclone.org/install.sh | sudo bash

      - name: 载入配置文件 (Python 强稳版)
        env:
          CONF: ${{ secrets.RCLONE_CONF }}
        run: |
          mkdir -p ~/.config/rclone
          # 使用 Python 写入，确保 JSON 的复杂引号不被 Bash 转义破坏
          python3 -c "import os; open(os.path.expanduser('~/.config/rclone/rclone.conf'), 'w').write(os.environ['CONF'])"

      - name: 执行全量迁移
        run: |
          # gdrive: 后面不需要斜杠，它会自动访问你分享给机器人的文件夹
          rclone copy gdrive: 123pan:/abc \
            -v --stats=15s \
            --transfers=4 \
            --checkers=8 \
            --drive-acknowledge-abuse \
            --ignore-errors
