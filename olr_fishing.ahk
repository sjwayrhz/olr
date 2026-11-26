; olr_fishing.ahk - ArcheAge One Last Ride fishing helper (AHK v2)
; Requires FindText.ahk in the same folder.
;
; SC029 (` key, top-left under Esc) : toggle the whole script on / off
; F5                               : toggle fishing on / off
; Each toggle shows a tooltip at the mouse cursor for 2 seconds, then it
; disappears (it does not stay at the cursor).
;
; Fishing searches the top strip (x 518-1165, y 0-392) for the 5 buff
; icons, every 10 ms. Once a buff is found, its position is remembered;
; later searches look nearby first (within 100 pixels up and down) and
; fall back to the top strip if not found nearby.
; Each scan runs one pass over all 5 buffs at tolerance 0.1.
; Every action is logged to olr_fishing_log.txt next to the script.
;
; Buff -> key (numpad keys, right side of the keyboard):
;   buff4s_0007.png -> Numpad4, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0005.png -> Numpad5, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0020.png -> Numpad6, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0001.png -> Numpad7, rest 5s (no scanning)
;   buff4s_0030.png -> Numpad8, rest 5s (no scanning)
;
; FindText patterns: threshold 120, generated from the 32x32 buff
; crops (tools/gen_buff_patterns.py). Threshold 180 was too dark: the
; patterns were 89-95% dark (only 53-111 bright pixels), so a dark
; patch of game world kept false-matching Buff0007 at (36,339).
; At 140 the binarized icons looked blurry and live icons were often
; missed. At 120 the patterns are 49-70% dark (311-519 bright pixels),
; the shapes are clearer, and the worst pair still separates by
; 0.351, far above the 0.1 tolerance.

#Requires AutoHotkey v2.0
#SingleInstance Force
#Include FindText.ahk

global MasterOn := true
global FishingOn := false
global FoundNear := false

BuffErrTight := 0.1
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
; on the left edge that keeps matching Buff0007. Matches near these
; spots are ignored and never remembered.
BadSpots := [[36, 339]]
BadSpotR := 50

; Search logic: first search the full screen. Once a buff is found,
; remember its position; later searches look nearby first (within
; 100 pixels up and down) and fall back to a full-screen search if
; not found nearby.

; Buff order: 0007, 0005, 0020, 0001, 0030
BuffText := [
    , "|<Buff0001>*120$32.zzzzzs00006zy0zxjs00zPk1U7qy7T1xj70wDPX41XqnXGARXn0HbNdrC8qmztXBcjtYHOPaT4q7lDr5YxLYsPKrrT6n0wxtgzTa7P7rxkqlhwS5hDzztPFnzzqqDzzxhcT3CPv3lj6zPgL1jrkj3PztDrqzwTzxU0000Tzzzzy"
    , "|<Buff0005>*120$32.zzzzzs0000600001U0003M0000q0k02BUz00NMQw00a73kk1UUDs0MA3z06177t5UTljMM1YfDq0FbvRURNbvM6rrra10wyxUTTbjM1rxxqUBwThi1vzzPk0DzqSU2DxXY01zPzXUDqzzqsljztzUPzwzzqzyTztU0000Tzzzzy"
    , "|<Buff0020>*120$32.zzzzzs00006zzzzxjzzzzPsDzzqwPzzxjNzsDPjy03qzzU0xjzy0DPzzU3qzzk0xjzs0DPzY03qTl7lxbxHaTPyrrrqz0wxxjzTZzPzqxBqzxwPBjzzzNPzzyP6zzUbljzW0wPztsSazxr7pjxsxrPzw70qzzDs5U0000Tzzzzy"
    , "|<Buff0007>*120$32.zzzzzs00006zzzzxjzzzzPzzw7qzzzMxj1ztjPk0Dxqw07zxj07zvPk1zzqw7Dzxj3lzzPlYDzqyl7ztjxHbyPyrrzqz0wzxjzTbzPhqxzqnRwTxdjzzzOKPzzqBU7zxXk4TzNS3rzqjXrzxissvzP0wjzqUDDzxU0000Tzzzzy"
    , "|<Buff0030>*120$32.zzzzzs00006zzzzxjszyDPtnzjqwzzrxj3xvzPVyBzqs71zxj1UTzPtk1zqyT0Txjzk3zPzY0zqzl7rxjxF7zPyrrzqz0wzxjzTazPzqxzqzxATxUDnz3M0M7yK03BzVXVztoMADyO68Lra1jdssUPzwjU6zyDs1U0000Tzzzzy"
]
BuffName := ["Buff0007", "Buff0005", "Buff0020", "Buff0001", "Buff0030"]
BuffKey := ["Numpad4", "Numpad5", "Numpad6", "Numpad7", "Numpad8"]
BuffSpace := [true, true, true, false, false]
BuffRest := [3500, 3500, 3500, 5200, 5200]

MemX := [-1, -1, -1, -1, -1]
MemY := [-1, -1, -1, -1, -1]

SetTimer(FishTimer, ScanMs)

; ` toggles the whole script. Turning it off also stops fishing.
SC029:: {
    global MasterOn, FishingOn
    MasterOn := !MasterOn
    if (!MasterOn) {
        FishingOn := false
        ShowTip("脚本已暂停")
    } else {
        ShowTip("脚本已开启")
    }
}

; F5 toggles fishing (only while the script is running).
F5:: {
    global MasterOn, FishingOn
    if (!MasterOn) {
        return
    }
    FishingOn := !FishingOn
    if (FishingOn) {
        ShowTip("钓鱼功能开启")
    } else {
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
    global MasterOn, FishingOn, BuffErrTight
    if (!MasterOn || !FishingOn) {
        return
    }
    ScanPass(BuffErrTight, "tight")
}

; One scan pass over all 5 buffs at the given tolerance.
; Acts on the first match and returns true.
ScanPass(err, label) {
    global BuffText
    for i, _ in BuffText {
        if (FindBuff(i, err, &fx, &fy)) {
            LogAction(i, fx, fy, label)
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
    global BuffKey, BuffSpace, BuffRest
    Send("{" BuffKey[i] "}")
    if (BuffSpace[i]) {
        Sleep(2000)
        Send("{Space}")
    }
    Sleep(BuffRest[i])
}
