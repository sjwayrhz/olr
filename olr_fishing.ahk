; olr_fishing.ahk - ArcheAge One Last Ride fishing helper (AHK v2)
; Requires FindText.ahk in the same folder.
;
; SC029 (` key, top-left under Esc) : toggle the whole script on / off
; Fishing mode is automatic: every 500 ms the script looks for the
; blue bar (blood bar) in a search region defined as fractions of the
; screen (so it scales to other resolutions); finding it enters
; fishing mode, losing it leaves fishing mode. Each change shows a
; tooltip at the mouse cursor for 2 seconds, then it disappears (it
; does not stay at the cursor).
;
; Fishing searches the top strip (x 518-1165, y 0-392) for the 5 buff
; icons. Four timers fire every 10 ms, staggered ~2.5 ms apart, so a
; scan is attempted about every 2.5 ms; whichever timer finds a buff
; first acts on it. Once a buff is found, its position is remembered;
; later searches look nearby first (within 100 pixels up and down) and
; fall back to the top strip if not found nearby.
; Each scan runs one pass over all 5 buffs, each at its own tolerance
; (BuffErr[i]; one number per buff: 0.1 num4, 0.2 num5, 0.1 num6,
; 0.1 num7, 0.1 num8).
; Every action is logged to olr_fishing_log.txt next to the script.
;
; Priority levels, smaller number = higher priority:
;   1. num7/num8: press immediately when found.
;   2. buff4s_error (red down-arrow, no key bound): when found,
;      immediately scan the 5 buffs (7,8,4,5,6) and press based on
;      what is found.
;   3. A buff different from the last one acted on: press immediately.
;   4. The same buff as the last one: press only after its rest
;      (RestShort/RestLong) has elapsed.
; The rest times themselves are unchanged (RestShort 2.6s, RestLong 5.1s).
;
; Buff -> key (numpad keys, right side of the keyboard):
;   buff_num4 -> Numpad4, wait 2s, Space, rest 2.6s
;   buff_num5 -> Numpad5, wait 2s, Space, rest 2.6s
;   buff_num6 -> Numpad6, wait 2s, Space, rest 2.6s
;   buff_num7 -> Numpad7, rest 5.1s
;   buff_num8 -> Numpad8, rest 5.1s
; Rest is a real wait for the low-priority buffs (num4/5/6): after an
; action the script waits the full rest (2.6s / 5.1s) before pressing
; one of them. The high-priority buffs (num7/num8) are checked first
; and interrupt a rest at once, so they are pressed the moment they
; appear. A buff different from the last one acted on is also pressed
; at once (Priority 3); only the same buff has to wait out its rest
; (Priority 4).
;
; FindText patterns: threshold 80, generated from the fresh 32x32
; live-buff crops (images/buff_num*_1.jpg, tools/gen_buff_patterns.py).
; The 5 new crops all carry the white "1s" countdown text, which makes
; them look alike: at T=120 the worst pair (num4 vs num8, both orange
; arrows) separates by only 0.270, below the 0.3 tolerance. T=80 is
; the best threshold for this set: worst pair separates by 0.333,
; above 0.3, with fragility similar to T=120. The orange-arrow buffs
; num4/num6/num8 stay close (num8 pattern vs num4 image is 0.266),
; but every tolerance is now 0.2 or lower, well under 0.266, so a
; num4 icon is not read as num8 even though the loop checks num8
; first. Keep every tolerance at or below 0.2 -- do not raise them,
; or num4/num6/num8 will be confused.

#Requires AutoHotkey v2.0
#SingleInstance Force
#Include FindText.ahk

global MasterOn := true
global FishingOn := false
global FoundNear := false
global Scanning := false

; Rest state: after acting on a buff, the script rests until RestUntil
; (a tick count). The rest only blocks the SAME buff (RestBuff): while
; it runs, a different buff is pressed at once (Priority 3), and the
; same buff is pressed only after the rest ends (Priority 4). The
; buff just acted on (RestBuff) is still on screen during its rest.
global RestUntil := 0
global RestBuff := 0

; Tolerance per buff, one number per key (no groups). num5 is 0.2.
; 2026-11-26: a tolerance of 0.4 was tried and reverted the same
; night: 0.4 is above the 0.387 separation between num5 and num7,
; so each one's pattern also matched the other's icon (num7 read as
; num5). With the current T=80 patterns the worst pair (num4 vs
; num8) only separates by 0.333, so keep every number at or below
; 0.2.
ErrNum4 := 0.1
ErrNum5 := 0.2
ErrNum6 := 0.1
ErrNum7 := 0.1
ErrNum8 := 0.1
BuffErr := [ErrNum4, ErrNum5, ErrNum6, ErrNum7, ErrNum8]
ScanMs := 10
NearR := 100

; Search region: the buff bar lives in this top strip (x 518-1165,
; y 0-392). Searching only this strip is much faster than full screen,
; and it excludes the left-edge game world (x < 518) whose dark patches
; kept false-matching every buff, and the fishing panel below y 392.
SearchX1 := 518
SearchY1 := 0
SearchX2 := 1165
SearchY2 := 392

; Known false-positive spots: dark patches of game world that match a
; buff pattern even though no buff is there. (36,339) is a dark patch
; on the left edge that keeps matching buff_num4. Matches near these
; spots are ignored and never remembered.
BadSpots := [[36, 339]]
BadSpotR := 50

; Search logic: first search the top strip. Once a buff is found,
; remember its position; later searches look nearby first (within
; 100 pixels up and down) and fall back to a top-strip search if
; not found nearby.

; Buff order: num4, num5, num6, num7, num8
BuffText := [
    "|<buff_num4>*80$32.00000000000zzzzwDzzzz3zzk7kzzs0wC07Ub3U07tks03zAC03zv3U1zyks0DzoD3Vzx3kcDz0wG3zsD6V7y3lcLzUwu4zwCOVYz35gxbkWHcEw0bzwC0E0k3U5061w000Ez0433Dk7X4Tw6kUVz30k6DkU00Vw00000000002"
    , "|<buff_num5>*80$32.000000000000000000000000000000000y00000M00033U000UCs0080w00101s00DUAE01c1/U0G7nA06t6E01gLnU0Poo006xZb01fxhkUH8R4A3Vyt1U05z0E007k1U00r31300Etr400DtUU03zk400zs00000000000002"
    , "|<buff_num6>*80$32.00000000000zzzzwDvzzz3s7zzkw0TzwCEG073js01knz00QBzw073TzU1kjzk0w/zs0D0zg03kTm3kw7yV4D1zcLXkzu4owDqVZb3tcx8kQG8N467by81c3020w1U0UDlU003wk080zkW7UDtUEm3wM20ky800400000000002"
    , "|<buff_num7>*80$32.00000000000zw03wD000z3U007kw2H0wC70MD3301VkUW0AQ220131VY88kmNM048XlUF0/cT002m7k00CZ4E03jLG0EOAkk8aza225jxUEUnsQ487zxE20U7zUU23Cs80C362810D0U3420+3U012qE63kbk13w00000080002"
    , "|<buff_num8>*80$32.00000000000zzzzwDkTy73lnzDkwCTrwC0xnz30iBzks71zwC1UDz3kk1zkw80DwDjU3z3zc0TkzG3nwDyV5z3zcLzkzu4vwDyVaT3zcxlkNm0S007Vz00003s0000jU0001U003oE003b0000Uk000s2000800000000000002"
]
BuffName := ["buff_num4", "buff_num5", "buff_num6", "buff_num7", "buff_num8"]
BuffKey := ["Numpad4", "Numpad5", "Numpad6", "Numpad7", "Numpad8"]
BuffSpace := [true, true, true, false, false]

; buff4s_error: the red down-arrow buff that appears under the fish bar
; (images/buff4s_error.png, 32x32, threshold 80, same as the other
; buffs). No key is bound to it -- it is only detected. When it appears,
; the script immediately scans the 5 buffs and acts on what it finds
; (Priority 2). Well separated from all 5 buffs (worst cross-error
; 0.536, far above the 0.2 tolerance), so it is never confused with them.
ErrorText := "|<buff4s_error>*80$32.zzzzzk0000A00001TzzzyLzzzzZzzzztTzzzyLzzzzZzjzztTvzzyLyzzzZzjzztTvzzyLyzzzZzjzztTzzry7yzxzZzDz7sTzzzyLzzzzVzzzrtTzzvyLzzzzZzzzztTxzzyLzjjzZzzzztTzXzy7zkTzZzs3ztTy0TyE00006"
ErrorErr := 0.2

; Blood bar search region, as fractions of the screen.
; The blue bar sits at x 0.367-0.632, y 0.064-0.078 of the screen
; (measured in a 1600x900 game; the same ratios hold at other
; resolutions when the game is full screen). The search region below
; adds a margin around it, so the bar is found even if the UI shifts
; a little. No fixed pixel coordinates are used for the blood bar
; any more.
BloodRX1 := 0.30
BloodRX2 := 0.70
BloodRY1 := 0.04
BloodRY2 := 0.10

; Blood bar pattern, 32x12, threshold 125, from images/buff_blood.png
; (replaced 2026-11-27: the old one was a 49x15 red HP bar, this one
; is the blue bar right under it). The bar is a blue gradient (gray
; 119-137), so T=125 gives a perfect dark/bright split (193 dark,
; 191 bright). Searched by screen fractions (x 0.30-0.70, y 0.04-0.10),
; not fixed pixels. Tolerance 0.2: verified against her 5 old
; screenshots, the pattern matches the blue bar at (590-592, 58) with
; max err 0.057-0.093, well inside 0.2.
BloodText := "|<buff_blood>*125$32.0000000000000M1z07zzzk1zzzw0zzzz0Tzzzk7zzzw0zzzz00zzzk0Dzzw00000U"
BloodErr := 0.2
; Rest times: only two numbers to change. Short rest follows the
; buffs that press Space (num4, num5, num6); long rest follows the
; rest-only buffs (num7, num8).
RestShort := 2600
RestLong := 5100

MemX := [-1, -1, -1, -1, -1]
MemY := [-1, -1, -1, -1, -1]

; Four scan timers, each firing every 10 ms, staggered ~2.5 ms apart
; (offsets 0, 2, 5, 7 ms), so a scan is attempted about every 2.5 ms.
; Whichever timer finds a buff first acts on it and the script rests;
; while a scan is in progress the other timers skip (Scanning guard),
; because AHK runs on one thread and two scans must never overlap.
SetTimer(FishTimer1, ScanMs)
SetTimer(StartFishTimer2, -2)
SetTimer(StartFishTimer3, -5)
SetTimer(StartFishTimer4, -7)

; Blood bar check: every 500 ms, look for the blue bar in its search
; region (fractions of the screen). Finding it enters fishing mode
; automatically (no F5 needed); losing it leaves fishing mode.
; Runs only while the script itself is on (MasterOn).
SetTimer(BloodCheck, 500)

FishTimer1() {
    FishTimer()
}
FishTimer2() {
    FishTimer()
}
FishTimer3() {
    FishTimer()
}
FishTimer4() {
    FishTimer()
}
StartFishTimer2() {
    SetTimer(FishTimer2, ScanMs)
}
StartFishTimer3() {
    SetTimer(FishTimer3, ScanMs)
}
StartFishTimer4() {
    SetTimer(FishTimer4, ScanMs)
}

; ` toggles the whole script. Turning it off also stops fishing.
SC029:: {
    global MasterOn, FishingOn, RestUntil
    MasterOn := !MasterOn
    if (!MasterOn) {
        FishingOn := false
        RestUntil := 0
        ShowTip("脚本已暂停")
    } else {
        ShowTip("脚本已开启")
    }
}

; Blood bar check, every 500 ms. When the blue bar appears in its
; search region (fractions of the screen), enter fishing mode
; automatically and show a tip at the mouse cursor. When it
; disappears, leave fishing mode.
BloodCheck() {
    global MasterOn, FishingOn, BloodText, BloodErr
    global BloodRX1, BloodRX2, BloodRY1, BloodRY2
    global RestUntil
    if (!MasterOn) {
        return
    }
    bx1 := Round(A_ScreenWidth * BloodRX1)
    by1 := Round(A_ScreenHeight * BloodRY1)
    bx2 := Round(A_ScreenWidth * BloodRX2)
    by2 := Round(A_ScreenHeight * BloodRY2)
    bx := 0
    by := 0
    matches := ""
    try matches := FindText(&bx, &by, bx1, by1, bx2, by2, BloodErr, BloodErr, BloodText)
    found := IsObject(matches) && matches.Length > 0
    if (found && !FishingOn) {
        FishingOn := true
        ShowTip("发现血条，钓鱼功能开启")
    } else if (!found && FishingOn) {
        FishingOn := false
        RestUntil := 0
        ShowTip("血条消失，钓鱼功能关闭")
    }
}

; Show a tooltip at the mouse cursor for 2 seconds, then hide it.
ShowTip(text) {
    MouseGetPos(&mx, &my)
    ToolTip(text, mx + 20, my + 20)
    SetTimer(HideTip, -2000)
}

HideTip() {
    ToolTip()
}

FishTimer() {
    global MasterOn, FishingOn, Scanning
    if (!MasterOn || !FishingOn || Scanning) {
        return
    }
    Scanning := true
    ScanPass()
    Scanning := false
}

; One scan pass over all 5 buffs, each at its own tolerance
; (BuffErr[i]: 0.1 num4, 0.2 num5, 0.1 num6, 0.1 num7, 0.1 num8).
; Acts on the first match and returns true.
; Priority levels, smaller number = higher priority:
;   1. num7/num8: press immediately when found.
;   2. buff4s_error: when found, immediately scan the 5 buffs
;      (7,8,4,5,6) and press based on what is found.
;   3. A buff different from the last one acted on: press immediately.
;   4. The same buff as the last one: press only after its rest
;      (RestShort/RestLong) has elapsed.
; The rest times themselves are unchanged.
ScanPass() {
    global BuffText, BuffErr, RestUntil, RestBuff
    global ErrorText, ErrorErr
    ; Priority 1: num7/num8 first, press immediately.
    ; Indices: 1=num4, 2=num5, 3=num6, 4=num7, 5=num8.
    for _, i in [4, 5] {
        if (FindBuff(i, BuffErr[i], &fx, &fy)) {
            LogAction(i, fx, fy, "p1")
            DoBuffAction(i)
            return true
        }
    }
    ; Priority 2: buff4s_error. If found, immediately scan the 5 buffs
    ; (7,8,4,5,6) and press the first one that may be pressed.
    if (FindError(&ex, &ey)) {
        for _, i in [4, 5, 1, 2, 3] {
            if (FindBuff(i, BuffErr[i], &fx, &fy) && CanPress(i)) {
                LogAction(i, fx, fy, "p2")
                DoBuffAction(i)
                return true
            }
        }
        return false
    }
    ; Priority 3/4: num4/5/6. Press if different from the last buff,
    ; or the same buff but its rest time has elapsed.
    for _, i in [1, 2, 3] {
        if (FindBuff(i, BuffErr[i], &fx, &fy) && CanPress(i)) {
            pr := (i != RestBuff) ? "p3" : "p4"
            LogAction(i, fx, fy, pr)
            DoBuffAction(i)
            return true
        }
    }
    return false
}

; May buff i be pressed now?
; Priority 3: a buff different from the last one acted on is pressed
; immediately. Priority 4: the same buff is pressed only after its
; rest (RestShort/RestLong) has elapsed.
CanPress(i) {
    global RestUntil, RestBuff
    if (i != RestBuff) {
        return true
    }
    return A_TickCount >= RestUntil
}

; Find the buff4s_error icon in the top strip. No key is bound to it;
; it only triggers an immediate scan of the 5 buffs (Priority 2).
FindError(&ex, &ey) {
    global ErrorText, ErrorErr
    global SearchX1, SearchY1, SearchX2, SearchY2
    return TryFind(ErrorText, SearchX1, SearchY1, SearchX2, SearchY2, ErrorErr, &ex, &ey)
}

; Search buff i: nearby first if its position is remembered, else the
; top search strip. On success, remember the position and return true.
FindBuff(i, err, &fx, &fy) {
    global BuffText, MemX, MemY, NearR, FoundNear
    global SearchX1, SearchY1, SearchX2, SearchY2
    FoundNear := false
    if (MemX[i] >= 0) {
        x1 := Max(MemX[i] - NearR, 0)
        y1 := Max(MemY[i] - NearR, 0)
        x2 := Min(MemX[i] + NearR, A_ScreenWidth)
        y2 := Min(MemY[i] + NearR, A_ScreenHeight)
        if (TryFind(BuffText[i], x1, y1, x2, y2, err, &fx, &fy)) {
            MemX[i] := fx
            MemY[i] := fy
            FoundNear := true
            return true
        }
    }
    if (TryFind(BuffText[i], SearchX1, SearchY1, SearchX2, SearchY2, err, &fx, &fy)) {
        MemX[i] := fx
        MemY[i] := fy
        return true
    }
    return false
}

TryFind(text, x1, y1, x2, y2, err, &fx, &fy) {
    fx := 0
    fy := 0
    matches := ""
    try matches := FindText(&fx, &fy, x1, y1, x2, y2, err, err, text)
    if (!IsObject(matches) || matches.Length = 0) {
        return false
    }
    for _, m in matches {
        if (!IsNearBadSpot(m.mx, m.my)) {
            fx := m.mx
            fy := m.my
            return true
        }
    }
    return false
}

IsNearBadSpot(x, y) {
    global BadSpots, BadSpotR
    for _, s in BadSpots {
        if (Abs(x - s[1]) <= BadSpotR && Abs(y - s[2]) <= BadSpotR) {
            return true
        }
    }
    return false
}

LogAction(i, fx, fy, label) {
    global BuffName, BuffKey, FoundNear
    where := FoundNear ? "near" : "full"
    line := FormatTime(, "yyyy-MM-dd HH:mm:ss") " " BuffName[i] " -> " BuffKey[i] " at " fx "," fy " " where " " label "`n"
    try FileAppend(line, A_ScriptDir "\olr_fishing_log.txt")
}

DoBuffAction(i) {
    global BuffKey, BuffSpace, RestShort, RestLong, RestUntil, RestBuff
    Send("{" BuffKey[i] "}")
    if (BuffSpace[i]) {
        Sleep(2000)
        Send("{Space}")
    }
    ; Start the rest without blocking: record which buff and when the
    ; rest ends. The rest only blocks the SAME buff (see CanPress):
    ; a different buff is pressed at once (Priority 3), the same buff
    ; only after the rest ends (Priority 4). Short rest after the
    ; Space buffs (num4/5/6), long rest after the rest-only buffs
    ; (num7/num8).
    RestBuff := i
    RestUntil := A_TickCount + (BuffSpace[i] ? RestShort : RestLong)
}
