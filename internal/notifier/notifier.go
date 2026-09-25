package notifier

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/smtp"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Severity of an alert.
type Severity string

const (
	SeverityWarning  Severity = "warning"
	SeverityCritical Severity = "critical"
	SeverityRecovery Severity = "recovery"
)

// Alert represents one notification event.
type Alert struct {
	Time    string   `json:"time"`
	Type    Severity `json:"type"`
	Title   string   `json:"title"`
	Message string   `json:"message"`
}

// Notifier manages sending alerts to various channels.
type Notifier struct {
	mu     sync.Mutex
	alerts []Alert
	max    int

	serverChanKey  string
	webhookURL     string
	notifyCooldown int // seconds

	// SMTP email channel (optional)
	smtpHost     string
	smtpPort     int
	smtpUser     string
	smtpPassword string
	smtpFrom     string
	smtpTo       []string // parsed recipients

	lastNotified map[string]int64 // key -> unix timestamp

	// dispatchCh bounds how many notification goroutines may run at once.
	// Without it a burst of alerts spawns one goroutine per alert and the
	// pile-up can exhaust file descriptors when a channel hangs.
	dispatchCh chan struct{}
	dropped    int // alerts dropped because the dispatch queue was full
}

// maxConcurrentDispatches is the notification fan-out limit.
const maxConcurrentDispatches = 16

// smtpTimeout bounds the whole SMTP conversation (dial + auth + DATA), so a
// stalled mail server cannot pin a goroutine forever.
const smtpTimeout = 20 * time.Second

// SMTPConfig holds email notification settings.
// All fields optional; email is disabled when Host is empty.
type SMTPConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	From     string
	To       string // comma-separated recipients
}

// NewNotifier creates a Notifier.
func NewNotifier(max int, serverChanKey, webhookURL string, notifyCooldown int, smtp SMTPConfig) *Notifier {
	var recipients []string
	if smtp.To != "" {
		for _, r := range strings.Split(smtp.To, ",") {
			r = strings.TrimSpace(r)
			if r != "" {
				recipients = append(recipients, r)
			}
		}
	}
	return &Notifier{
		alerts:         make([]Alert, 0, max),
		max:            max,
		serverChanKey:  serverChanKey,
		webhookURL:     webhookURL,
		notifyCooldown: notifyCooldown,
		smtpHost:       smtp.Host,
		smtpPort:       smtp.Port,
		smtpUser:       smtp.User,
		smtpPassword:   smtp.Password,
		smtpFrom:       smtp.From,
		smtpTo:         recipients,
		lastNotified:   make(map[string]int64),
		dispatchCh:     make(chan struct{}, maxConcurrentDispatches),
	}
}

// Get returns a copy of recent alerts.
func (n *Notifier) Get() []Alert {
	n.mu.Lock()
	defer n.mu.Unlock()
	out := make([]Alert, len(n.alerts))
	copy(out, n.alerts)
	return out
}

// Dropped reports how many alerts were discarded because the dispatch queue
// was saturated. A non-zero value means notification channels are too slow.
func (n *Notifier) Dropped() int {
	n.mu.Lock()
	defer n.mu.Unlock()
	return n.dropped
}

// Push adds a new alert and dispatches notifications.
func (n *Notifier) Push(a Alert) {
	n.mu.Lock()
	// Prepend
	n.alerts = append([]Alert{a}, n.alerts...)
	if len(n.alerts) > n.max {
		n.alerts = n.alerts[:n.max]
	}
	n.mu.Unlock()

	// Dispatch async, bounded by dispatchCh so a slow channel cannot cause
	// unbounded goroutine growth. When saturated the alert is still recorded
	// above and only the outbound push is skipped.
	select {
	case n.dispatchCh <- struct{}{}:
		go func() {
			defer func() { <-n.dispatchCh }()
			n.dispatch(a)
		}()
	default:
		n.mu.Lock()
		n.dropped++
		n.mu.Unlock()
	}
}

func (n *Notifier) dispatch(a Alert) {
	key := a.Title
	now := time.Now().Unix()

	n.mu.Lock()
	last, ok := n.lastNotified[key]
	if ok && now-last < int64(n.notifyCooldown) {
		n.mu.Unlock()
		return // in cooldown
	}
	n.lastNotified[key] = now
	n.pruneCooldownsLocked(now)
	n.mu.Unlock()

	if n.serverChanKey != "" {
		_ = n.sendServerChan(a)
	}
	if n.webhookURL != "" {
		_ = n.sendWebhook(a)
	}
	if n.smtpHost != "" && len(n.smtpTo) > 0 {
		_ = n.sendEmail(a)
	}
}

// pruneCooldownsLocked removes cooldown entries that can no longer suppress a
// notification, so lastNotified does not grow with every distinct alert title.
func (n *Notifier) pruneCooldownsLocked(now int64) {
	ttl := int64(n.notifyCooldown)
	if ttl < 60 {
		ttl = 60
	}
	for k, ts := range n.lastNotified {
		if now-ts > ttl {
			delete(n.lastNotified, k)
		}
	}
}

// sendServerChan sends via ServerChan (方糖) - pushes to WeChat.
func (n *Notifier) sendServerChan(a Alert) error {
	title := fmt.Sprintf("[SCP:SL Monitor] %s", a.Title)
	desp := fmt.Sprintf("**%s**\n\n%s\n\n时间: %s", a.Title, a.Message, a.Time)

	apiURL := fmt.Sprintf("https://sctapi.ftqq.com/%s.send", n.serverChanKey)
	form := url.Values{}
	form.Set("title", title)
	form.Set("desp", desp)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.PostForm(apiURL, form)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	return nil
}

// sendWebhook sends via Discord/Slack compatible webhook.
func (n *Notifier) sendWebhook(a Alert) error {
	color := 16761857 // yellow (warning)
	switch a.Type {
	case SeverityCritical:
		color = 16727838 // red
	case SeverityRecovery:
		color = 5399544 // green
	}

	payload := map[string]interface{}{
		"embeds": []map[string]interface{}{
			{
				"title":       a.Title,
				"description": a.Message,
				"color":       color,
				"footer": map[string]string{
					"text": a.Time,
				},
			},
		},
	}

	body, _ := json.Marshal(payload)
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Post(n.webhookURL, "application/json", bytes.NewReader(body))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	return nil
}

// sendEmail sends an alert via SMTP. Supports STARTTLS for port 587
// and implicit TLS for port 465.
func (n *Notifier) sendEmail(a Alert) error {
	if n.smtpHost == "" || len(n.smtpTo) == 0 {
		return nil
	}

	subject := fmt.Sprintf("[SCP:SL Monitor][%s] %s", strings.ToUpper(string(a.Type)), a.Title)
	body := fmt.Sprintf(
		"Server Health Monitor Alert\r\n"+
			"==========================\r\n"+
			"Severity: %s\r\n"+
			"Title:    %s\r\n"+
			"Time:     %s\r\n"+
			"\r\n%s\r\n",
		a.Type, a.Title, a.Time, a.Message,
	)

	msg := fmt.Sprintf(
		"From: %s\r\n"+
			"To: %s\r\n"+
			"Subject: %s\r\n"+
			"MIME-Version: 1.0\r\n"+
			"Content-Type: text/plain; charset=\"utf-8\"\r\n"+
			"\r\n%s",
		n.smtpFrom, strings.Join(n.smtpTo, ", "), subject, body,
	)

	// JoinHostPort keeps IPv6 literals correctly bracketed.
	addr := net.JoinHostPort(n.smtpHost, strconv.Itoa(n.smtpPort))
	dialer := &net.Dialer{Timeout: smtpTimeout}

	// Dial with a timeout: tls.Dial and smtp.SendMail have none, so a stalled
	// or blackholed mail server would block this goroutine indefinitely.
	var conn net.Conn
	var err error
	if n.smtpPort == 465 {
		// Port 465 = implicit TLS.
		conn, err = tls.DialWithDialer(dialer, "tcp", addr,
			&tls.Config{ServerName: n.smtpHost, MinVersion: tls.VersionTLS12})
	} else {
		// Port 587 = STARTTLS, 25 = plain (upgraded below when offered).
		conn, err = dialer.Dial("tcp", addr)
	}
	if err != nil {
		return err
	}
	defer conn.Close()
	// Bound the whole conversation (auth + DATA + QUIT).
	_ = conn.SetDeadline(time.Now().Add(smtpTimeout))

	client, err := smtp.NewClient(conn, n.smtpHost)
	if err != nil {
		return err
	}
	defer client.Close()

	if n.smtpPort != 465 {
		if ok, _ := client.Extension("STARTTLS"); ok {
			if err := client.StartTLS(&tls.Config{
				ServerName: n.smtpHost,
				MinVersion: tls.VersionTLS12,
			}); err != nil {
				return err
			}
		}
		// When STARTTLS is unavailable, smtp.PlainAuth itself refuses to send
		// credentials over an unencrypted link to a non-local host, so no
		// plaintext password can leak here.
	}
	return n.doSMTP(client, msg)
}

func (n *Notifier) doSMTP(client *smtp.Client, msg string) error {
	if err := client.Auth(smtp.PlainAuth("", n.smtpUser, n.smtpPassword, n.smtpHost)); err != nil {
		return err
	}
	if err := client.Mail(n.smtpFrom); err != nil {
		return err
	}
	for _, rcpt := range n.smtpTo {
		if err := client.Rcpt(rcpt); err != nil {
			return err
		}
	}
	w, err := client.Data()
	if err != nil {
		return err
	}
	if _, err := w.Write([]byte(msg)); err != nil {
		return err
	}
	if err := w.Close(); err != nil {
		return err
	}
	return client.Quit()
}
