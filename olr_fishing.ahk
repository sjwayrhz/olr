; olr_fishing.ahk - ArcheAge One Last Ride fishing helper (AHK v2)
; Requires FindText.ahk in the same folder.
;
; SC029 (` key, top-left under Esc) : toggle the whole script on / off
; F5                               : toggle fishing on / off
; Each toggle shows a tooltip at the mouse cursor for 2 seconds, then it
; disappears (it does not stay at the cursor).
;
; Fishing searches the top strip (x 518-1165, y 0-392) for the 5 buff
; icons. Four timers fire every 10 ms, staggered ~2.5 ms apart, so a
; scan is attempted about every 2.5 ms; whichever timer finds a buff
; first acts on it. Once a buff is found, its position is remembered;
; later searches look nearby first (within 100 pixels up and down) and
; fall back to the top strip if not found nearby.
; Each scan runs one pass over all 5 buffs, each at its own tolerance
; (BuffErr[i]; num4/num5/num6 use 0.2, num7/num8 use 0.3).
; Every action is logged to olr_fishing_log.txt next to the script.
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
; appear.
;
; FindText patterns: threshold 80, generated from the fresh 32x32
; live-buff crops (images/buff_num*_1.jpg, tools/gen_buff_patterns.py).
; The 5 new crops all carry the white "1s" countdown text, which makes
; them look alike: at T=120 the worst pair (num4 vs num8, both orange
; arrows) separates by only 0.270, below the 0.3 tolerance. T=80 is
; the best threshold for this set: worst pair separates by 0.333,
; above 0.3, with fragility similar to T=120. Note the orange-arrow
; buffs num4/num6/num8 stay close (num8 pattern vs num4 image is
; 0.266); the loop checks num4 before num8, so a num4 icon is read
; as num4 first. Keep the tolerance at 0.3 -- do not raise it, or
; num4/num6/num8 will be confused.

#Requires AutoHotkey v2.0
#SingleInstance Force
#Include FindText.ahk

global MasterOn := true
global FishingOn := false
global FoundNear := false
global Scanning := false

; Rest state: after acting on a buff, the script rests until RestUntil
; (a tick count). The rest is a real wait for the low-priority buffs
; (num4/5/6): while resting, only the high-priority buffs (num7/num8)
; are looked for, and finding one interrupts the rest at once. The
; buff just acted on (RestBuff) is still on screen during its rest.
global RestUntil := 0
global RestBuff := 0

; Tolerance per buff. num4/num5/num6 use ErrTight (0.1), num7/num8
; use ErrLoose (0.2). Only two numbers to change here.
; 2026-11-26: ErrLoose was tried at 0.4 and reverted the same night:
; 0.4 is above the 0.387 separation between num5 and num7, so each
; one's pattern also matched the other's icon (num7 read as num5).
; With the current T=80 patterns the worst pair (num4 vs num8) only
; separates by 0.333, so keep both numbers at or below 0.2.
ErrTight := 0.1
ErrLoose := 0.2
BuffErr := [ErrTight, ErrTight, ErrTight, ErrLoose, ErrLoose]
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

; Search logic: first search the full screen. Once a buff is found,
; remember its position; later searches look nearby first (within
; 100 pixels up and down) and fall back to a full-screen search if
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

; F5 toggles fishing (only while the script is running).
F5:: {
    global MasterOn, FishingOn, RestUntil
    if (!MasterOn) {
        return
    }
    FishingOn := !FishingOn
    if (FishingOn) {
        ShowTip("钓鱼功能开启")
    } else {
        RestUntil := 0
        ShowTip("钓鱼功能关闭")
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
    ScanPass("tight")
    Scanning := false
}

; One scan pass over all 5 buffs, each at its own tolerance
; (BuffErr[i]: 0.1 for num4/num5/num6, 0.2 for num7/num8).
; Acts on the first match and returns true.
; Priority: num7 and num8 are high priority and are checked first;
; num4/num5/num6 are low priority and are checked after them.
; Rest: after an action the script waits RestShort/RestLong before
; acting on a low-priority buff. A high-priority buff (num7/num8)
; found during the rest interrupts it at once and is acted on
; immediately; the low-priority ones never interrupt, so the rest
; is a real wait for them. (Before 2026-11-27 every buff interrupted
; the rest, so when buffs appeared in quick succession the script
; never actually waited -- that is why the rest seemed broken.)
ScanPass(label) {
    global BuffText, BuffErr, RestUntil, RestBuff
    if (RestUntil > 0 && A_TickCount >= RestUntil) {
        RestUntil := 0
    }
    resting := (RestUntil > 0)
    ; High priority first, then low priority. Indices: 1=num4, 2=num5,
    ; 3=num6, 4=num7, 5=num8. So check 4,5 (num7,num8) before 1,2,3.
    order := [4, 5, 1, 2, 3]
    for _, i in order {
        ; Low-priority buffs (indices 1,2,3 = num4/5/6) never
        ; interrupt a rest.
        if (resting && i <= 3) {
            continue
        }
        if (FindBuff(i, BuffErr[i], &fx, &fy)) {
            LogAction(i, fx, fy, resting ? label "-interrupt" : label)
            DoBuffAction(i)
            return true
        }
    }
    return false
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
    ; rest ends. During the rest only the high-priority buffs
    ; (num7/num8) are looked for and can interrupt it; the
    ; low-priority buffs (num4/5/6) wait out the full rest (see
    ; ScanPass). Short rest after the Space buffs (num4/5/6), long
    ; rest after the rest-only buffs (num7/num8).
    RestBuff := i
    RestUntil := A_TickCount + (BuffSpace[i] ? RestShort : RestLong)
}
