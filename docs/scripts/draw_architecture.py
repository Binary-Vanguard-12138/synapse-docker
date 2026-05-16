#!/usr/bin/env python3
"""Generate docs/screenshots/architecture.png — the stack architecture diagram."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = "/root/synapse-docker/docs/screenshots/architecture.png"

# ── colour palette ────────────────────────────────────────────────────────────
C_INTERNET  = "#4A90D9"   # blue
C_EDGE      = "#2C7BB6"   # dark blue  (Nginx / coturn)
C_AUTH      = "#7B4F9E"   # purple     (Keycloak / MAS)
C_MATRIX    = "#1A936F"   # green      (Synapse / LiveKit)
C_NOTIF     = "#E08030"   # orange     (ntfy)
C_DB        = "#5C6370"   # slate      (PostgreSQL)
C_ARROW     = "#888888"
C_BG        = "#F7F8FA"
WHITE       = "#FFFFFF"
DARK        = "#1E1E2E"

FIG_W, FIG_H = 16, 10

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_aspect("equal")
ax.axis("off")
fig.patch.set_facecolor(C_BG)
ax.set_facecolor(C_BG)


# ── helpers ───────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, color, label, sublabel=None, fontsize=9, radius=0.25):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=1.2, edgecolor=color, facecolor=color + "22",
    )
    ax.add_patch(rect)
    # header bar
    header = FancyBboxPatch(
        (x, y + h - 0.42), w, 0.42,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=0, edgecolor=color, facecolor=color,
        clip_on=True,
    )
    ax.add_patch(header)
    ax.text(x + w / 2, y + h - 0.21, label,
            ha="center", va="center", fontsize=fontsize,
            fontweight="bold", color=WHITE, zorder=5)
    if sublabel:
        ax.text(x + w / 2, y + h / 2 - 0.1, sublabel,
                ha="center", va="center", fontsize=7.5,
                color=color, zorder=5, style="italic")


def arrow(ax, x0, y0, x1, y1, color=C_ARROW, label=None, label_side="top",
          bidirectional=False):
    style = "Simple,tail_width=1.2,head_width=7,head_length=6"
    arr = FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle=style,
        color=color, zorder=3,
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(arr)
    if bidirectional:
        arr2 = FancyArrowPatch(
            (x1, y1), (x0, y0),
            arrowstyle=style,
            color=color, zorder=3,
            connectionstyle="arc3,rad=0.0",
        )
        ax.add_patch(arr2)
    if label:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dy = 0.18 if label_side == "top" else -0.22
        ax.text(mx, my + dy, label, ha="center", va="center",
                fontsize=6.5, color="#555555", zorder=6)


def port_label(ax, x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=6.8,
            color="#FFFFFF", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.18", facecolor=C_EDGE,
                      edgecolor="none", alpha=0.88),
            zorder=7)


# ── Internet cloud ────────────────────────────────────────────────────────────
cloud_x, cloud_y, cloud_w, cloud_h = 0.4, 3.8, 2.0, 2.4
cloud_rect = FancyBboxPatch(
    (cloud_x, cloud_y), cloud_w, cloud_h,
    boxstyle="round,pad=0.15,rounding_size=0.5",
    linewidth=1.5, edgecolor=C_INTERNET, facecolor=C_INTERNET + "18",
)
ax.add_patch(cloud_rect)
ax.text(cloud_x + cloud_w / 2, cloud_y + cloud_h - 0.35,
        "Internet", ha="center", va="center",
        fontsize=10, fontweight="bold", color=C_INTERNET)
ax.text(cloud_x + cloud_w / 2, cloud_y + cloud_h / 2 - 0.15,
        "Clients\n(Element X, browsers,\nAndroid apps)",
        ha="center", va="center", fontsize=7.5, color=C_INTERNET)

# ── Nginx ─────────────────────────────────────────────────────────────────────
nx, ny, nw, nh = 3.6, 3.8, 2.0, 2.4
box(ax, nx, ny, nw, nh, C_EDGE, "Nginx", "HTTPS reverse proxy\n:80 · :443 · :2586", fontsize=9)

# Internet → Nginx arrow
arrow(ax, cloud_x + cloud_w, cloud_y + cloud_h / 2,
      nx, ny + nh / 2, color=C_EDGE)

# ── Port callouts on the Nginx box left edge ──────────────────────────────────
port_label(ax, nx - 0.32, ny + nh * 0.75, ":80")
port_label(ax, nx - 0.36, ny + nh * 0.50, ":443")
port_label(ax, nx - 0.40, ny + nh * 0.25, ":2586")

# ── Synapse ───────────────────────────────────────────────────────────────────
sx, sy, sw, sh = 6.6, 7.2, 2.2, 1.5
box(ax, sx, sy, sw, sh, C_MATRIX, "Synapse", ":8008 / :8448", fontsize=9)
arrow(ax, nx + nw, ny + nh * 0.80, sx, sy + sh / 2, color=C_MATRIX, label=":8008")

# ── MAS ───────────────────────────────────────────────────────────────────────
mx2, my2, mw, mh = 6.6, 5.4, 2.2, 1.5
box(ax, mx2, my2, mw, mh, C_AUTH, "MAS", "Matrix Auth Service\n:8080", fontsize=9)
arrow(ax, nx + nw, ny + nh * 0.55, mx2, my2 + mh / 2, color=C_AUTH, label="/oauth2, /login …")

# ── Keycloak ──────────────────────────────────────────────────────────────────
kx, ky, kw, kh = 6.6, 3.6, 2.2, 1.5
box(ax, kx, ky, kw, kh, C_AUTH, "Keycloak", "Identity provider\n:8080", fontsize=9)
arrow(ax, nx + nw, ny + nh * 0.30, kx, ky + kh / 2, color=C_AUTH, label="auth.<domain>")

# ── LiveKit + lk-jwt ──────────────────────────────────────────────────────────
lx, ly, lw, lh = 6.6, 1.9, 2.2, 1.4
box(ax, lx, ly, lw, lh, C_MATRIX, "LiveKit SFU", "WebRTC media\n:7880 ws / :7881 tcp", fontsize=8.5)
arrow(ax, nx + nw, ny + nh * 0.10, lx, ly + lh / 2, color=C_MATRIX, label="/livekit/")

jx, jy, jw, jh = 9.6, 2.1, 2.0, 1.0
box(ax, jx, jy, jw, jh, C_MATRIX, "lk-jwt", ":8080", fontsize=9)
arrow(ax, nx + nw, ny + nh * 0.05, jx, jy + jh / 2, color=C_MATRIX,
      label="/livekit/jwt", label_side="top")
# LiveKit ↔ lk-jwt
arrow(ax, jx, jy + jh / 2, lx + lw, ly + lh * 0.6,
      color=C_MATRIX, bidirectional=False)

# ── ntfy ─────────────────────────────────────────────────────────────────────
ox, oy, ow, oh = 6.6, 0.5, 2.2, 1.1
box(ax, ox, oy, ow, oh, C_NOTIF, "ntfy", "UnifiedPush · :80", fontsize=9)
arrow(ax, nx + nw, ny - 0.2, ox, oy + oh / 2, color=C_NOTIF, label=":2586")

# ── coturn ────────────────────────────────────────────────────────────────────
cx2, cy2, cw, ch = 3.6, 0.5, 2.0, 1.5
box(ax, cx2, cy2, cw, ch, C_EDGE, "coturn", "TURN/STUN\n:3478 / :5349 TLS\nudp 49152–49200", fontsize=8)
# Internet → coturn direct
arrow(ax, cloud_x + cloud_w / 2, cloud_y,
      cx2 + cw / 2, cy2 + ch,
      color=C_EDGE, label=":3478/:5349")

# ── PostgreSQL ────────────────────────────────────────────────────────────────
dbx, dby, dbw, dbh = 10.0, 5.2, 3.6, 2.2
box(ax, dbx, dby, dbw, dbh, C_DB, "PostgreSQL 16",
    "synapse db  ·  mas db  ·  keycloak db", fontsize=9)

# Synapse → DB
arrow(ax, sx + sw, sy + sh / 2,
      dbx, dby + dbh * 0.80,
      color=C_DB, bidirectional=True)
# MAS → DB
arrow(ax, mx2 + mw, my2 + mh / 2,
      dbx, dby + dbh * 0.50,
      color=C_DB, bidirectional=True)
# Keycloak → DB
arrow(ax, kx + kw, ky + kh / 2,
      dbx, dby + dbh * 0.20,
      color=C_DB, bidirectional=True)

# ── Internal service arrows ───────────────────────────────────────────────────
# MAS ↔ Keycloak  (upstream IdP)
arrow(ax, mx2 + mw / 2, my2,
      kx + kw / 2, ky + kh,
      color=C_AUTH, bidirectional=True, label="OIDC upstream")

# MAS ↔ Synapse  (MSC3861 delegation)
arrow(ax, sx + sw / 2, sy,
      mx2 + mw / 2, my2 + mh,
      color="#999999", bidirectional=True, label="MSC3861")

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor=C_EDGE  + "33", edgecolor=C_EDGE,   label="Edge / proxy"),
    mpatches.Patch(facecolor=C_AUTH  + "33", edgecolor=C_AUTH,   label="Auth layer"),
    mpatches.Patch(facecolor=C_MATRIX+ "33", edgecolor=C_MATRIX, label="Matrix / media"),
    mpatches.Patch(facecolor=C_NOTIF + "33", edgecolor=C_NOTIF,  label="Notifications"),
    mpatches.Patch(facecolor=C_DB   + "33",  edgecolor=C_DB,     label="Database"),
]
ax.legend(handles=legend_items, loc="upper right",
          fontsize=8, framealpha=0.85,
          bbox_to_anchor=(0.995, 0.995),
          fancybox=True)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(FIG_W / 2, FIG_H - 0.25, "Matrix / Synapse Self-Hosted Stack — Architecture",
        ha="center", va="top", fontsize=12, fontweight="bold", color=DARK)

plt.tight_layout(pad=0.2)
plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor=C_BG)
print(f"Saved {OUT}")
