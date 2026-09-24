#!/usr/bin/env python3
"""
Fast deployment script for SCP:SL Monitor Agent.
Uploads binary, configs, and restarts the service via SSH.

Uses paramiko for SSH/SCP (fast, reliable).

Usage:
    python deploy.py --host <server-address> --user root --key /path/to/key --binary build/server-health-monitor-agent
    python deploy.py --host <server-address> --user root --password xxx --binary build/server-health-monitor-agent

Environment variables also supported:
  DEPLOY_HOST, DEPLOY_PORT, DEPLOY_USER, DEPLOY_PASSWORD, DEPLOY_KEY
"""

import argparse
import os
import sys
import time
import base64
import shlex
import uuid

try:
    import paramiko
    from scp import SCPClient
except ImportError:
    print("[ERROR] 需要 paramiko 和 scp 库")
    print("        pip install paramiko scp")
    sys.exit(1)


# Files to deploy (local_path -> remote_path, mode)
DEPLOY_FILES = [
    # Binary
    ('binary', '/usr/local/sbin/server-health-monitor-agent', 0o755),
    # Config
    ('server-health-monitor-agent.conf.example', '/etc/server-health-monitor-agent.conf', 0o640),
    # systemd unit
    ('deploy/systemd/server-health-monitor-agent.service',
     '/etc/systemd/system/server-health-monitor-agent.service', 0o644),
]


def parse_args():
    p = argparse.ArgumentParser(description='SCP:SL Monitor - Fast Deploy')
    p.add_argument('--host', default=os.environ.get('DEPLOY_HOST', ''), help='Server hostname/IP')

    # 处理端口 空字符串回退22  修改
    port_raw = os.environ.get('DEPLOY_PORT')
    if port_raw and port_raw.strip():
        port_default = int(port_raw)
    else:
        port_default = 22
    p.add_argument('--port', type=int, default=port_default, help='SSH port')

    p.add_argument('--user', default=os.environ.get('DEPLOY_USER', 'root'), help='SSH username')
    p.add_argument('--password', default=os.environ.get('DEPLOY_PASSWORD', ''), help='SSH password')
    p.add_argument('--sudo-password', default=os.environ.get('DEPLOY_SUDO_PASSWORD', ''), help='sudo password (not persisted)')
    p.add_argument('--key', default=os.environ.get('DEPLOY_KEY', ''), help='SSH private key (path or base64 content)')
    p.add_argument('--binary', default='build/server-health-monitor-agent', help='Path to compiled binary')
    p.add_argument('--replace-legacy', action='store_true',
                   help='Stop and replace the legacy monitor-agent.service after backup')
    p.add_argument('--audit-only', action='store_true', help='Audit the server without uploading or changing it')
    action = p.add_mutually_exclusive_group()
    action.add_argument('--preflight', action='store_true', help='Run checks without changing the server')
    action.add_argument('--install', action='store_true', help='Install and restart the service')
    action.add_argument('--rollback', action='store_true', help='Restore the latest deployment backup')
    action.add_argument('--health-check', action='store_true', help='Check service health')
    return p.parse_args()


def connect(args):
    client = paramiko.SSHClient()
    # Production deployments must verify the target host against known_hosts.
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())

    connect_kwargs = {
        'hostname': args.host,
        'port': args.port,
        'username': args.user,
        'timeout': 30,
    }

    temp_key_path = None
    if args.key:
        # Try as file path first, then as base64 content
        if os.path.isfile(args.key):
            connect_kwargs['key_filename'] = args.key
        else:
            # Decode base64 key
            try:
                key_data = base64.b64decode(args.key).decode()
                key_path = os.path.join(os.getcwd(), '.deploy-key-' + uuid.uuid4().hex)
                temp_key_path = key_path
                with open(key_path, 'w', encoding='utf-8') as key_file:
                    key_file.write(key_data)
                os.chmod(key_path, 0o600)
                connect_kwargs['key_filename'] = key_path
            except Exception:
                # Treat as raw key content
                key_path = os.path.join(os.getcwd(), '.deploy-key-' + uuid.uuid4().hex)
                temp_key_path = key_path
                with open(key_path, 'w', encoding='utf-8') as key_file:
                    key_file.write(args.key)
                os.chmod(key_path, 0o600)
                connect_kwargs['key_filename'] = key_path
    elif args.password:
        connect_kwargs['password'] = args.password
    else:
        # Try default ssh key
        pass

    print(f"[+] 连接 {args.user}@{args.host}:{args.port} ...")
    try:
        client.connect(**connect_kwargs)
    finally:
        if temp_key_path:
            try:
                os.unlink(temp_key_path)
            except FileNotFoundError:
                pass
    print("[+] SSH 连接成功")
    return client


def exec_cmd(client, cmd, show_output=True, input_data=None):
    print(f"    $ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    if input_data is not None:
        stdin.write(input_data)
        stdin.flush()
        stdin.channel.shutdown_write()
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if show_output and out:
        for line in out.split('\n')[:10]:
            print(f"      {line}")
        if len(out.split('\n')) > 10:
            print(f"      ... ({len(out.split(chr(10)))} lines total)")
    if exit_code != 0 and err:
        print(f"    [stderr] {err[:200]}")
    return exit_code, out, err


def audit_remote(client):
    audit_cmd = r'''set -eu
printf '%s\n' '=== identity ==='
id
printf '%s\n' '=== matching services ==='
systemctl list-units --type=service --all --no-legend --no-pager | grep -Ei 'monitor|scpsl' || true
printf '%s\n' '=== listeners ==='
ss -ltnup 2>/dev/null | grep -E ':(8080|8081|9090|3000)\b' || true
printf '%s\n' '=== config (secrets redacted) ==='
    for file in /etc/server-health-monitor-agent.conf; do
    if [ -f "$file" ]; then
        echo "[$file]"
        sed -E 's#(auth_pass|serverchan_key|webhook_url|password|token|secret)([[:space:]]*=).*#\1\2[REDACTED]#Ig' "$file" | grep -Ev '^[[:space:]]*(#|$)' || true
    fi
done
printf '%s\n' '=== recent logs ==='
    journalctl -u monitor-agent.service -u server-health-monitor-agent.service -n 40 --no-pager -o short-iso 2>&1 || true
'''
    return exec_cmd(client, audit_cmd)


def remote_has_legacy_conflict(client):
    code, out, _ = exec_cmd(
        client,
        "if systemctl is-active --quiet monitor-agent.service; then exit 42; fi; "
        "if ss -ltn 2>/dev/null | grep -q ':8080 '; then exit 42; fi; exit 41",
        show_output=False,
    )
    return code == 42 or code == 0


def exec_privileged(client, cmd, sudo_password, needs_sudo):
    if not needs_sudo:
        return exec_cmd(client, cmd, show_output=False)
    if not sudo_password:
        raise RuntimeError("目标服务器需要 sudo，但未提供 sudo 密码")
    wrapped = "sudo -S -p '' sh -c " + shlex.quote(cmd)
    return exec_cmd(client, wrapped, show_output=False, input_data=sudo_password + "\n")


def upload_source(scp, local_path, remote_path, author_header):
    if not author_header or not local_path.lower().endswith(('.py', '.sh', '.service', '.timer', '.conf')):
        scp.put(local_path, remote_path)
        return
    with open(local_path, 'r', encoding='utf-8') as source:
        content = source.read()
    staged_path = os.path.join(os.getcwd(), '.deploy-source-' + uuid.uuid4().hex)
    with open(staged_path, 'w', encoding='utf-8') as staged:
        staged.write(author_header)
        staged.write(content)
    try:
        scp.put(staged_path, remote_path)
    finally:
        os.unlink(staged_path)


def deploy(args):
    client = connect(args)
    uid_code, uid_out, uid_err = exec_cmd(client, "id -u", show_output=False)
    if uid_code != 0:
        raise RuntimeError(f"无法确认远程用户权限: {uid_err[:200]}")
    needs_sudo = uid_out.strip() != "0"
    sudo_password = args.sudo_password or args.password

    print("\n[+] 部署前审计 ...")
    audit_remote(client)
    if args.audit_only:
        print("\n[OK] 仅审计完成，未上传或修改服务器")
        client.close()
        return

    if args.preflight:
        preflight_cmd = (
            "set -eu; "
            "command -v systemctl >/dev/null; "
            "command -v ss >/dev/null; "
            "test -d /run/systemd/system; "
            "test $(df -Pk /tmp | awk 'NR==2 {print $4}') -ge 131072; "
            "test $(getconf LONG_BIT) -ge 64"
        )
        code, _, err = exec_privileged(client, preflight_cmd, sudo_password, needs_sudo)
        if code != 0:
            client.close()
            raise RuntimeError("安装前检查失败: " + (err or "systemd、命令或磁盘空间不满足要求")[:200])
        if remote_has_legacy_conflict(client) and not args.replace_legacy:
            client.close()
            raise RuntimeError("检测到旧服务或 8080 端口冲突")
        client.close()
        print("[OK] 预检通过")
        return

    if args.health_check:
        code, out, err = exec_privileged(
            client, "systemctl is-active server-health-monitor-agent.service",
            sudo_password, needs_sudo)
        client.close()
        if code != 0 or out.strip() != 'active':
            raise RuntimeError("服务健康检查失败: " + (out or err)[:200])
        print("[OK] 服务健康")
        return

    if args.rollback:
        rollback_cmd = (
            "set -eu; "
            "found=0; for f in /usr/local/sbin/server-health-monitor-agent "
            "/etc/server-health-monitor-agent.conf "
            "/etc/systemd/system/server-health-monitor-agent.service; do "
            "latest=$(ls -1t \"$f\".bak.* 2>/dev/null | head -n 1 || true); "
            "if [ -n \"$latest\" ]; then cp -a \"$latest\" \"$f\"; found=1; fi; done; "
            "if [ \"$found\" -eq 0 ]; then echo '没有可用备份' >&2; exit 1; fi; "
            "systemctl daemon-reload; systemctl restart server-health-monitor-agent.service"
        )
        code, _, err = exec_privileged(client, rollback_cmd, sudo_password, needs_sudo)
        client.close()
        if code != 0:
            raise RuntimeError("回滚失败: " + err[:200])
        print("[OK] 已回滚上一版本")
        return

    if remote_has_legacy_conflict(client) and not args.replace_legacy:
        client.close()
        raise RuntimeError(
            "检测到 monitor-agent.service 或 8080 端口正在使用。"
            "如确认要切换到 Go Agent，请显式使用 --replace-legacy。"
        )

    # 1. Upload files
    print("\n[+] 上传文件 ...")
    code, _, err = exec_privileged(
        client,
        "mkdir -p /var/lib/server-health-monitor && chmod 0750 /var/lib/server-health-monitor",
        sudo_password,
        needs_sudo,
    )
    if code != 0:
        raise RuntimeError(f"创建部署临时目录失败: {err[:200]}")
    author_header = (
        "# Copyright (c) 2026 寒碑墓人 <3775864508@qq.com>\n"
        "# Deployment copy; licensed under the MIT License.\n\n"
    )
    with SCPClient(client.get_transport(), socket_timeout=30) as scp:
        for local_name, remote_path, mode in DEPLOY_FILES:
            local_path = local_name
            if local_name == 'binary':
                local_path = args.binary

            if not os.path.isfile(local_path):
                raise RuntimeError(f"安装必需文件不存在: {local_path}")

            # Upload to temp first, then move (to avoid partial files)
            # SCP runs as the SSH user; use a private temporary path before sudo moves it.
            temp_path = f"/tmp/server-health-monitor-deploy-{os.getpid()}-{os.path.basename(remote_path)}"
            print(f"    {local_path} -> {remote_path}")
            upload_source(scp, local_path, temp_path, author_header)
            # Move to final location with proper permissions
            quoted_temp = shlex.quote(temp_path)
            quoted_remote = shlex.quote(remote_path)
            command = (
                f"if [ -e {quoted_remote} ]; then backup={quoted_remote}.bak.$(date +%Y%m%d%H%M%S); "
                f"cp -a {quoted_remote} \"$backup\"; fi; "
                f"mv {quoted_temp} {quoted_remote} && chmod {oct(mode)[2:]} {quoted_remote}"
            )
            code, _, err = exec_privileged(client, command, sudo_password, needs_sudo)
            if code != 0:
                raise RuntimeError(f"安装 {remote_path} 失败: {err[:200]}")

    # 2. Create state dir
    print("\n[+] 设置目录和权限 ...")
    code, _, err = exec_privileged(
        client,
        "mkdir -p /var/lib/server-health-monitor && chmod 0750 /var/lib/server-health-monitor",
        sudo_password,
        needs_sudo,
    )
    if code != 0:
        raise RuntimeError(f"创建状态目录失败: {err[:200]}")

    # 3. Reload systemd
    print("\n[+] 重新加载 systemd ...")
    code, _, err = exec_privileged(client, "systemctl daemon-reload", sudo_password, needs_sudo)
    if code != 0:
        raise RuntimeError(f"重新加载 systemd 失败: {err[:200]}")

    # 4. Enable and restart services
    print("\n[+] 启用并重启服务 ...")
    if args.replace_legacy:
        code, _, err = exec_privileged(client, "systemctl disable --now monitor-agent.service", sudo_password, needs_sudo)
        if code != 0:
            raise RuntimeError(f"停止旧服务失败: {err[:200]}")
    code, _, err = exec_privileged(
        client,
        "systemctl enable --now server-health-monitor-agent.service",
        sudo_password,
        needs_sudo,
    )
    if code != 0:
        raise RuntimeError(f"启用服务失败: {err[:200]}")
    code, _, err = exec_privileged(client, "systemctl restart server-health-monitor-agent.service", sudo_password, needs_sudo)
    if code != 0:
        raise RuntimeError(f"重启服务失败: {err[:200]}")

    # 5. Verify
    print("\n[+] 验证服务状态 ...")
    time.sleep(2)
    exit_code, out, _ = exec_privileged(
        client,
        "systemctl is-active server-health-monitor-agent.service",
        sudo_password,
        needs_sudo,
    )
    if exit_code == 0 and out.strip() == 'active':
        print("    [OK] server-health-monitor-agent 运行中")
    else:
        raise RuntimeError(f"服务健康检查失败: {(out or '状态命令失败').strip()[:200]}")

    # Check port
    exit_code, out, _ = exec_cmd(client, "ss -tlnp | grep :8080 || true")
    if ':8080' in out:
        print("    [OK] 8080 端口已监听")
    else:
        print("    [WARN] 8080 端口未监听")

    print("\n" + "=" * 50)
    print("  部署完成！")
    print("  面板地址: http://{}:8080/".format(args.host))
    print("  Prometheus: http://{}:8080/metrics".format(args.host))
    print("=" * 50)

    client.close()


def main():
    args = parse_args()
    if not args.host:
        print("[ERROR] 请指定服务器地址 (--host 或 DEPLOY_HOST)")
        sys.exit(1)

    try:
        deploy(args)
    except Exception as e:
        print(f"\n[ERROR] 部署失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
