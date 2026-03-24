"""Market-type-specific research context for the Researcher agent.

Maps a market ticker/event to a tailored risk checklist injected into the
research prompt. Each branch covers a distinct Kalshi market category observed
across historical and live opportunity data.

Data-driven: each market type is a dict entry with a label, resolution
description template, and a list of risk questions. Adding a new market type
is a single dict insertion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from coliseum.storage.files import OpportunitySignal


def _slug(ticker: str) -> str:
    """Extract the trailing slug from a hyphenated ticker."""
    parts = ticker.split("-")
    return parts[-1] if len(parts) > 1 else "unknown"


@dataclass(frozen=True)
class MarketTypeConfig:
    """Definition for one market-type research context."""

    label: str
    resolution_desc: str
    risk_questions: list[str] = field(default_factory=list)
    uses_slug: bool = True


MARKET_TYPES: dict[str, MarketTypeConfig] = {
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
    "WTIW": MarketTypeConfig(
        label="WTI Oil Price Market",
        resolution_desc="YES resolves on the official NYMEX/CME WTI front-month daily settlement price compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current WTI front-month futures price? (distance from threshold)",
            "CME settles WTI at 2:28–2:30 PM ET — the market resolves at that specific settlement print, not intraday high/low",
            "What are the latest EIA weekly inventory numbers? (builds are bearish, draws are bullish for price)",
            "What is the OPEC+ production stance? Any recent meeting decisions or voluntary cut changes?",
            "Any geopolitical disruptions (Iran, Venezuela, Russia) currently affecting supply?",
            "Any short-term weather/infrastructure events affecting production?",
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
    "BTC": MarketTypeConfig(
        label="Bitcoin Price Market",
        resolution_desc="YES resolves on the BTC spot price at a specific timestamp compared to a threshold.",
        uses_slug=False,
        risk_questions=[
            "What is the current BTC spot price and how far is it from the threshold?",
            "What specific exchange or index does Kalshi use for settlement? (Coinbase, CME reference rate, or a composite — this determines the exact price used)",
            "What is the time remaining until settlement? BTC is highly volatile intraday",
            "Any major crypto news events (ETF flows, exchange hacks, regulatory news, macro risk-off events) that could cause a large move before settlement?",
            "What does the options market (Deribit) imply about near-term volatility?",
        ],
    ),
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

_FALLBACK = MarketTypeConfig(
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

# Aliases for tickers that share a market-type config
_ALIASES: dict[str, str] = {
    "GOVTFUND": "GOVSHUT",
    "FEDCHAIR": "PRESNOMFEDCHAIR",
    "SOTU": "ATTENDSOTU",
    "FOMCDISSENT": "FOMC",
    "WTID": "WTIW",
    "AAAGASW": "AAAGASM",
    "BTCD": "BTC",
    "TOPALBUM": "TOPSONG",
    "SUPERBOWLHALFTIME": "FIRSTSUPERBOWLSONG",
}


def _match_market_type(event: str) -> MarketTypeConfig:
    """Find the best matching MarketTypeConfig for an uppercased event ticker."""
    for key in MARKET_TYPES:
        if key in event:
            return MARKET_TYPES[key]
    for alias, canonical in _ALIASES.items():
        if alias in event:
            return MARKET_TYPES[canonical]
    # Special compound match: BERNIE + MENTION
    if "MENTION" in event and "BERNIE" in event:
        return MARKET_TYPES["BERNIEMENTION"]
    # Special compound match: political leader departure
    if "OUT" in event and any(x in event for x in ("LEADER", "PRES")):
        return MARKET_TYPES["KHAMENEI"]
    # MLB generic
    if "MLB" in event and "GAME" in event:
        return MARKET_TYPES["MLBSTGAME"]
    # Olympics hockey
    if "HOCKEY" in event and "OLYMPIC" in event:
        return MARKET_TYPES["WOHOCKEY"]
    return _FALLBACK


def _format_context(config: MarketTypeConfig, slug: str) -> str:
    """Render a MarketTypeConfig into the prompt text injected for the Researcher."""
    desc = config.resolution_desc.format(slug=slug)
    questions = "\n".join(f"- {q.format(slug=slug)}" for q in config.risk_questions)
    return f"**{config.label}** — {desc}\n\nSpecific risks to investigate:\n{questions}"


def get_market_type_context(opportunity: OpportunitySignal) -> str:
    """Return market-type-specific research guidance based on the ticker."""
    event = opportunity.event_ticker.upper()
    config = _match_market_type(event)
    slug = _slug(opportunity.market_ticker.upper()) if config.uses_slug else ""
    return _format_context(config, slug)
