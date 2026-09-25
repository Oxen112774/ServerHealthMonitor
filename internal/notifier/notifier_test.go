package notifier

import "testing"

func TestPruneCooldownsDropsExpiredEntries(t *testing.T) {
	n := NewNotifier(10, "", "", 60, SMTPConfig{})
	n.lastNotified["stale"] = 1000
	n.lastNotified["fresh"] = 1150

	n.pruneCooldownsLocked(1200)

	if _, ok := n.lastNotified["stale"]; ok {
		t.Fatal("expired cooldown entry was not pruned")
	}
	if _, ok := n.lastNotified["fresh"]; !ok {
		t.Fatal("still-active cooldown entry was pruned")
	}
}

func TestPruneCooldownsHonoursMinimumTTL(t *testing.T) {
	// Cooldown 0 disables suppression entirely, but the map must still be
	// bounded rather than growing one entry per distinct alert title.
	n := NewNotifier(10, "", "", 0, SMTPConfig{})
	n.lastNotified["old"] = 1000
	n.lastNotified["recent"] = 1150

	n.pruneCooldownsLocked(1200)

	if _, ok := n.lastNotified["old"]; ok {
		t.Fatal("entry older than the minimum TTL was not pruned")
	}
	if _, ok := n.lastNotified["recent"]; !ok {
		t.Fatal("entry within the minimum TTL was pruned")
	}
}

func TestPushDropsWhenDispatchQueueSaturated(t *testing.T) {
	n := NewNotifier(10, "", "", 0, SMTPConfig{})
	// Occupy every dispatch slot so the next Push finds no capacity.
	for i := 0; i < maxConcurrentDispatches; i++ {
		n.dispatchCh <- struct{}{}
	}

	n.Push(Alert{Title: "saturated", Type: SeverityCritical})

	if got := n.Dropped(); got != 1 {
		t.Fatalf("expected 1 dropped alert, got %d", got)
	}
	// The alert must still be recorded for the dashboard even when the
	// outbound push is skipped.
	if alerts := n.Get(); len(alerts) != 1 || alerts[0].Title != "saturated" {
		t.Fatalf("alert was not recorded, got %+v", alerts)
	}
}