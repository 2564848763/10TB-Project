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

      - name: 载入配置文件 (Base64 解包)
        env:
          RCLONE_CONF_BASE64: ${{ secrets.RCLONE_CONF }}
        run: |
          mkdir -p ~/.config/rclone
          # 将打包后的乱码还原为真实的配置文件
          echo "$RCLONE_CONF_BASE64" | base64 -d > ~/.config/rclone/rclone.conf

      - name: 执行全量迁移
        run: |
          rclone copy gdrive:/ 123pan:/ \
            -v --stats=15s \
            --transfers=8 \
            --checkers=16 \
            --buffer-size=128M \
            --drive-chunk-size=128M \
            --ignore-errors
