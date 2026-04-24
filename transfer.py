name: GDrive to 123Pan Full Transfer

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

      - name: 载入配置文件
        env:
          CONF: ${{ secrets.RCLONE_CONF }}
        run: |
          mkdir -p ~/.config/rclone
          # 使用 printf 避免 echo 可能带来的换行转义问题
          printf "%s" "$CONF" > ~/.config/rclone/rclone.conf

      - name: 执行全量迁移
        run: |
          # 加上 --drive-acknowledge-abuse 绕过谷歌对大文件的安全扫描警告
          rclone copy gdrive:/ 123pan:/ \
            -v --stats=15s \
            --transfers=4 \
            --checkers=8 \
            --drive-acknowledge-abuse \
            --ignore-errors
