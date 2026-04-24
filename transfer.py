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
          python3 -c "import os; open(os.path.expanduser('~/.config/rclone/rclone.conf'), 'w').write(os.environ['CONF'])"

      - name: 执行全量迁移
        run: |
          # 注意：gdrive: 后面不要加斜杠，它会自动识别分享给机器人的根目录
          rclone copy gdrive: 123pan:/abc \
            -v --stats=15s \
            --transfers=4 \
            --checkers=8 \
            --drive-acknowledge-abuse \
            --ignore-errors
