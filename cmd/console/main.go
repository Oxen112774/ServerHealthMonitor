package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/Oxen112774/ServerHealthMonitor/internal/console/audit"
	"github.com/Oxen112774/ServerHealthMonitor/internal/console/auth"
	"github.com/Oxen112774/ServerHealthMonitor/internal/console/servers"
	"github.com/Oxen112774/ServerHealthMonitor/internal/console/tickets"
	consoweb "github.com/Oxen112774/ServerHealthMonitor/internal/console/web"
)

var (
	version   = "dev"
	buildDate = "unknown"
)

func main() {
	fmt.Printf("Server Health Monitor Console v%s (built %s)\n", version, buildDate)
	fmt.Println("========================================================")

	// CLI flags
	host := flag.String("host", "127.0.0.1", "Listen address")
	port := flag.Int("port", 8081, "Listen port")
	dataDir := flag.String("data", "./console-data", "Data directory")
	adminUser := flag.String("admin-user", "", "Create admin user on first run (username)")
	adminPass := flag.String("admin-pass", "", "Admin user password (prefer CONSOLE_ADMIN_PASS env var)")
	unlockUser := flag.String("unlock-user", "", "Unlock a permanently locked account (CLI fallback)")
	resetUserPass := flag.String("reset-user-password", "", "Reset a user's password (forces password change on next login, use with --new-pass)")
	newPass := flag.String("new-pass", "", "New password for --reset-user-password (prefer CONSOLE_NEW_PASS env var)")
	rotateUserKey := flag.String("rotate-user-key", "", "Rotate a user's API key and print the new one (shown only once)")
	frameAncestor := flag.String("frame-ancestor", "", "Comma-separated origins allowed to embed console pages in a frame (default: framing denied)")
	flag.Parse()

	// Passwords are read from environment variables when the flags are absent.
	// argv is visible to other local processes (tasklist/ps), env vars are not
	// exposed the same way, so env is the recommended channel.
	resolvedAdminUser := *adminUser
	resolvedAdminPass := *adminPass
	resolvedNewPass := *newPass
	if resolvedAdminUser == "" {
		resolvedAdminUser = os.Getenv("CONSOLE_ADMIN_USER")
	}
	if resolvedAdminPass == "" {
		resolvedAdminPass = os.Getenv("CONSOLE_ADMIN_PASS")
	}
	if resolvedNewPass == "" {
		resolvedNewPass = os.Getenv("CONSOLE_NEW_PASS")
	}
	if *adminPass != "" || *newPass != "" {
		fmt.Println("⚠️  警告：检测到通过命令行传递密码，本机其他进程可读取进程列表。")
		fmt.Println("   建议改用 CONSOLE_ADMIN_PASS / CONSOLE_NEW_PASS 环境变量传入。")
	}

	// Ensure data directory
	absDataDir, _ := filepath.Abs(*dataDir)
	os.MkdirAll(absDataDir, 0750)
	fmt.Printf("数据目录: %s\n", absDataDir)

	// Initialize components
	authMgr := auth.NewAuthManager(absDataDir)
	authMgr.Load()
	serverMgr := servers.NewManager(absDataDir)
	auditLog := audit.NewLogger(absDataDir)
	ticketStore := tickets.NewStore(absDataDir)

	// Create default admin if requested
	if resolvedAdminUser != "" && resolvedAdminPass != "" {
		apiKey, err := authMgr.CreateUser(resolvedAdminUser, resolvedAdminPass, auth.RoleOwner)
		if err != nil {
			fmt.Printf("创建管理员失败: %v\n", err)
		} else {
			fmt.Println("")
			fmt.Println("========== 管理员账户已创建 ==========")
			fmt.Printf("  用户名:    %s\n", resolvedAdminUser)
			fmt.Println("  密码:      已设置（为防止凭据进入日志，不显示明文密码）")
			fmt.Printf("  API 密钥:  %s\n", apiKey)
			fmt.Println("  ⚠️  请妥善保存 API 密钥，只显示这一次！")
			fmt.Println("======================================")
			fmt.Println("")
		}
	}

	// CLI fallback operations for locked accounts / lost API keys (no web access required)
	if *unlockUser != "" {
		if err := authMgr.UnlockUser(*unlockUser, "CLI 解锁"); err != nil {
			fmt.Printf("解锁失败: %v\n", err)
		} else {
			fmt.Printf("✅ 已解锁用户: %s\n", *unlockUser)
		}
		fmt.Println("")
	}
	if *resetUserPass != "" {
		if resolvedNewPass == "" {
			fmt.Println("--reset-user-password 需要配合 --new-pass 或 CONSOLE_NEW_PASS 环境变量")
			os.Exit(1)
		}
		if err := authMgr.ChangePassword(*resetUserPass, resolvedNewPass); err != nil {
			fmt.Printf("重置密码失败: %v\n", err)
		} else {
			fmt.Printf("✅ 已重置用户 %s 的密码（下次登录将强制修改密码）\n", *resetUserPass)
		}
		fmt.Println("")
	}
	if *rotateUserKey != "" {
		key, err := authMgr.RotateAPIKey(*rotateUserKey)
		if err != nil {
			fmt.Printf("轮换密钥失败: %v\n", err)
		} else {
			fmt.Println("")
			fmt.Printf("🔑 用户 %s 新 API 密钥: %s\n", *rotateUserKey, key)
			fmt.Println("  ⚠️  只显示这一次，请妥善保存！")
			fmt.Println("")
		}
	}

	// Check if any users exist
	users := authMgr.ListUsers()
	if len(users) == 0 {
		fmt.Println("")
		fmt.Println("⚠️  警告：尚未创建任何用户！")
		fmt.Println("请使用以下方式创建管理员账户（推荐环境变量，避免凭据进入进程列表）：")
		fmt.Println("  CONSOLE_ADMIN_USER=用户名 CONSOLE_ADMIN_PASS=密码 server-health-monitor-console")
		fmt.Println("  （或）server-health-monitor-console --admin-user 用户名 --admin-pass 密码")
		fmt.Println("")
	}

	// Optionally allow specific origins (e.g. the desktop shell on another
	// localhost port) to embed console pages in a frame.
	if allowed := consoweb.SetFrameAncestors(strings.Split(*frameAncestor, ",")); len(allowed) > 0 {
		fmt.Printf("   允许内嵌来源: %s\n", strings.Join(allowed, ", "))
	}

	// HTTP handler
	h := consoweb.NewHandler(authMgr, serverMgr, auditLog, absDataDir, ticketStore)

	mux := http.NewServeMux()
	h.Register(mux)

	addr := fmt.Sprintf("%s:%d", *host, *port)
	srv := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	fmt.Println("")
	fmt.Printf("🚀 管理控制台启动中...\n")
	fmt.Printf("   地址: http://%s/console/\n", addr)
	fmt.Printf("   登录页: http://%s/console/login\n", addr)
	fmt.Println("")
	fmt.Println("按 Ctrl+C 停止")
	fmt.Println("")

	log.Printf("HTTP server listening on %s", addr)
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("HTTP server error: %v", err)
	}
}
