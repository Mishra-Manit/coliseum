---
id: opp_f7523215
event_ticker: KXNBAMENTION-26MAR07PHIATL
market_ticker: KXNBAMENTION-26MAR07PHIATL-INJU
yes_price: 0.96
no_price: 0.05
close_time: '2026-03-08T04:00:00Z'
discovered_at: '2026-03-07T16:57:07.431547Z'
status: recommended
research_completed_at: '2026-03-07T16:57:50.504327+00:00'
research_duration_seconds: 32
recommendation_completed_at: '2026-03-07T16:57:55.960175+00:00'
action: null
---

# What will the announcers say during Philadelphia vs Atlanta Professional Basketball Game?

**Outcome**: Injury / Injured

## Scout Assessment

**Rationale**: CONFIRMED (structural): This market resolves based on whether the broadcast audio contains the word/phrase "Injury / Injured" during the specified Philadelphia vs Atlanta NBA game, and the game/broadcast is scheduled to occur before the market close (2026-03-08 04:00 UTC). Supporting evidence: the contract is priced at 96¢ YES (4–5¢ NO), implying the market expects at least one mention; these mention-prop markets typically have many opportunities for the word to occur during injury updates, foul/medical stoppages, and sideline reports. Resolution source: Kalshi rules/methodology for the KXNBAMENTION event (official Kalshi market resolution based on the broadcast transcript/recording). Risk checklist: clear resolution source ✓; stable inputs (single broadcast, binary mention) ✓; no formal appeals/reviews typically applicable ✓. Risk level: LOW (selected as the single lowest-risk available in this dataset given Tier exclusions and close-within-48h constraint). Remaining risks: if the game is postponed/canceled, broadcast feed differs from the referenced source, or "injury" is never said on-air. Sources: https://kalshi.com/

## Market Snapshot

| Metric | Value |
|--------|-------|
| Yes Price | 96¢ ($0.96) |
| No Price | 5¢ ($0.05) |
| Closes | 2026-03-08 04:00 AM |

---

## Research Synthesis

**Flip Risk: UNCERTAIN**

**Event Status:**
Multiple independent schedule listings show Philadelphia at Atlanta on **Saturday, March 7, 2026**, with tip around **6:00–7:30 PM ET** at State Farm Arena (i.e., the event appears scheduled and not obviously canceled). citeturn0search1turn0search4turn0search0 No search result surfaced a postponement/cancellation notice.

**Key Evidence For YES:**
- There is contemporaneous, game-specific injury context: a March 7 “Hawks vs. 76ers Injury Report” article states **Philadelphia has multiple players listed on the injury report** and Atlanta has at least one questionable player (knee). This increases the chance the announcers say “injury/injured” during availability updates or in-game context. citeturn0search2
- The event’s distribution suggests a likely nationally-available broadcast: listings note **NBA TV / League Pass** and local RSNs (e.g., FDSN SE, NBC Sports Philadelphia variant), making a standard broadcast (with typical injury storylines/updates) likely to occur. citeturn0search1turn0reddit14

**Key Evidence Against YES / Risks Found:**
- **Structural/operational ambiguity risk:** The market’s rules (as shown on Coinbase’s Kalshi event page) state resolution is based on **video primarily**, but if no consensus, then **transcripts** are used “according to the news publications listed in the contract,” and it further specifies **national broadcast** (or home local if not nationally televised). This introduces edge cases: feed mismatch (national vs local), or a word audible on one feed but not used/recognized in the reviewed recording/transcript. citeturn1search2turn2search1
- **Word-form edge case:** Rules text says the “exact phrase/word, or a plural or possessive form… must be used,” and that “grammatical/tense inflections are otherwise not included.” That could matter if only “injuries” counts but “injured” is treated as a tense/inflection (or vice versa), depending on the contract’s exact target token(s). I could not find the INJU-specific contract text clarifying whether both “injury” and “injured” are explicitly included. citeturn1search2turn2search13
- **Precedent of mention-market disputes:** Community reports indicate some “mentions” style markets have resolved contrary to a trader’s recollection of hearing a phrase, with the implication that Kalshi uses a specific “official” source/interpretation. This is not about INJU specifically, but it is relevant operational risk. citeturn0reddit19turn0reddit18

**Resolution Mechanics:**
For this event type, the rules text visible on Coinbase says YES requires the **play-by-play or color commentator(s)** to say the target word during the game window (tip-off to end, including OT). Resolution uses **video as primary evidence**; if consensus cannot be reached, **transcripts** may be used; and it resolves on the **national broadcast**, else the home local broadcast. Ads with announcers do not count, but promotional content aired during the event does. citeturn1search2turn2search1

**Unconfirmed:**
- The exact INJU market’s own “full rules” page/PDF (whether it explicitly includes both **“injury”** and **“injured”**, and how it treats “injuries”).
- Confirmation of the **designated national broadcast** for this specific game as carried in practice (NBA TV vs local only), and whether Kalshi’s reviewed video source matches what most viewers see.
- Any historical dataset showing how often INJU mention markets unexpectedly resolve NO.

**Conclusion:**
The underlying game appears on schedule, and there is current, game-specific injury-report content—both of which support a high chance the word “injury” is said at least once. citeturn0search2turn0search1 However, the biggest flip risk is **resolution mechanics/word-form mismatch** (broadcast-source selection + strict morphology rules + potential reliance on a reviewed recording/transcript rather than “what viewers heard”), which can create surprise NO outcomes even when the intuitive event seems likely. citeturn1search2turn2search13turn0reddit19 **Confidence: MEDIUM-LOW**, with the single biggest remaining uncertainty being the INJU-specific wording/rules page (exact accepted forms and the precise broadcast source used).

**Sources (URLs checked):**
1. https://www.ticketmaster.com/atlanta-hawks-v-philadelphia-76ers-atlanta-georgia-03-07-2026/event/0E0062FD9AD1163A
2. https://www.nba.com/hawks/tickets/games/2025-26/atlanta-hawks-vs-philadelphia-76ers-atlanta-ga-tickets-03-07-2026
3. https://www.nba.com/game/0022500917
4. https://foxsportsthegame.iheart.com/content/2026-03-07-hawks-vs-76ers-injury-report-march-7/
5. https://www.reddit.com/r/sixers/comments/1rn68id/tailgate_thread_philadelphia_76ers_3428_atlanta/
6. https://www.coinbase.com/en-mx/predictions/event/KXNBAMENTION-26MAR07PHIATL
7. https://www.cftc.gov/sites/default/files/filings/orgrules/25/03/rules03072516933.pdf
8. https://www.reddit.com/r/Kalshi/comments/1ojms4h/it_has_happened_to_me/
9. https://www.reddit.com/r/Kalshi/comments/1pv0kr9/kalshi_mentions_market_where_livestream_ended_and/
