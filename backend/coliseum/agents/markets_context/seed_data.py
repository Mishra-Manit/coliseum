"""Static seed data for market category context.

Pure data — no logic. Contains the category definitions, aliases, and fallback
used by the reader (ticker matching) and refresher (Grok prompt context).
Adding a new market type is a single dict insertion.

SCOPE: Only markets that pass the Scout filter (filters.py) or have appeared
in the opportunities DB. A small buffer covers markets likely to be gated soon.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarketTypeConfig:
    """Definition for one market-type research context."""

    label: str
    resolution_desc: str
    risk_questions: list[str] = field(default_factory=list)
    uses_slug: bool = True


MARKET_TYPES: dict[str, MarketTypeConfig] = {
    # -------------------------------------------------------------------------
    # Mention markets
    # -------------------------------------------------------------------------
    "NBAMENTION": MarketTypeConfig(
        label="NBA Broadcast Mention Market",
        resolution_desc="YES resolves if the word/phrase `{slug}` appears in the official broadcast transcript for this NBA game.",
        risk_questions=[
            "Is the game still scheduled? Search for postponements or cancellations.",
            "What pre-game conditions make `{slug}` likely to be spoken? (injury reports, player availability, recent news — announcers will mention injuries if a key player is out or questionable)",
            "Does Kalshi's rule require the exact root word, or do plurals and variants count? (e.g., 'injury' vs 'injured' vs 'injuries') — search Kalshi rules for this ticker",
            "Which specific broadcast feed is the designated resolution source? (national vs local broadcast can differ)",
            "Have similar NBA mention markets for `{slug}` ever resolved NO unexpectedly? Search Reddit/Kalshi community for disputes on this word",
        ],
    ),
    "TRUMPMENTION": MarketTypeConfig(
        label="Trump Speech Mention Market",
        resolution_desc="YES resolves if Trump mentions `{slug}` during the specified remarks or event.",
        risk_questions=[
            "Is the speech/event still scheduled? Search for cancellations or schedule changes.",
            "What is the stated purpose of the event — does it naturally require mention of `{slug}`? (e.g., a visit to troops involved in a specific operation)",
            "Does Kalshi require an exact word match, or does a related topic reference count?",
            "Is there a confirmed transcript/video that will be used as the resolution source?",
            "Search for the most recent Trump speech transcripts to see if he has already mentioned this topic in the current window",
        ],
    ),
    "BERNIEMENTION": MarketTypeConfig(
        label="Political Figure Mention Market",
        resolution_desc="YES resolves if the specified figure mentions `{slug}` in a public appearance or broadcast.",
        risk_questions=[
            "Is the event (speech, interview, broadcast appearance) still happening as scheduled?",
            "Does the topic `{slug}` align with what the speaker is known to discuss?",
            "What is Kalshi's exact resolution source and word-matching rule?",
            "Has the word already been said earlier in the window? Search recent transcripts.",
        ],
    ),
    "PRESMENTION": MarketTypeConfig(
        label="Presidential Mention Market",
        resolution_desc="YES resolves if the president mentions `{slug}` during the specified event or within the measurement window.",
        uses_slug=True,
        risk_questions=[
            "Is the speech/event still scheduled? Check White House schedule for any changes",
            "What is the event context — does the topic `{slug}` align with the agenda?",
            "Search recent presidential speech transcripts for uses of this word/phrase",
            "What is Kalshi's exact resolution source and word-matching criteria?",
            "What is the time remaining before the event or window closes?",
        ],
    ),
    "SURVIVORMENTION": MarketTypeConfig(
        label="Survivor TV Show Mention Market",
        resolution_desc="YES resolves if `{slug}` is mentioned/occurs during the specified Survivor episode.",
        risk_questions=[
            "Is the episode still scheduled to air? Check for preemptions or schedule changes",
            "What does `{slug}` refer to in the context of this Survivor market? (word, phrase, event, or player action)",
            "What is Kalshi's exact resolution source — broadcast transcript, closed captions, or official CBS source?",
            "Search for Survivor spoiler communities for any previews or press screener leaks about this episode",
            "What happened in the prior episode that might set up this word/event appearing?",
        ],
    ),
    # -------------------------------------------------------------------------
    # Trump speech / Truth Social markets
    # -------------------------------------------------------------------------
    "TRUMPSAYMONTH": MarketTypeConfig(
        label="Trump Monthly Speech Phrase Market",
        resolution_desc="YES resolves if Trump says `{slug}` in any public remark within the specified month.",
        risk_questions=[
            "How much of the measurement window remains before close?",
            "Are there any scheduled Trump events (rallies, press conferences, signings) in the remaining window where this phrase could plausibly appear?",
            "Search recent Trump speech transcripts and Truth Social posts for the phrase — has it already been said in this window?",
            "Does Kalshi require an exact phrase match, or do paraphrases count?",
            "What is the base rate for Trump saying this phrase in a typical month?",
        ],
    ),
    "TRUMPSAY": MarketTypeConfig(
        label="Trump Exact Phrase Market",
        resolution_desc="YES resolves if Trump says `{slug}` in a public remark within the specified short window.",
        risk_questions=[
            "How much time remains before the market closes?",
            "Are there scheduled events (rallies, press gaggles, speeches, interviews) before close where this phrase could appear?",
            "Search Trump speech transcripts and Truth Social for recent uses of this phrase",
            "Kalshi resolution source: public recordings/transcripts — any ambiguity in what qualifies as 'said' (written posts vs spoken remarks)?",
            "This is a short-window prop; the key question is whether the remaining schedule makes it likely or unlikely",
        ],
    ),
    "TRUTHSOCIAL": MarketTypeConfig(
        label="Truth Social Post Count Market",
        resolution_desc="YES resolves based on Trump's post count on Truth Social during a specific week, compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "Has the measurement window (the specified week) ended yet?",
            "What does the current tracked count show? Search third-party trackers (Roll Call, Factba.se, or Coinbase prediction market pages that display counts)",
            "What does Kalshi's rule include in the count: Truths only, or also ReTruths and Quote Truths? Are deleted posts excluded?",
            "Is there any confirmed dispute or appeal on the week's final count?",
            "What has Trump's weekly posting volume been in recent weeks?",
        ],
    ),
    # -------------------------------------------------------------------------
    # Political / government markets
    # -------------------------------------------------------------------------
    "NYTHEAD": MarketTypeConfig(
        label="New York Times Headline Count Market",
        resolution_desc="YES resolves based on the number of full-width NYT front-page headlines in a specified period.",
        uses_slug=False,
        risk_questions=[
            "Has the measurement period ended? If yes, the outcome is effectively locked.",
            "What archive does Kalshi use to verify front pages? (NYT Today's Paper, Frontpages.com, Kiosko)",
            "What is Kalshi's exact definition of 'full-width headline'? This is the most likely source of dispute — search Kalshi rules for this market",
            "Search the NYT front page archive for the relevant dates to count qualifying headlines",
        ],
    ),
    "ATTENDSOTU": MarketTypeConfig(
        label="SOTU Attendance Market",
        resolution_desc="YES resolves if `{slug}` attends the State of the Union address as a named guest.",
        risk_questions=[
            "Is the SOTU still scheduled as planned? Check for date/time confirmations.",
            "Is there confirmed reporting that `{slug}` was invited and accepted?",
            "Any last-minute illness, travel issues, or scheduling conflicts reported?",
            "How does Kalshi verify attendance — live broadcast footage, pool reports, or White House guest list?",
            "What is the time remaining before the event — has the SOTU already occurred?",
        ],
    ),
    "GOVSHUT": MarketTypeConfig(
        label="Government Shutdown / Funding Market",
        resolution_desc="YES resolves based on whether the federal government is shut down or funded at a specific date/time.",
        uses_slug=False,
        risk_questions=[
            "What is the exact legal trigger — when does the current CR/appropriations expire?",
            "Search for the latest vote counts, Senate floor scheduling, and leadership statements",
            "What procedural paths exist to avoid shutdown (split bills, unanimous consent, short CR)? Are any of these actively being pursued?",
            "Search for the most recent Congressional statements and roll call positions",
            "What is the historical base rate for last-minute funding resolutions?",
        ],
    ),
    "PRESNOMFEDCHAIR": MarketTypeConfig(
        label="Presidential Nomination Market",
        resolution_desc="YES resolves if Trump announces a specific nominee within the specified window.",
        uses_slug=False,
        risk_questions=[
            "Are there any credible news reports of an imminent announcement?",
            "What does the White House schedule show for the remaining window?",
            "Has a frontrunner been reported by credible outlets (WSJ, Reuters, Bloomberg)?",
            "What is the precedent for how quickly these announcements follow reported shortlists?",
            "Is there any White House statement ruling out an announcement in this window?",
        ],
    ),
    "KHAMENEI": MarketTypeConfig(
        label="Political Leader Departure Market",
        resolution_desc="YES resolves if the specified leader leaves office before the deadline.",
        uses_slug=False,
        risk_questions=[
            "What is the leader's most recent documented public appearance? (confirms still active)",
            "What is the constitutional/legal mechanism for departure — death, resignation, removal? How recently have any of these been plausible?",
            "What is the historical base rate for departures of this type of leader?",
            "Search for the latest health reporting, political stability reporting, or institutional moves that could indicate an imminent change",
            "How much time remains in the window?",
        ],
    ),
    # -------------------------------------------------------------------------
    # Economics markets
    # -------------------------------------------------------------------------
    "PAYROLLS": MarketTypeConfig(
        label="Nonfarm Payrolls Market",
        resolution_desc="YES resolves on the BLS Employment Situation headline number compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "Is the BLS release still scheduled for the expected date? Search for any government shutdown delays (BLS delays releases during funding lapses — this has happened in 2026)",
            "What does the ADP National Employment Report show for this period?",
            "What are weekly initial jobless claims trending? (proxy for labor market health)",
            "Are there seasonal adjustment or benchmark revision effects that could push the headline above/below the threshold independently of actual hiring?",
            "What is the Bloomberg/Reuters economist consensus for this month's print?",
        ],
    ),
    "JOBLESSCLAIMS": MarketTypeConfig(
        label="Initial Jobless Claims Market",
        resolution_desc="YES resolves on the DOL seasonally-adjusted initial claims figure for the specified week compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "Is the DOL Weekly Claims release still on schedule? Search for shutdown delays (BLS/DOL delay releases during funding lapses)",
            "What were the prior 2-3 weeks of initial claims? (trend direction and whether a one-week reversal could breach the threshold)",
            "What does the 4-week moving average show relative to the strike? (cushion size)",
            "This market closes ~5 minutes BEFORE the data release — confirm the exact close time vs. the 8:30 AM ET release time, since early releases can affect the price",
            "Are there any known seasonal adjustment methodology changes or benchmark revisions for this period?",
            "Search for analyst consensus estimates for this week's claims print",
        ],
    ),
    "KXU3": MarketTypeConfig(
        label="Unemployment Rate (U-3) Market",
        resolution_desc="YES resolves on the BLS U-3 unemployment rate for the specified month compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "Is the BLS Employment Situation release still on schedule? Search for shutdown delays (BLS has delayed releases during 2026 government funding lapses)",
            "What do recent labor market data points (ADP, initial claims, JOLTS) suggest about the direction of unemployment?",
            "What is the economist consensus for this month's U-3 rate?",
            "U-3 is derived from the household survey — is there any unusual household survey methodology note for this period?",
            "What has U-3 been in the preceding 2-3 months? (trending direction matters)",
        ],
    ),
    "GDP": MarketTypeConfig(
        label="GDP Growth Market",
        resolution_desc="YES resolves on the BEA's GDP advance/revised estimate for the specified quarter compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the latest GDPNow estimate from the Atlanta Fed?",
            "What does the Philadelphia Fed Survey of Professional Forecasters show?",
            "What is the spread between nowcast models (Atlanta Fed often diverges from consensus)? A wide spread signals high uncertainty.",
            "Which BEA release (advance, second, third estimate) does the market use? The advance estimate comes first and can differ significantly from later revisions",
            "Is the BEA release still on schedule, or could a government shutdown delay it?",
        ],
    ),
    "CPI": MarketTypeConfig(
        label="CPI Inflation Market",
        resolution_desc="YES resolves on the BLS CPI year-over-year rate for the specified month compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What does the Cleveland Fed's Inflation Nowcasting model show?",
            "What are the recent monthly trends in shelter/OER (owners' equivalent rent — the single largest CPI component and biggest source of upside surprise)?",
            "What does the economist consensus show for this month's YoY CPI?",
            "Is the BLS release still on schedule? (government shutdown risk applies)",
            "Are there any known methodological changes or unusual seasonal adjustments for this specific CPI release?",
        ],
    ),
    "EHSALES": MarketTypeConfig(
        label="Existing Home Sales Market",
        resolution_desc="YES resolves on the NAR existing home sales figure (SAAR) for the specified month compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the economist consensus for this month's existing home sales?",
            "NAR releases existing home sales data around the 20th-25th of the following month at 10:00 AM ET",
            "What do pending home sales (a leading indicator) show for this period?",
            "What are current mortgage rates? Higher rates suppress sales volume",
            "Any seasonal adjustment changes or methodology notes for this release?",
        ],
    ),
    "ARMOMINF": MarketTypeConfig(
        label="Argentina Monthly Inflation Market",
        resolution_desc="YES resolves on the INDEC-reported Argentina CPI monthly inflation rate compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is INDEC's scheduled release date for this month's CPI?",
            "What do private-sector inflation trackers (consultoras) estimate for this month?",
            "What is the trend — has monthly inflation been decelerating under Milei's stabilization program?",
            "Any FX devaluation events (crawling peg adjustments) that would push CPI higher?",
            "What was the prior month's MoM CPI? (baseline for trend)",
        ],
    ),
    # -------------------------------------------------------------------------
    # Commodities / energy markets
    # -------------------------------------------------------------------------
    "WTIW": MarketTypeConfig(
        label="WTI Oil Price Market",
        resolution_desc="YES resolves on the official NYMEX/CME WTI front-month daily settlement price compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current WTI front-month futures price? (distance from threshold)",
            "CME settles WTI at 2:28-2:30 PM ET — the market resolves at that specific settlement print, not intraday high/low",
            "What are the latest EIA weekly inventory numbers? (builds are bearish, draws are bullish for price)",
            "What is the OPEC+ production stance? Any recent meeting decisions or voluntary cut changes?",
            "Any geopolitical disruptions (Iran, Venezuela, Russia) currently affecting supply?",
            "Any short-term weather/infrastructure events affecting production?",
        ],
    ),
    "BRENTD": MarketTypeConfig(
        label="Brent Crude Daily Price Market",
        resolution_desc="YES resolves on the Brent crude close price (USD/bbl) at 5:00 PM ET on the specified date compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current Brent front-month futures price and distance from threshold?",
            "What price source does Kalshi use — ICE Brent settlement or spot at 5 PM ET?",
            "What is the Brent-WTI spread? Geopolitical events affect Brent more than WTI",
            "Any OPEC+ production decisions, Middle East disruptions, or sanctions news?",
            "Time remaining until the 5 PM ET snapshot?",
        ],
    ),
    "AAAGASM": MarketTypeConfig(
        label="National Gas Price Market",
        resolution_desc="YES resolves on the national average retail gasoline price compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current AAA national average? (gasprices.aaa.com)",
            "What series does Kalshi use for resolution: AAA, EIA weekly all-grades, or EIA regular grade? These can differ by 10-15 cents — this is critical",
            "What does the latest EIA Weekly Petroleum Status Report show for gasoline inventories and refinery utilization?",
            "What has WTI crude been doing? Retail prices lag crude by ~1-2 weeks",
            "Any regional refinery outages or weather disruptions affecting the national average?",
        ],
    ),
    "GOLDD": MarketTypeConfig(
        label="Gold Daily Price Market",
        resolution_desc="YES resolves on the gold close price (USD/troy oz) at 5:00 PM ET on the specified date compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current gold spot price and distance from threshold?",
            "What price source does Kalshi use — COMEX settlement, LBMA fix, or spot at 5 PM ET?",
            "Gold is a safe-haven asset — any macro risk events (Fed announcements, geopolitical escalation) that could cause a large move?",
            "What is the USD/DXY doing? Gold moves inversely to the dollar",
            "Any central bank gold buying/selling news?",
            "Time remaining until the 5 PM ET snapshot?",
        ],
    ),
    # -------------------------------------------------------------------------
    # FOMC / monetary policy
    # -------------------------------------------------------------------------
    "FOMC": MarketTypeConfig(
        label="FOMC Dissent Count Market",
        resolution_desc="YES resolves on the number of dissenting votes at the specified FOMC meeting.",
        uses_slug=False,
        risk_questions=[
            "Has the FOMC meeting already occurred? If yes, what was the vote tally?",
            "What was the dissent count at the prior meeting? (sets the baseline)",
            "Who are the rotating voting members for this meeting? (FOMC voter roster changes)",
            "What public speeches have voting members given recently signaling hawkish/dovish positions?",
            "The dissent count is revealed immediately when the FOMC statement is issued — what is the scheduled statement release time?",
        ],
    ),
    # -------------------------------------------------------------------------
    # Travel / transportation
    # -------------------------------------------------------------------------
    "TSAW": MarketTypeConfig(
        label="TSA Passenger Volume Market",
        resolution_desc="YES resolves on the TSA's published weekly average passenger screening count compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What are TSA's published daily throughput numbers so far this week? (tsa.gov/travel/passenger-volumes publishes daily counts)",
            "How many days of the measurement window remain?",
            "Are there any ongoing weather events, FAA ground stops, or travel disruptions that could suppress volumes for multiple days?",
            "What is the prior-week average for comparison?",
            "Does Kalshi include all 7 days, or a specific subset? Check market rules",
        ],
    ),
    # -------------------------------------------------------------------------
    # Crypto markets
    # -------------------------------------------------------------------------
    "BTC": MarketTypeConfig(
        label="Bitcoin Price Market",
        resolution_desc="YES resolves on the BTC/USD price at a specific timestamp compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current BTC spot price and how far is it from the threshold?",
            "What specific exchange or index does Kalshi use for settlement? (Coinbase, CME reference rate, or a composite — this determines the exact price used)",
            "What is the time remaining until settlement? BTC is highly volatile intraday",
            "Any major crypto news events (ETF flows, exchange hacks, regulatory news, macro risk-off events) that could cause a large move before settlement?",
            "What does the options market (Deribit) imply about near-term volatility?",
        ],
    ),
    "ETH": MarketTypeConfig(
        label="Ethereum Price Market",
        resolution_desc="YES resolves on the ETH/USD price at Kalshi's snapshot time (typically 5:00 PM ET) compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current ETH spot price and how far is it from the threshold?",
            "What specific price source does Kalshi use for ETH settlement? (exchange, index, or composite)",
            "What is the time remaining until settlement? ETH volatility can be extreme intraday",
            "Any major Ethereum ecosystem news (network upgrades, DeFi exploits, ETF flows) that could cause a large move?",
            "What is the ETH/BTC correlation doing? BTC moves often drag ETH",
            "Check ETH options implied volatility on Deribit for expected move magnitude",
        ],
    ),
    "SOL": MarketTypeConfig(
        label="Solana Price Market",
        resolution_desc="YES resolves on the SOL/USD price at Kalshi's snapshot time compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current SOL spot price and distance from threshold?",
            "What price source does Kalshi use for SOL settlement?",
            "Time remaining until settlement? SOL is highly volatile",
            "Any Solana network issues (outages, congestion) or ecosystem news that could move price?",
            "SOL often moves with higher beta than BTC — what is BTC doing?",
        ],
    ),
    "XRP": MarketTypeConfig(
        label="Ripple (XRP) Price Market",
        resolution_desc="YES resolves on the XRP/USD price at Kalshi's snapshot time compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current XRP spot price and distance from threshold?",
            "What price source does Kalshi use for XRP settlement?",
            "Any Ripple/SEC legal developments or XRP ETF news that could cause outsized moves?",
            "Time remaining until settlement?",
            "XRP has historically lower correlation with BTC than other alts — check XRP-specific catalysts",
        ],
    ),
    "DOGE": MarketTypeConfig(
        label="Dogecoin Price Market",
        resolution_desc="YES resolves on the DOGE/USD price at Kalshi's snapshot time compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current DOGE spot price and distance from threshold?",
            "What price source does Kalshi use for DOGE settlement?",
            "DOGE is heavily sentiment-driven — any Elon Musk tweets or meme catalysts?",
            "Time remaining until settlement?",
            "DOGE volatility is extreme; even 95+ cent contracts can flip on a single social media post",
        ],
    ),
    # -------------------------------------------------------------------------
    # Weather markets
    # -------------------------------------------------------------------------
    "HIGHTEMP": MarketTypeConfig(
        label="Daily High Temperature Market",
        resolution_desc="YES resolves based on the daily high temperature at the specified city's NWS weather station compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What does the NWS point forecast show for the high temp at this station on the target date?",
            "Kalshi resolves off the NWS Daily Climate Report (CLI) — this uses LOCAL STANDARD TIME year-round, which shifts the measurement window during DST",
            "What do the GFS/ECMWF/HRRR ensemble models show? Check spread between models for uncertainty",
            "Is the threshold near the forecast or is there a comfortable margin?",
            "Any frontal passages, cloud cover changes, or precipitation expected that could suppress the high?",
            "NWS CLI reports can occasionally be delayed or revised — has this happened recently for this station?",
        ],
    ),
    "LOWTEMP": MarketTypeConfig(
        label="Daily Low Temperature Market",
        resolution_desc="YES resolves based on the daily low temperature at the specified city's NWS weather station compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What does the NWS point forecast show for the low temp at this station on the target date?",
            "Kalshi resolves off the NWS Daily Climate Report (CLI) using LOCAL STANDARD TIME year-round",
            "What do ensemble models (GFS/ECMWF/HRRR) show for overnight lows? Check model spread",
            "Is the threshold near the forecast or is there a comfortable margin?",
            "Cloud cover overnight acts as insulation (raises lows); clear skies allow radiative cooling (lowers lows) — what is the cloud forecast?",
            "Any wind events expected? Wind prevents radiative cooling and keeps lows higher",
        ],
    ),
    "RAIN": MarketTypeConfig(
        label="Rain / Precipitation Market",
        resolution_desc="YES resolves based on precipitation recorded at the NWS weather station for the specified city and period.",
        uses_slug=False,
        risk_questions=[
            "What does the NWS point forecast show for precipitation probability and amount?",
            "Kalshi resolves off NWS Daily Climate Report (CLI) or NOWData monthly totals — confirm which",
            "What do radar and model QPF (quantitative precipitation forecasts) show?",
            "Is the threshold a daily total or a monthly cumulative? Monthly markets can swing with a single heavy rain day",
            "For daily rain markets: precipitation timing matters — does the measurement window cover the full calendar day in local standard time?",
        ],
    ),
    # -------------------------------------------------------------------------
    # Sports markets
    # -------------------------------------------------------------------------
    "NBAGAME": MarketTypeConfig(
        label="NBA Game Winner Market",
        resolution_desc="YES resolves if `{slug}` wins the specified game.",
        risk_questions=[
            "Is the game still scheduled? Search for postponements or rescheduling.",
            "What is the latest official NBA injury report for both teams? (nba.com/news and ESPN injury reports — check for star player availability)",
            "What are the current sportsbook moneylines (DraftKings, FanDuel, BetMGM)? A large spread between Kalshi and sportsbooks signals mispricing risk",
            "Is either team on a back-to-back? (fatigue affects win probability)",
            "Recent head-to-head record and season records for both teams",
            "Any key lineup/rotation changes (resting stars, load management)?",
        ],
    ),
    "NBATOTAL": MarketTypeConfig(
        label="NBA Game Total Market",
        resolution_desc="YES resolves if the combined final score exceeds the specified threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the latest injury/availability status for high-usage players on both teams? (A key player out significantly changes expected total)",
            "What are the current sportsbook over/under lines for this game?",
            "What are both teams' offensive and defensive ratings this season, and do the numbers change materially with key players absent?",
            "What is the recent pace-of-play for both teams?",
            "Is either team on a back-to-back or in a stretch of fatigue?",
        ],
    ),
    "NBATRADE": MarketTypeConfig(
        label="NBA Trade Market",
        resolution_desc="YES resolves if `{slug}` is traded before the deadline.",
        risk_questions=[
            "What does the latest insider reporting say? (ESPN's Shams Charania, Athletic's Wojnarowski — these are the authoritative sources)",
            "Has the team's front office publicly confirmed or denied trade interest?",
            "What is the player's current injury/availability status? (injuries reduce trade value and complicate medical clearances)",
            "What assets would a realistic trade package require, and which teams have the cap space and picks to execute?",
            "How much time remains before the NBA trade deadline (Feb 6)?",
            "What did the player say publicly about their situation?",
        ],
    ),
    "NEXTTEAM": MarketTypeConfig(
        label="NBA Player Destination Market",
        resolution_desc="YES resolves if the player's next team is `{slug}`.",
        risk_questions=[
            "What does the latest insider reporting say about the player's preferred destination?",
            "Has the team (`{slug}`) been specifically named by credible reporters as an active suitor with real offer capacity?",
            "What are the asset/cap constraints for `{slug}` — do they have the picks and players to match salary?",
            "Is the player's current team open to trading now vs. waiting for the offseason?",
            "What is the player's current injury status and contract situation?",
        ],
    ),
    "NCAAMBGAME": MarketTypeConfig(
        label="NCAA Men's Basketball Game Market",
        resolution_desc="YES resolves if `{slug}` wins.",
        risk_questions=[
            "Is the game still scheduled? College games are occasionally postponed.",
            "What are the current KenPom/NET rankings and win probabilities for both teams?",
            "What do available sportsbook lines show?",
            "Any reported injury or eligibility issues for key players on either team?",
            "Is this a home/away/neutral site game? Home court matters significantly in college basketball",
        ],
    ),
    "NCAABBGAME": MarketTypeConfig(
        label="NCAA Women's Basketball Game Market",
        resolution_desc="YES resolves if `{slug}` wins.",
        risk_questions=[
            "Is the game still scheduled? Any postponements or venue changes?",
            "What are the NET rankings and season records for both teams?",
            "Any reported injury issues for key players?",
            "Home/away/neutral site?",
            "What do available betting markets show for this matchup?",
        ],
    ),
    "MLBSTGAME": MarketTypeConfig(
        label="MLB Game Market",
        resolution_desc="YES resolves based on the official MLB box score winner.",
        uses_slug=False,
        risk_questions=[
            "Is this a spring training game? Spring training lineups are experimental — starters may be pulled early, prospects may play, and rosters change daily",
            "Is the game still scheduled? Spring training games are more frequently cancelled or shortened due to weather or logistics",
            "Does Kalshi count a suspended/shortened game as a completed result?",
            "For regular season: who is starting (pitching matchup is the primary driver)?",
            "What are current sportsbook moneylines?",
            "Any injury/roster news affecting the lineup?",
        ],
    ),
    "WBCGAME": MarketTypeConfig(
        label="World Baseball Classic Game Market",
        resolution_desc="YES resolves based on the official WBC game result.",
        uses_slug=False,
        risk_questions=[
            "Is the game still scheduled? WBC games can be affected by weather or scheduling changes",
            "Which MLB players are participating for each team? (roster construction is the key variable)",
            "What stage is this (pool play, elimination, semifinal, final)? Tiebreaker rules differ",
            "What are sportsbook odds for this matchup?",
            "WBC uses different rules than MLB (pitch counts, mercy rule) — do these affect resolution?",
        ],
    ),
    "NASCARRACE": MarketTypeConfig(
        label="NASCAR Race Winner Market",
        resolution_desc="YES resolves if `{slug}` wins the race.",
        risk_questions=[
            "Has the race started or finished yet? Search for the current race status.",
            "If pre-race: what do practice/qualifying results show for `{slug}`?",
            "What are the current sportsbook odds for `{slug}` to win?",
            "NASCAR fields are large (30-40 cars) — a single driver NOT winning is structurally likely; understand the direction of this market (YES or NO)",
            "Any mechanical issues, crash news, or weather delays reported?",
            "What track type is this? (superspeedway vs road course vs oval — different tracks suit different drivers)",
        ],
    ),
    "INDYCARRACE": MarketTypeConfig(
        label="IndyCar Race Winner Market",
        resolution_desc="YES resolves if `{slug}` wins the race.",
        risk_questions=[
            "Has the race started or finished? Search for official IndyCar race results.",
            "If pre-race: what do practice times and qualifying show?",
            "What are sportsbook odds for `{slug}`?",
            "IndyCar fields are large — understand the direction (YES vs NO side)",
            "Any reported mechanical issues, crashes, or weather delays?",
            "Street circuits (like St. Petersburg) favor specific car setups and teams",
        ],
    ),
    "WOHOCKEY": MarketTypeConfig(
        label="Olympic Ice Hockey Market",
        resolution_desc="YES resolves if `{slug}` wins the gold medal.",
        risk_questions=[
            "What stage is the tournament at? Search for current bracket results.",
            "What do sportsbooks currently price for `{slug}` gold? (DraftKings, FanDuel — compare to Kalshi price)",
            "What is `{slug}`'s group composition and path to the final?",
            "Are NHL stars participating? (full NHL participation changes relative strength)",
            "Any injury/roster news for `{slug}` or their likely medal round opponents?",
            "What recent best-on-best international results exist (4 Nations, World Championships)?",
        ],
    ),
    "AOMEN": MarketTypeConfig(
        label="Australian Open ATP Market",
        resolution_desc="YES resolves if `{slug}` wins the title.",
        risk_questions=[
            "Where is `{slug}` in the draw right now? Search for current match results.",
            "What is `{slug}`'s current physical status? (injuries, blisters, match load — check post-match press conference reports)",
            "Who are the remaining opponents and what is the H2H history?",
            "What do current sportsbook odds show for `{slug}` to win the title?",
            "How many matches has `{slug}` played vs opponents (fatigue differential)?",
            "Did `{slug}` receive any walkovers/retirements that reduced match load?",
        ],
    ),
    "AOWOMEN": MarketTypeConfig(
        label="Australian Open WTA Market",
        resolution_desc="YES resolves if `{slug}` wins the title.",
        risk_questions=[
            "Where is `{slug}` in the draw right now? Search for current match results.",
            "What is `{slug}`'s current physical status? (injuries, blisters, match load — check post-match press conference reports)",
            "Who are the remaining opponents and what is the H2H history?",
            "What do current sportsbook odds show for `{slug}` to win the title?",
            "How many matches has `{slug}` played vs opponents (fatigue differential)?",
            "Did `{slug}` receive any walkovers/retirements that reduced match load?",
        ],
    ),
    # -------------------------------------------------------------------------
    # Entertainment markets
    # -------------------------------------------------------------------------
    "NETFLIXRANK": MarketTypeConfig(
        label="Netflix Ranking Market",
        resolution_desc="YES resolves based on a specific title's position in Netflix's official Top 10 for a specified date.",
        risk_questions=[
            "Check FlixPatrol (flixpatrol.com) for the current Netflix Top 10 — this is the primary data source used for resolution",
            "Is the ranking for a specific date (daily) or a weekly aggregate?",
            "Is `{slug}` currently trending up or down? New episodes or press coverage drive rapid ranking changes",
            "Is this the US ranking or the global ranking? They can differ significantly",
            "What new content dropped this week that could displace `{slug}`?",
        ],
    ),
    "TOPSONG": MarketTypeConfig(
        label="Billboard Chart Market",
        resolution_desc="YES resolves based on `{slug}`'s position on the Billboard Hot 100 or Albums chart for the specified week.",
        risk_questions=[
            "What does the current Luminate/Billboard tracking show for `{slug}`? (Chart analysts publish midweek tracking data)",
            "What songs/albums are above `{slug}` this week?",
            "Billboard weights streaming (most), airplay, and sales — which factor is `{slug}` strongest in?",
            "When does the chart week end and when is the new chart published?",
            "Is there a major competitor release this week that could push `{slug}` down?",
        ],
    ),
    "FIRSTSUPERBOWLSONG": MarketTypeConfig(
        label="Super Bowl Halftime Setlist Market",
        resolution_desc="YES resolves based on which song is performed first during the halftime show.",
        uses_slug=False,
        risk_questions=[
            "What song does the official Apple Music/NFL promotional trailer feature? (trailers typically signal the show's featured tracks)",
            "What has the artist's recent tour setlist looked like — specifically which song opens the show? (JamBase, Setlist.fm for recent concert setlists)",
            "Have any rehearsal reports or setlist leaks emerged? (these typically surface 1-7 days before the game)",
            "Halftime shows often differ from tour setlists — the show is ~12-15 minutes and goes through major revisions up to game week",
            "Search for any credible insider or production crew reports about the opening",
        ],
    ),
    "SUPERBOWLAD": MarketTypeConfig(
        label="Super Bowl Advertiser Market",
        resolution_desc="YES resolves if `{slug}` runs a national in-game ad during the Super Bowl broadcast.",
        risk_questions=[
            "Check Ad Age, Adweek, Marketing Dive, and iSpot.tv advertiser trackers — these publish confirmed advertisers in the weeks before the game",
            "Has `{slug}` confirmed a Super Bowl buy, or is it only reported/rumored?",
            "Did `{slug}` advertise during prior Super Bowls? (prior participation is the strongest predictor)",
            "Does Kalshi count national broadcast spots only, or also streaming/Peacock breaks?",
            "A Peacock-only or regional buy would NOT count as a national Super Bowl ad under most resolution rules",
        ],
    ),
    "KXRT": MarketTypeConfig(
        label="Rotten Tomatoes Score Market",
        resolution_desc="YES resolves based on the Rotten Tomatoes Tomatometer score for the specified film at the specified time.",
        uses_slug=False,
        risk_questions=[
            "What is the current Tomatometer score and how many reviews are counted?",
            "Scores stabilize after ~100+ reviews — early scores with <30 reviews are highly volatile",
            "When does the measurement window close? Late reviews can shift the score",
            "Is this the critics score (Tomatometer) or audience score? They differ significantly",
            "Major franchise films tend to have predictable score ranges — what are comparable films rated?",
        ],
    ),
    # -------------------------------------------------------------------------
    # AI / tech markets
    # -------------------------------------------------------------------------
    "TOPMODEL": MarketTypeConfig(
        label="AI Model Rankings Market",
        resolution_desc="YES resolves based on `{slug}` being the top-ranked AI model per Kalshi's specified benchmark.",
        risk_questions=[
            "Which specific leaderboard does Kalshi use for resolution? (LMSYS Chatbot Arena, Scale HELM, HuggingFace Open LLM — these differ significantly)",
            "What is the current ranking of `{slug}` on the relevant leaderboard?",
            "Have any major model releases been announced or dropped in the measurement window?",
            "Does the leaderboard update in real-time or on a fixed schedule?",
            "What is the close date — could a new release change rankings before then?",
        ],
    ),
    "SPACEXCOUNT": MarketTypeConfig(
        label="SpaceX Launch Count Market",
        resolution_desc="YES resolves based on SpaceX's total launch count for the specified year compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is SpaceX's current launch count for the year? (Spaceflight Now, NASASpaceflight.com maintain running tallies)",
            "What upcoming launches are on the manifest before year-end?",
            "Are any upcoming launches at risk of delay (FAA license, weather, hardware)?",
            "Does Kalshi count Falcon 9, Falcon Heavy, and Starship separately or combined?",
            "What was SpaceX's launch cadence in prior comparable periods?",
        ],
    ),
}

FALLBACK = MarketTypeConfig(
    label="General Market",
    resolution_desc="Research what specifically triggers YES resolution and whether any current conditions threaten that outcome.",
    uses_slug=False,
    risk_questions=[
        "What is the exact determining event and has it occurred yet?",
        "Is the event still on schedule, or are there disruption risks?",
        "What are Kalshi's exact resolution criteria — which source, which measurement?",
        "What is the latest publicly available data or news directly relevant to this outcome?",
        "What is the strongest current argument that YES will NOT resolve?",
        "Are there any known disputes, appeals, or rule ambiguities for this market type?",
    ],
)

ALIASES: dict[str, str] = {
    # Government / political aliases
    "GOVTFUND": "GOVSHUT",
    "FEDCHAIR": "PRESNOMFEDCHAIR",
    "SOTU": "ATTENDSOTU",
    # FOMC aliases
    "FOMCDISSENT": "FOMC",
    # Oil / gas aliases
    "WTID": "WTIW",
    "WTI": "WTIW",
    "AAAGASW": "AAAGASM",
    "AAAGASD": "AAAGASM",
    # Crypto aliases
    "BTCD": "BTC",
    "BTC15M": "BTC",
    "ETHD": "ETH",
    "ETH15M": "ETH",
    "SOLD": "SOL",
    "SOLE": "SOL",
    "SOL15M": "SOL",
    "XRPD": "XRP",
    "XRP15M": "XRP",
    "DOGED": "DOGE",
    # Entertainment aliases
    "TOPALBUM": "TOPSONG",
    "SUPERBOWLHALFTIME": "FIRSTSUPERBOWLSONG",
    # Unemployment alternative ticker
    "ECONSTATU3": "KXU3",
    # Weather high-temp city aliases (KXHIGH* and KXHIGHT* variants)
    "HIGHAUS": "HIGHTEMP",
    "HIGHCHI": "HIGHTEMP",
    "HIGHDEN": "HIGHTEMP",
    "HIGHLAX": "HIGHTEMP",
    "HIGHMIA": "HIGHTEMP",
    "HIGHNY": "HIGHTEMP",
    "HIGHPHIL": "HIGHTEMP",
    "HIGHTATL": "HIGHTEMP",
    "HIGHTBOS": "HIGHTEMP",
    "HIGHTDAL": "HIGHTEMP",
    "HIGHTDC": "HIGHTEMP",
    "HIGHTHOU": "HIGHTEMP",
    "HIGHTLV": "HIGHTEMP",
    "HIGHTMIN": "HIGHTEMP",
    "HIGHTNOLA": "HIGHTEMP",
    "HIGHTOKC": "HIGHTEMP",
    "HIGHTPHX": "HIGHTEMP",
    "HIGHTSATX": "HIGHTEMP",
    "HIGHTSEA": "HIGHTEMP",
    "HIGHTSFO": "HIGHTEMP",
    # Weather low-temp city aliases
    "LOWTATL": "LOWTEMP",
    "LOWTAUS": "LOWTEMP",
    "LOWTBOS": "LOWTEMP",
    "LOWTCHI": "LOWTEMP",
    "LOWTDAL": "LOWTEMP",
    "LOWTDC": "LOWTEMP",
    "LOWTDEN": "LOWTEMP",
    "LOWTHOU": "LOWTEMP",
    "LOWTLAX": "LOWTEMP",
    "LOWTLV": "LOWTEMP",
    "LOWTMIA": "LOWTEMP",
    "LOWTMIN": "LOWTEMP",
    "LOWTNOLA": "LOWTEMP",
    "LOWTNYC": "LOWTEMP",
    "LOWTOKC": "LOWTEMP",
    "LOWTPHIL": "LOWTEMP",
    "LOWTPHX": "LOWTEMP",
    "LOWTSATX": "LOWTEMP",
    "LOWTSEA": "LOWTEMP",
    "LOWTSFO": "LOWTEMP",
    # Rain aliases
    "RAINNYC": "RAIN",
    "RAINM": "RAIN",
}
