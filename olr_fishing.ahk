#Requires AutoHotkey v2.0
#SingleInstance Force
#Include FindText.ahk

global MasterOn := true
global FishingOn := false
global FoundNear := false
global Scanning := false

global RestUntil := [0, 0, 0, 0, 0]
global LastBuff := 0

ErrNum4 := 0.2
ErrNum5 := 0.2
ErrNum6 := 0.2
ErrNum7 := 0.2
ErrNum8 := 0.2
BuffErr := [ErrNum4, ErrNum5, ErrNum6, ErrNum7, ErrNum8]
ScanMs := 10
NearR := 10
StripRX := 50

SearchX1 := 518
SearchY1 := 0
SearchX2 := 1165
SearchY2 := 392

BadSpots := [[36, 339]]
BadSpotR := 50

BuffText := [
    "|<buff_num4>*80$32.00000000000zzzzwDzzzz3zzk7kzzs0wC07Ub3U07tks03zAC03zv3U1zyks0DzoD3Vzx3kcDz0wG3zsD6V7y3lcLzUwu4zwCOVYz35gxbkWHcEw0bzwC0E0k3U5061w000Ez0433Dk7X4Tw6kUVz30k6DkU00Vw00000000002"
    , "|<buff_num5>*80$32.000000000000000000000000000000000y00000M00033U000UCs0080w00101s00DUAE01c1/U0G7nA06t6E01gLnU0Poo006xZb01fxhkUH8R4A3Vyt1U05z0E007k1U00r31300Etr400DtUU03zk400zs00000000000002"
    , "|<buff_num6>*80$32.00000000000zzzzwDvzzz3s7zzkw0TzwCEG073js01knz00QBzw073TzU1kjzk0w/zs0D0zg03kTm3kw7yV4D1zcLXkzu4owDqVZb3tcx8kQG8N467by81c3020w1U0UDlU003wk080zkW7UDtUEm3wM20ky800400000000002"
    , "|<buff_num7>*80$32.00000000000zw03wD000z3U007kw2H0wC70MD3301VkUW0AQ220131VY88kmNM048XlUF0/cT002m7k00CZ4E03jLG0EOAkk8aza225jxUEUnsQ487zxE20U7zUU23Cs80C362810D0U3420+3U012qE63kbk13w00000080002"
    , "|<buff_num8>*80$32.00000000000zzzzwDkTy73lnzDkwCTrwC0xnz30iBzks71zwC1UDz3kk1zkw80DwDjU3z3zc0TkzG3nwDyV5z3zcLzkzu4vwDyVaT3zcxlkNm0S007Vz00003s0000jU0001U003oE003b0000Uk000s2000800000000000002"
]
BuffText2 := [
    "|<buff_num4_png>*80$32.k0000E00000zzzzwDzzzz3zzs7kzzs0wC07Ub3U07xks03zQC03zv3U1zykw0DzoD3Fzx3kYDz0wF3zsD9F7y3qqLzUz04zwCTNYz34qx7kmRcEw9bzwC0E0k7U5063w000Mz0A13zk7VWTw6kENz30M2DkU00Pw00000M00006"
    , "|<buff_num5_png>*80$32.U0000E0000000000000000000000U0000y00000M00033U000UCs0080w00161s00/kAE01Y1DU0F7mA0BF6E06rLnU10Io40TRZZ01rxhkU58N4A1tzt1U05z0E006k1U00r30102EtkY00Dtkk03zM400zw000U0000A00006"
    , "|<buff_num6_png>*80$32.k0000E00000zzzzwDzzzz3s7zzkw0TzwCEz073js01knz00QBzw073TzU1kjzk0w/zs0D0zY03kTl3kw7tF4D1yqLnkz04pwDzNZb3tqx8kwB8NA63ryN1w3020yFU2kDtU003zkU80zsX7kDskEq3wM30kyA0040000080000C"
    , "|<buff_num7_png>*80$32.k0000M00000zy03wD000z3U007my2P1wC20MD3301VkUW0AQ2001X9VW+8kkTM048XlUF0/aT002l7k00RL4E06rrG010wlkAzTa225rxUEUBsS489zzE2EU7zUU23Cs80C162810D0U3020+3U032qE67kbk03wU0000S0802C"
    , "|<buff_num8_png>*80$32.k0000E00000zzzzwDkTyD3lnzDkwCTrwC0xnz3UiBzks71zwC1UDz3kk1zky80TwDjE3z3zY0Tkzl3nwDtF7z3yqLzkz04vwDzNaT3zoxnkht8So01lz00003s0020jU002FU04/wM003X0000kE00AM3000400000000800006"
]

ErrorText2 := "|<buff4s_error_2>*80$32.0000000000000000Tzzzy7yLzzVz1zzsTyTzy4bDzzVfXzzsQtzzy7CTzzVfbzzsGHzzy7zzzzVzjzzsTvzzy7yzxzVyDzDsTzzzy7zzzzVzzzrsTzzvy7zzxzVzzzzsTxzzy7zjzzVzzzzsTzXzy7zkTzVzs3zsTy0zy000002"
BuffNum7Right2 := "|<buff_num7_right2>*80$12.00003w3w1w0wUwMQAQ4A0A0400E0k0F0oUkEE8E4I4o0s8AM0M1U20040w3w0000U"
BuffNum7Top := "|<buff_num7_top>*80$32.00000000000zs03wD000z30007kw2E0wC008D3301VkU00AQ200131UU00kkNE04U"
BuffNum7Third := "|<buff_num7_0007>*80$32.00000000000zs03wD000z30007kw2E0wC008D3301VkU00AQ200131UU00kkNE0483U0001cR000m7k00CV4E03eLG00OAkE06zY221jx0EU3sI487zx02007UUU02AM80606200060U1020+2U012oE43kZk03w00000000002"
BuffNum6Third := "|<buff_num6_0026>*80$32.00000000000zzzzwDzzzz3s7zzkw0TzwCEn073js01knz00QBzw073TzU1kjzk0w/zs0D0w203kTt3kw7yl4D1z6LnkzwYowDz9Zb3ymx8kxVcNA6TryM1k3020y1U2UDlU003yk080zt67UDtUUq3wk40ky800400000000002"
BuffNum4Third := "|<buff_num4_0003>*80$32.00000000001zzzzsTzzzy7zzkDVzzk1sQ0T1C700DvVk07ysQ07zq703zxVs0TzcS6Xzu7V8Ty1sW7zkSGWDw7hgjz1y09zsQyn9y69huDVYvEVsHDzsQ0U1UD0O0A7s000ly0867zUD68zsBV13y61UQTV0017s00000000002"
BuffNum5Third := "|<buff_num5_0011>*80$32.000000000000000000000000000000000600000M00023U000U4k0080M00141U00/k8E00Y1/00F7k40BF6006qLn010oo00TRYU00rx00058N001lwE1U04n0E004E0U00F000000s0000/FUU03Qk400Qs00000000000002"
BuffNum7Right := "|<buff_num7_right>*80$12.00003w3w1w0wUwMQAQ4A2A0414k0k0F0oUkkM8M4Q4p0zsCsAM3k2004Uw3w0000U"
BuffName := ["buff_num4", "buff_num5", "buff_num6", "buff_num7", "buff_num8"]
BuffKey := ["Numpad4", "Numpad5", "Numpad6", "Numpad7", "Numpad8"]
BuffSpace := [true, true, true, false, false]

ErrorText := "|<buff4s_error>*80$32.zzzzzk0000A00001TzzzyLzzzzZzzzztTzzzyLzzzzZzjzztTvzzyLyzzzZzjzztTvzzyLyzzzZzjzztTzzry7yzxzZzDz7sTzzzyLzzzzVzzzrtTzzvyLzzzzZzzzztTxzzyLzjjzZzzzztTzXzy7zkTzZzs3ztTy0TyE00006"
ErrorErr := 0.3

BloodRX1 := 0.30
BloodRX2 := 0.70
BloodRY1 := 0.04
BloodRY2 := 0.20

BloodText := "|<buff_blood>*125$32.0000000000000M1z07zzzk1zzzw0zzzz0Tzzzk7zzzw0zzzz00zzzk0Dzzw00000U"
BloodErr := 0.1
RestShort := 2900
RestLong := 5100

MemX := [-1, -1, -1, -1, -1]
MemY := [-1, -1, -1, -1, -1]

SetTimer(FishTimer1, ScanMs)
SetTimer(StartFishTimer2, -2)
SetTimer(StartFishTimer3, -5)
SetTimer(StartFishTimer4, -7)

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

SC029:: {
    global MasterOn, FishingOn, RestUntil, LastBuff
    MasterOn := !MasterOn
    if (!MasterOn) {
        FishingOn := false
        RestUntil := [0, 0, 0, 0, 0]
        LastBuff := 0
        ShowTip("脚本已暂停")
    } else {
        ShowTip("脚本已开启")
    }
}

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
        RestUntil := [0, 0, 0, 0, 0]
        ShowTip("血条消失，钓鱼功能关闭")
        PlayBloodGone()
    }
}

ShowTip(text) {
    MouseGetPos(&mx, &my)
    ToolTip(text, mx + 20, my + 20)
    SetTimer(HideTip, -2000)
}

HideTip() {
    ToolTip()
}

PlayBloodGone() {
    SoundBeep(880, 120)
    SoundBeep(659, 200)
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

ScanPass() {
    global BuffText, BuffErr, RestUntil, LastBuff
    global ErrorText, ErrorErr
    for _, i in [4, 5] {
        if (FindBuff(i, BuffErr[i], &fx, &fy) && CanPress(i)) {
            LogAction(i, fx, fy, "p1")
            DoBuffAction(i)
            return true
        }
    }
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
    for _, i in [1, 2, 3] {
        if (FindBuff(i, BuffErr[i], &fx, &fy) && CanPress(i)) {
            pr := (i != LastBuff) ? "p3" : "p4"
            LogAction(i, fx, fy, pr)
            DoBuffAction(i)
            return true
        }
    }
    return false
}

CanPress(i) {
    global RestUntil
    return A_TickCount >= RestUntil[i]
}

FindError(&ex, &ey) {
    global ErrorText, ErrorText2, ErrorErr
    global SearchX1, SearchY1, SearchX2, SearchY2
    if (TryFind(ErrorText, SearchX1, SearchY1, SearchX2, SearchY2, ErrorErr, &ex, &ey))
        return true
    return TryFind(ErrorText2, SearchX1, SearchY1, SearchX2, SearchY2, ErrorErr, &ex, &ey)
}

FindBuff(i, err, &fx, &fy) {
    global BuffText, BuffText2, BuffNum4Third, BuffNum5Third, BuffNum6Third, BuffNum7Third, BuffNum7Right, BuffNum7Top, BuffNum7Right2, MemX, MemY, NearR, StripRX, FoundNear
    global SearchX1, SearchY1, SearchX2, SearchY2
    FoundNear := false
    pats := [BuffText[i], BuffText2[i]]
    if (i = 1)
        pats.Push(BuffNum4Third)
    if (i = 2)
        pats.Push(BuffNum5Third)
    if (i = 3)
        pats.Push(BuffNum6Third)
    if (i = 4) {
        pats.Push(BuffNum7Third)
        pats.Push(BuffNum7Right)
        pats.Push(BuffNum7Top)
        pats.Push(BuffNum7Right2)
    }
    for _, e2 in [err, 0.25] {
        if (MemX[i] >= 0) {
            x1 := Max(MemX[i] - NearR, 0)
            y1 := Max(MemY[i] - NearR, 0)
            x2 := Min(MemX[i] + NearR, A_ScreenWidth)
            y2 := Min(MemY[i] + NearR, A_ScreenHeight)
            for _, pat in pats {
                if (TryFind(pat, x1, y1, x2, y2, e2, &fx, &fy)) {
                    MemX[i] := fx
                    MemY[i] := fy
                    FoundNear := true
                    return true
                }
            }
            sx1 := Max(MemX[i] - NearR, 0)
            sy1 := Max(MemY[i] - NearR, 0)
            sx2 := Min(MemX[i] + StripRX, A_ScreenWidth)
            sy2 := Min(MemY[i] + NearR, A_ScreenHeight)
            for _, pat in pats {
                if (TryFind(pat, sx1, sy1, sx2, sy2, e2, &fx, &fy)) {
                    MemX[i] := fx
                    MemY[i] := fy
                    return true
                }
            }
        }
        for _, pat in pats {
            if (TryFind(pat, SearchX1, SearchY1, SearchX2, SearchY2, e2, &fx, &fy)) {
                MemX[i] := fx
                MemY[i] := fy
                return true
            }
        }
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
        if (!IsNearBadSpot(m.x, m.y)) {
            fx := m.x
            fy := m.y
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
    global BuffKey, BuffSpace, RestShort, RestLong, RestUntil, LastBuff
    Send("{" BuffKey[i] "}")
    if (BuffSpace[i]) {
        Sleep(2000)
        Send("{Space}")
    }
    LastBuff := i
    RestUntil[i] := A_TickCount + (BuffSpace[i] ? RestShort : RestLong)
}
