; olr_fishing.ahk - ArcheAge One Last Ride fishing helper (AHK v2)
; Requires FindText.ahk in the same folder.
;
; SC029 (` key, top-left under Esc) : toggle the whole script on / off
; F5                               : toggle fishing on / off
; Each toggle shows a tooltip at the mouse cursor for 2 seconds, then it
; disappears (it does not stay at the cursor).
;
; Fishing watches the full screen for the 5 buff icons. Once a buff is
; found, its position is remembered; later searches look nearby first
; (faster) and fall back to a full-screen search if not found nearby.
; Each scan runs one pass over all 5 buffs at tolerance 0 (exact match only).
; Every action is logged to olr_fishing_log.txt next to the script.
;
; Buff -> key (numpad keys, right side of the keyboard):
;   buff4s_0007.png -> Numpad4, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0005.png -> Numpad5, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0020.png -> Numpad6, wait 2s, Space, rest 2s (no scanning)
;   buff4s_0001.png -> Numpad7, rest 5s (no scanning)
;   buff4s_0030.png -> Numpad8, rest 5s (no scanning)
;
; FindText patterns: threshold 180, generated from the 32x32 buff
; crops (tools/gen_buff_patterns.py). Threshold 120 was too weak: the
; worst pair (0007 vs 0030) separated by only 0.244, and the live
; animated icon crossed it, so everything matched 0007 first and only
; Numpad4 was ever pressed (2026-11-26 bug). At 180 the worst pair
; separates by 0.434.

#Requires AutoHotkey v2.0
#SingleInstance Force
#Include FindText.ahk

global MasterOn := true
global FishingOn := false
global FoundNear := false

BuffErrTight := 0
ScanMs := 400
NearR := 70

; Buff order: 0007, 0005, 0020, 0001, 0030
BuffText := [
    "|<Buff0007>*180$32.zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzxzzzzzzzzzzzzzzTzzzzjzzzztzzzzzTzzzzvzzzzbTzzztzzzzxTbzzyrrzzzUxzzzzTbzzjrxzzzxwzzzjzzzyzzzzzDyTzzrs7zzxyDzzzzjzzzzzzzzzjzzzzzzzzzzzzzzzzzzzy"
    , "|<Buff0005>*180$32.zzzzzzzzzzznzzzzs3zzzw0Lzzz7lzzzlzzTzwSytzz7bvxzlwzzDwDHzvz3zDzbyTzzxznZzzzzxjzzzxTbzzyrrzzzUxzznzTbzyzrxzzbxwzzznzzzzkjzzzztzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzy"
    , "|<Buff0020>*180$32.zzzzzzzzzzrzzzzzzzzzzzzzzzzyzzzzzzzzzzzzzzzzzvzzzzzDzzzzbzzzzvzzzzxzzzzazzzzxTzzzxTbzzyrrzzzUxzzzzTbzzzrxxzzxwvzzzzzTzzzzzTzzxznzzr1yzzzwTjzzzrzzzzzzzzzzzzzzzzzzzzzzzzzzzy"
    , "|<Buff0001>*180$40.zzzzzzzzzzzzzzTzzzxzxtzzz0znjzzzrz6vO7yTxPhhjtzKiqqzjzMvPOyzxnhhBqTriKovRxzzzzzrzzzzzDTzzzzzyzzzzzvvzzzvzbzzzzzyzzzzzzvzzzzbzjzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzTzzzzzwzzzzzztzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzy"
    , "|<Buff0030>*180$32.zzzzzzzzzzzzzzzzzzzzzzvzzzzzzzzzzDzzzzvzzzzw7zzzzDzzzzvzzzzzTzzzzzzzzzzbzzzztzzzzxTbzzyrrzzzUxzzzzTbzzzrxzzzxwzzzzzzzw0TzzzA7zzrztzvyyTzyzDxzzb3zzzzkzzzzzTzzzzvzzzzzzzzzzy"
]
BuffName := ["Buff0007", "Buff0005", "Buff0020", "Buff0001", "Buff0030"]
BuffKey := ["Numpad4", "Numpad5", "Numpad6", "Numpad7", "Numpad8"]
BuffSpace := [true, true, true, false, false]
BuffRest := [3500, 3500, 3500, 5000, 5000]

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

; Search buff i: nearby first if its position is remembered, else full screen.
; On success, remember the position and return true.
FindBuff(i, err, &fx, &fy) {
    global BuffText, MemX, MemY, NearR, FoundNear
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
    if (TryFind(BuffText[i], 0, 0, A_ScreenWidth, A_ScreenHeight, err, &fx, &fy)) {
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
    fx := matches[1].mx
    fy := matches[1].my
    return true
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
