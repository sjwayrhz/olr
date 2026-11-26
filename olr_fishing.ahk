; olr_fishing.ahk - ArcheAge One Last Ride fishing helper (AHK v2)
; Requires FindText.ahk in the same folder.
;
; SC029 (` key, top-left under Esc) : toggle the whole script on / off
; F5                               : toggle fishing on / off
; A tooltip follows the mouse cursor and shows the current state.
;
; Fishing watches the full screen for the 5 buff icons. Once a buff is
; found, its position is remembered; later searches look nearby first
; (faster) and fall back to a full-screen search if not found nearby.
;
; Buff -> key (numpad keys, right side of the keyboard):
;   buff4s_0007.png -> Numpad4, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0005.png -> Numpad5, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0020.png -> Numpad6, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0001.png -> Numpad7, rest 5s (no scanning)
;   buff4s_0030.png -> Numpad8, rest 5s (no scanning)
;
; FindText patterns: threshold 120, tolerance 0.2, generated from the
; 32x32 buff crops (tools/gen_buff_patterns.py). Pairwise separation
; checked 2026-11-26: no two patterns match each other at 0.2.

#Requires AutoHotkey v2.0
#SingleInstance Force
#Include FindText.ahk

global MasterOn := true
global FishingOn := false

BuffErr1 := 0.2
BuffErr0 := 0.2
ScanMs := 400
NearR := 70

; Buff order: 0007, 0005, 0020, 0001, 0030
BuffText := [
    "|<Buff0007>*120$32.zzzzzs00006zzzzxjzzzzPzzw7qzzzMxj1ztjPk0Dxqw07zxj07zvPk1zzqw7Dzxj3lzzPlYDzqyl7ztjxHbyPyrrzqz0wzxjzTbzPhqxzqnRwTxdjzzzOKPzzqBU7zxXk4TzNS3rzqjXrzxissvzP0wjzqUDDzxU0000Tzzzzy"
    , "|<Buff0005>*120$32.zzzzzs0000600001U0003M0000q0k02BUz00NMQw00a73kk1UUDs0MA3z06177t5UTljMM1YfDq0FbvRURNbvM6rrra10wyxUTTbjM1rxxqUBwThi1vzzPk0DzqSU2DxXY01zPzXUDqzzqsljztzUPzwzzqzyTztU0000Tzzzzy"
    , "|<Buff0020>*120$32.zzzzzs00006zzzzxjzzzzPsDzzqwPzzxjNzsDPjy03qzzU0xjzy0DPzzU3qzzk0xjzs0DPzY03qTl7lxbxHaTPyrrrqz0wxxjzTZzPzqxBqzxwPBjzzzNPzzyP6zzUbljzW0wPztsSazxr7pjxsxrPzw70qzzDs5U0000Tzzzzy"
    , "|<Buff0001>*120$32.zzzzzs00006zy0zxjs00zPk1U7qy7T1xj70wDPX41XqnXGARXn0HbNdrC8qmztXBcjtYHOPaT4q7lDr5YxLYsPKrrT6n0wxtgzTa7P7rxkqlhwS5hDzztPFnzzqqDzzxhcT3CPv3lj6zPgL1jrkj3PztDrqzwTzxU0000Tzzzzy"
    , "|<Buff0030>*120$32.zzzzzs00006zzzzxjszyDPtnzjqwzzrxj3xvzPVyBzqs71zxj1UTzPtk1zqyT0Txjzk3zPzY0zqzl7rxjxF7zPyrrzqz0wzxjzTazPzqxzqzxATxUDnz3M0M7yK03BzVXVztoMADyO68Lra1jdssUPzwjU6zyDs1U0000Tzzzzy"
]
BuffKey := ["Numpad4", "Numpad5", "Numpad6", "Numpad7", "Numpad8"]
BuffSpace := [true, true, true, false, false]
BuffRest := [2000, 2000, 2000, 5000, 5000]

MemX := [-1, -1, -1, -1, -1]
MemY := [-1, -1, -1, -1, -1]

SetTimer(FishTimer, ScanMs)
SetTimer(TipTimer, 100)

; ` toggles the whole script. Turning it off also stops fishing.
SC029:: {
    global MasterOn, FishingOn
    MasterOn := !MasterOn
    if (!MasterOn) {
        FishingOn := false
    }
    TipTimer()
}

; F5 toggles fishing (only while the script is running).
F5:: {
    global MasterOn, FishingOn
    if (!MasterOn) {
        return
    }
    FishingOn := !FishingOn
    TipTimer()
}

TipTimer() {
    global MasterOn, FishingOn
    if (!MasterOn) {
        text := "脚本已暂停"
    } else if (FishingOn) {
        text := "钓鱼功能开启"
    } else {
        text := "钓鱼功能关闭"
    }
    MouseGetPos(&mx, &my)
    ToolTip(text, mx + 20, my + 20)
}

FishTimer() {
    global MasterOn, FishingOn, BuffText
    if (!MasterOn || !FishingOn) {
        return
    }
    for i, _ in BuffText {
        if (FindBuff(i, &fx, &fy)) {
            DoBuffAction(i)
            return
        }
    }
}

; Search buff i: nearby first if its position is remembered, else full screen.
; On success, remember the position and return true.
FindBuff(i, &fx, &fy) {
    global BuffText, MemX, MemY, NearR
    if (MemX[i] >= 0) {
        x1 := Max(MemX[i] - NearR, 0)
        y1 := Max(MemY[i] - NearR, 0)
        x2 := Min(MemX[i] + NearR, A_ScreenWidth)
        y2 := Min(MemY[i] + NearR, A_ScreenHeight)
        if (TryFind(BuffText[i], x1, y1, x2, y2, &fx, &fy)) {
            MemX[i] := fx
            MemY[i] := fy
            return true
        }
    }
    if (TryFind(BuffText[i], 0, 0, A_ScreenWidth, A_ScreenHeight, &fx, &fy)) {
        MemX[i] := fx
        MemY[i] := fy
        return true
    }
    return false
}

TryFind(text, x1, y1, x2, y2, &fx, &fy) {
    global BuffErr1, BuffErr0
    fx := 0
    fy := 0
    matches := ""
    try matches := FindText(&fx, &fy, x1, y1, x2, y2, BuffErr1, BuffErr0, text)
    if (!IsObject(matches) || matches.Length = 0) {
        return false
    }
    fx := matches[1].mx
    fy := matches[1].my
    return true
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
