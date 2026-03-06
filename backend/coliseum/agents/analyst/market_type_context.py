"""Market-type-specific research context for the Researcher agent.

Maps a market ticker/event to a tailored risk checklist injected into the
research prompt. Each branch covers a distinct Kalshi market category observed
across historical and live opportunity data.
"""

from coliseum.storage.files import OpportunitySignal


def get_market_type_context(opportunity: OpportunitySignal) -> str:
    """Return market-type-specific research guidance based on the ticker."""
    ticker = opportunity.market_ticker.upper()
    event = opportunity.event_ticker.upper()

    # --- Mention Markets ---

    if "NBAMENTION" in event:
        parts = ticker.split("-")
        mention_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**NBA Broadcast Mention Market** — YES resolves if the word/phrase `{mention_slug}` "
            f"appears in the official broadcast transcript for this NBA game.\n\n"
            f"Specific risks to investigate:\n"
            f"- Is the game still scheduled? Search for postponements or cancellations.\n"
            f"- What pre-game conditions make `{mention_slug}` likely to be spoken? "
            f"(injury reports, player availability, recent news — announcers will mention injuries "
            f"if a key player is out or questionable)\n"
            f"- Does Kalshi's rule require the exact root word, or do plurals and variants count? "
            f"(e.g., 'injury' vs 'injured' vs 'injuries') — search Kalshi rules for this ticker\n"
            f"- Which specific broadcast feed is the designated resolution source? "
            f"(national vs local broadcast can differ)\n"
            f"- Have similar NBA mention markets for `{mention_slug}` ever resolved NO unexpectedly? "
            f"Search Reddit/Kalshi community for disputes on this word"
        )

    if "TRUMPMENTION" in event:
        parts = ticker.split("-")
        mention_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Trump Speech Mention Market** — YES resolves if Trump mentions `{mention_slug}` "
            f"during the specified remarks or event.\n\n"
            f"Specific risks to investigate:\n"
            f"- Is the speech/event still scheduled? Search for cancellations or schedule changes.\n"
            f"- What is the stated purpose of the event — does it naturally require mention of "
            f"`{mention_slug}`? (e.g., a visit to troops involved in a specific operation)\n"
            f"- Does Kalshi require an exact word match, or does a related topic reference count?\n"
            f"- Is there a confirmed transcript/video that will be used as the resolution source?\n"
            f"- Search for the most recent Trump speech transcripts to see if he has already "
            f"mentioned this topic in the current window"
        )

    if "BERNIEMENTION" in event or ("MENTION" in event and "BERNIE" in event):
        parts = ticker.split("-")
        mention_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Political Figure Mention Market** — YES resolves if the specified figure mentions "
            f"`{mention_slug}` in a public appearance or broadcast.\n\n"
            f"Specific risks to investigate:\n"
            f"- Is the event (speech, interview, broadcast appearance) still happening as scheduled?\n"
            f"- Does the topic `{mention_slug}` align with what the speaker is known to discuss?\n"
            f"- What is Kalshi's exact resolution source and word-matching rule?\n"
            f"- Has the word already been said earlier in the window? Search recent transcripts."
        )

    # --- Trump Speech/Phrase Markets ---

    if "TRUMPSAYMONTH" in event:
        parts = ticker.split("-")
        phrase_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Trump Monthly Speech Phrase Market** — YES resolves if Trump says `{phrase_slug}` "
            f"in any public remark within the specified month.\n\n"
            f"Specific risks to investigate:\n"
            f"- How much of the measurement window remains before close?\n"
            f"- Are there any scheduled Trump events (rallies, press conferences, signings) "
            f"in the remaining window where this phrase could plausibly appear?\n"
            f"- Search recent Trump speech transcripts and Truth Social posts for the phrase — "
            f"has it already been said in this window?\n"
            f"- Does Kalshi require an exact phrase match, or do paraphrases count?\n"
            f"- What is the base rate for Trump saying this phrase in a typical month?"
        )

    if "TRUMPSAY" in event:
        parts = ticker.split("-")
        phrase_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Trump Exact Phrase Market** — YES resolves if Trump says `{phrase_slug}` "
            f"in a public remark within the specified short window.\n\n"
            f"Specific risks to investigate:\n"
            f"- How much time remains before the market closes?\n"
            f"- Are there scheduled events (rallies, press gaggles, speeches, interviews) "
            f"before close where this phrase could appear?\n"
            f"- Search Trump speech transcripts and Truth Social for recent uses of this phrase\n"
            f"- Kalshi resolution source: public recordings/transcripts — any ambiguity in "
            f"what qualifies as 'said' (written posts vs spoken remarks)?\n"
            f"- This is a short-window prop; the key question is whether the remaining schedule "
            f"makes it likely or unlikely"
        )

    # --- Truth Social / Social Media Count Markets ---

    if "TRUTHSOCIAL" in event:
        return (
            "**Truth Social Post Count Market** — YES resolves based on Trump's post count "
            "on Truth Social during a specific week, compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- Has the measurement window (the specified week) ended yet?\n"
            "- What does the current tracked count show? Search third-party trackers "
            "(Roll Call, Factba.se, or Coinbase prediction market pages that display counts)\n"
            "- What does Kalshi's rule include in the count: Truths only, or also ReTruths "
            "and Quote Truths? Are deleted posts excluded?\n"
            "- Is there any confirmed dispute or appeal on the week's final count?\n"
            "- What has Trump's weekly posting volume been in recent weeks?"
        )

    # --- NYT / Media Count Markets ---

    if "NYTHEAD" in event:
        return (
            "**New York Times Headline Count Market** — YES resolves based on the number of "
            "full-width NYT front-page headlines in a specified period.\n\n"
            "Specific risks to investigate:\n"
            "- Has the measurement period ended? If yes, the outcome is effectively locked.\n"
            "- What archive does Kalshi use to verify front pages? "
            "(NYT Today's Paper, Frontpages.com, Kiosko)\n"
            "- What is Kalshi's exact definition of 'full-width headline'? "
            "This is the most likely source of dispute — search Kalshi rules for this market\n"
            "- Search the NYT front page archive for the relevant dates to count qualifying headlines"
        )

    # --- SOTU Attendance Markets ---

    if "ATTENDSOTU" in event or "SOTU" in event:
        parts = ticker.split("-")
        person_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**SOTU Attendance Market** — YES resolves if `{person_slug}` attends the State of "
            f"the Union address as a named guest.\n\n"
            f"Specific risks to investigate:\n"
            f"- Is the SOTU still scheduled as planned? Check for date/time confirmations.\n"
            f"- Is there confirmed reporting that `{person_slug}` was invited and accepted?\n"
            f"- Any last-minute illness, travel issues, or scheduling conflicts reported?\n"
            f"- How does Kalshi verify attendance — live broadcast footage, pool reports, "
            f"or White House guest list?\n"
            f"- What is the time remaining before the event — has the SOTU already occurred?"
        )

    # --- Government / Political Event Markets ---

    if "GOVSHUT" in event or "GOVTFUND" in event:
        return (
            "**Government Shutdown / Funding Market** — YES resolves based on whether the "
            "federal government is shut down or funded at a specific date/time.\n\n"
            "Specific risks to investigate:\n"
            "- What is the exact legal trigger — when does the current CR/appropriations expire?\n"
            "- Search for the latest vote counts, Senate floor scheduling, and leadership statements\n"
            "- What procedural paths exist to avoid shutdown (split bills, unanimous consent, "
            "short CR)? Are any of these actively being pursued?\n"
            "- Search for the most recent Congressional statements and roll call positions\n"
            "- What is the historical base rate for last-minute funding resolutions?"
        )

    if "PRESNOMFEDCHAIR" in event or "FEDCHAIR" in event:
        return (
            "**Presidential Nomination Market** — YES resolves if Trump announces a specific "
            "nominee within the specified window.\n\n"
            "Specific risks to investigate:\n"
            "- Are there any credible news reports of an imminent announcement?\n"
            "- What does the White House schedule show for the remaining window?\n"
            "- Has a frontrunner been reported by credible outlets (WSJ, Reuters, Bloomberg)?\n"
            "- What is the precedent for how quickly these announcements follow reported shortlists?\n"
            "- Is there any White House statement ruling out an announcement in this window?"
        )

    if "KHAMENEI" in event or ("OUT" in event and any(x in event for x in ["LEADER", "PRES"])):
        return (
            "**Political Leader Departure Market** — YES resolves if the specified leader "
            "leaves office before the deadline.\n\n"
            "Specific risks to investigate:\n"
            "- What is the leader's most recent documented public appearance? (confirms still active)\n"
            "- What is the constitutional/legal mechanism for departure — death, resignation, "
            "removal? How recently have any of these been plausible?\n"
            "- What is the historical base rate for departures of this type of leader?\n"
            "- Search for the latest health reporting, political stability reporting, or "
            "institutional moves that could indicate an imminent change\n"
            "- How much time remains in the window?"
        )

    # --- Economic Data Markets ---

    if "PAYROLLS" in event:
        return (
            "**Nonfarm Payrolls Market** — YES resolves on the BLS Employment Situation "
            "headline number compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- Is the BLS release still scheduled for the expected date? Search for any "
            "government shutdown delays (BLS delays releases during funding lapses — this "
            "has happened in 2026)\n"
            "- What does the ADP National Employment Report show for this period?\n"
            "- What are weekly initial jobless claims trending? (proxy for labor market health)\n"
            "- Are there seasonal adjustment or benchmark revision effects that could push the "
            "headline above/below the threshold independently of actual hiring?\n"
            "- What is the Bloomberg/Reuters economist consensus for this month's print?"
        )

    if event.startswith("KXU3"):
        return (
            "**Unemployment Rate (U-3) Market** — YES resolves on the BLS U-3 unemployment "
            "rate for the specified month compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- Is the BLS Employment Situation release still on schedule? Search for shutdown "
            "delays (BLS has delayed releases during 2026 government funding lapses)\n"
            "- What do recent labor market data points (ADP, initial claims, JOLTS) suggest "
            "about the direction of unemployment?\n"
            "- What is the economist consensus for this month's U-3 rate?\n"
            "- U-3 is derived from the household survey — is there any unusual household "
            "survey methodology note for this period?\n"
            "- What has U-3 been in the preceding 2-3 months? (trending direction matters)"
        )

    if "GDP" in event:
        return (
            "**GDP Growth Market** — YES resolves on the BEA's GDP advance/revised estimate "
            "for the specified quarter compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What is the latest GDPNow estimate from the Atlanta Fed?\n"
            "- What does the Philadelphia Fed Survey of Professional Forecasters show?\n"
            "- What is the spread between nowcast models (Atlanta Fed often diverges from "
            "consensus)? A wide spread signals high uncertainty.\n"
            "- Which BEA release (advance, second, third estimate) does the market use? "
            "The advance estimate comes first and can differ significantly from later revisions\n"
            "- Is the BEA release still on schedule, or could a government shutdown delay it?"
        )

    if "CPIYOY" in event or "CPI" in event:
        return (
            "**CPI Inflation Market** — YES resolves on the BLS CPI year-over-year rate "
            "for the specified month compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What does the Cleveland Fed's Inflation Nowcasting model show?\n"
            "- What are the recent monthly trends in shelter/OER (owners' equivalent rent — "
            "the single largest CPI component and biggest source of upside surprise)?\n"
            "- What does the economist consensus show for this month's YoY CPI?\n"
            "- Is the BLS release still on schedule? (government shutdown risk applies)\n"
            "- Are there any known methodological changes or unusual seasonal adjustments "
            "for this specific CPI release?"
        )

    if "WTIW" in event or "WTID" in event:
        return (
            "**WTI Oil Price Market** — YES resolves on the official NYMEX/CME WTI "
            "front-month daily settlement price compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What is the current WTI front-month futures price? (distance from threshold)\n"
            "- CME settles WTI at 2:28–2:30 PM ET — the market resolves at that specific "
            "settlement print, not intraday high/low\n"
            "- What are the latest EIA weekly inventory numbers? (builds are bearish, "
            "draws are bullish for price)\n"
            "- What is the OPEC+ production stance? Any recent meeting decisions or "
            "voluntary cut changes?\n"
            "- Any geopolitical disruptions (Iran, Venezuela, Russia) currently affecting supply?\n"
            "- Any short-term weather/infrastructure events affecting production?"
        )

    if "AAAGASM" in event or "AAAGASW" in event:
        return (
            "**National Gas Price Market** — YES resolves on the national average retail "
            "gasoline price compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What is the current AAA national average? (gasprices.aaa.com)\n"
            "- What series does Kalshi use for resolution: AAA, EIA weekly all-grades, "
            "or EIA regular grade? These can differ by 10-15 cents — this is critical\n"
            "- What does the latest EIA Weekly Petroleum Status Report show for "
            "gasoline inventories and refinery utilization?\n"
            "- What has WTI crude been doing? Retail prices lag crude by ~1-2 weeks\n"
            "- Any regional refinery outages or weather disruptions affecting the national average?"
        )

    if "FOMC" in event or "FOMCDISSENT" in event:
        return (
            "**FOMC Dissent Count Market** — YES resolves on the number of dissenting votes "
            "at the specified FOMC meeting.\n\n"
            "Specific risks to investigate:\n"
            "- Has the FOMC meeting already occurred? If yes, what was the vote tally?\n"
            "- What was the dissent count at the prior meeting? (sets the baseline)\n"
            "- Who are the rotating voting members for this meeting? (FOMC voter roster changes)\n"
            "- What public speeches have voting members given recently signaling "
            "hawkish/dovish positions?\n"
            "- The dissent count is revealed immediately when the FOMC statement is issued — "
            "what is the scheduled statement release time?"
        )

    if "TSAW" in event:
        return (
            "**TSA Passenger Volume Market** — YES resolves on the TSA's published "
            "weekly average passenger screening count compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What are TSA's published daily throughput numbers so far this week? "
            "(tsa.gov/travel/passenger-volumes publishes daily counts)\n"
            "- How many days of the measurement window remain?\n"
            "- Are there any ongoing weather events, FAA ground stops, or travel disruptions "
            "that could suppress volumes for multiple days?\n"
            "- What is the prior-week average for comparison?\n"
            "- Does Kalshi include all 7 days, or a specific subset? Check market rules"
        )

    if "BTCD" in event or "BTC" in event:
        return (
            "**Bitcoin Price Market** — YES resolves on the BTC spot price at a specific "
            "timestamp compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What is the current BTC spot price and how far is it from the threshold?\n"
            "- What specific exchange or index does Kalshi use for settlement? "
            "(Coinbase, CME reference rate, or a composite — this determines the exact price used)\n"
            "- What is the time remaining until settlement? BTC is highly volatile intraday\n"
            "- Any major crypto news events (ETF flows, exchange hacks, regulatory news, "
            "macro risk-off events) that could cause a large move before settlement?\n"
            "- What does the options market (Deribit) imply about near-term volatility?"
        )

    # --- Sports: Game Winner Markets ---

    if "NBAGAME" in event:
        parts = ticker.split("-")
        team_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**NBA Game Winner Market** — YES resolves if `{team_slug}` wins the specified game.\n\n"
            f"Specific risks to investigate:\n"
            f"- Is the game still scheduled? Search for postponements or rescheduling.\n"
            f"- What is the latest official NBA injury report for both teams? "
            f"(nba.com/news and ESPN injury reports — check for star player availability)\n"
            f"- What are the current sportsbook moneylines (DraftKings, FanDuel, BetMGM)? "
            f"A large spread between Kalshi and sportsbooks signals mispricing risk\n"
            f"- Is either team on a back-to-back? (fatigue affects win probability)\n"
            f"- Recent head-to-head record and season records for both teams\n"
            f"- Any key lineup/rotation changes (resting stars, load management)?"
        )

    if "NBATOTAL" in event:
        return (
            "**NBA Game Total Market** — YES resolves if the combined final score exceeds "
            "the specified threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What is the latest injury/availability status for high-usage players on both teams? "
            "(A key player out significantly changes expected total)\n"
            "- What are the current sportsbook over/under lines for this game?\n"
            "- What are both teams' offensive and defensive ratings this season, "
            "and do the numbers change materially with key players absent?\n"
            "- What is the recent pace-of-play for both teams?\n"
            "- Is either team on a back-to-back or in a stretch of fatigue?"
        )

    if "NBATRADE" in event:
        parts = ticker.split("-")
        player_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**NBA Trade Market** — YES resolves if `{player_slug}` is traded before the deadline.\n\n"
            f"Specific risks to investigate:\n"
            f"- What does the latest insider reporting say? (ESPN's Shams Charania, "
            f"Athletic's Wojnarowski — these are the authoritative sources)\n"
            f"- Has the team's front office publicly confirmed or denied trade interest?\n"
            f"- What is the player's current injury/availability status? "
            f"(injuries reduce trade value and complicate medical clearances)\n"
            f"- What assets would a realistic trade package require, and which teams "
            f"have the cap space and picks to execute?\n"
            f"- How much time remains before the NBA trade deadline (Feb 6)?\n"
            f"- What did the player say publicly about their situation?"
        )

    if "NEXTTEAM" in event:
        parts = ticker.split("-")
        team_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**NBA Player Destination Market** — YES resolves if the player's next team "
            f"is `{team_slug}`.\n\n"
            f"Specific risks to investigate:\n"
            f"- What does the latest insider reporting say about the player's preferred destination?\n"
            f"- Has the team (`{team_slug}`) been specifically named by credible reporters "
            f"as an active suitor with real offer capacity?\n"
            f"- What are the asset/cap constraints for `{team_slug}` — do they have the "
            f"picks and players to match salary?\n"
            f"- Is the player's current team open to trading now vs. waiting for the offseason?\n"
            f"- What is the player's current injury status and contract situation?"
        )

    if "NCAAMBGAME" in event:
        parts = ticker.split("-")
        team_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**NCAA Men's Basketball Game Market** — YES resolves if `{team_slug}` wins.\n\n"
            f"Specific risks to investigate:\n"
            f"- Is the game still scheduled? College games are occasionally postponed.\n"
            f"- What are the current KenPom/NET rankings and win probabilities for both teams?\n"
            f"- What do available sportsbook lines show?\n"
            f"- Any reported injury or eligibility issues for key players on either team?\n"
            f"- Is this a home/away/neutral site game? Home court matters significantly "
            f"in college basketball"
        )

    if "NCAABBGAME" in event:
        parts = ticker.split("-")
        team_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**NCAA Women's Basketball Game Market** — YES resolves if `{team_slug}` wins.\n\n"
            f"Specific risks to investigate:\n"
            f"- Is the game still scheduled? Any postponements or venue changes?\n"
            f"- What are the NET rankings and season records for both teams?\n"
            f"- Any reported injury issues for key players?\n"
            f"- Home/away/neutral site?\n"
            f"- What do available betting markets show for this matchup?"
        )

    if "MLBSTGAME" in event or ("MLB" in event and "GAME" in event):
        return (
            "**MLB Game Market** — YES resolves based on the official MLB box score winner.\n\n"
            "Specific risks to investigate:\n"
            "- Is this a spring training game? Spring training lineups are experimental — "
            "starters may be pulled early, prospects may play, and rosters change daily\n"
            "- Is the game still scheduled? Spring training games are more frequently "
            "cancelled or shortened due to weather or logistics\n"
            "- Does Kalshi count a suspended/shortened game as a completed result?\n"
            "- For regular season: who is starting (pitching matchup is the primary driver)?\n"
            "- What are current sportsbook moneylines?\n"
            "- Any injury/roster news affecting the lineup?"
        )

    # --- Sports: Racing Markets ---

    if "NASCARRACE" in event:
        parts = ticker.split("-")
        driver_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**NASCAR Race Winner Market** — YES resolves if `{driver_slug}` wins the race.\n\n"
            f"Specific risks to investigate:\n"
            f"- Has the race started or finished yet? Search for the current race status.\n"
            f"- If pre-race: what do practice/qualifying results show for `{driver_slug}`?\n"
            f"- What are the current sportsbook odds for `{driver_slug}` to win?\n"
            f"- NASCAR fields are large (30-40 cars) — a single driver NOT winning is "
            f"structurally likely; understand the direction of this market (YES or NO)\n"
            f"- Any mechanical issues, crash news, or weather delays reported?\n"
            f"- What track type is this? (superspeedway vs road course vs oval — "
            f"different tracks suit different drivers)"
        )

    if "INDYCARRACE" in event:
        parts = ticker.split("-")
        driver_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**IndyCar Race Winner Market** — YES resolves if `{driver_slug}` wins the race.\n\n"
            f"Specific risks to investigate:\n"
            f"- Has the race started or finished? Search for official IndyCar race results.\n"
            f"- If pre-race: what do practice times and qualifying show?\n"
            f"- What are sportsbook odds for `{driver_slug}`?\n"
            f"- IndyCar fields are large — understand the direction (YES vs NO side)\n"
            f"- Any reported mechanical issues, crashes, or weather delays?\n"
            f"- Street circuits (like St. Petersburg) favor specific car setups and teams"
        )

    # --- Sports: Olympics / International ---

    if "WOHOCKEY" in event or ("HOCKEY" in event and "OLYMPIC" in event):
        parts = ticker.split("-")
        team_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Olympic Ice Hockey Market** — YES resolves if `{team_slug}` wins the gold medal.\n\n"
            f"Specific risks to investigate:\n"
            f"- What stage is the tournament at? Search for current bracket results.\n"
            f"- What do sportsbooks currently price for `{team_slug}` gold? "
            f"(DraftKings, FanDuel — compare to Kalshi price)\n"
            f"- What is `{team_slug}`'s group composition and path to the final?\n"
            f"- Are NHL stars participating? (full NHL participation changes relative strength)\n"
            f"- Any injury/roster news for `{team_slug}` or their likely medal round opponents?\n"
            f"- What recent best-on-best international results exist (4 Nations, World Championships)?"
        )

    if "AOMEN" in event or "AOWOMEN" in event:
        parts = ticker.split("-")
        player_slug = parts[-1] if len(parts) > 1 else "unknown"
        tour = "ATP" if "AOMEN" in event else "WTA"
        return (
            f"**Australian Open {tour} Market** — YES resolves if `{player_slug}` wins the title.\n\n"
            f"Specific risks to investigate:\n"
            f"- Where is `{player_slug}` in the draw right now? Search for current match results.\n"
            f"- What is `{player_slug}`'s current physical status? "
            f"(injuries, blisters, match load — check post-match press conference reports)\n"
            f"- Who are the remaining opponents and what is the H2H history?\n"
            f"- What do current sportsbook odds show for `{player_slug}` to win the title?\n"
            f"- How many matches has `{player_slug}` played vs opponents (fatigue differential)?\n"
            f"- Did `{player_slug}` receive any walkovers/retirements that reduced match load?"
        )

    # --- Entertainment / Media Markets ---

    if "NETFLIXRANK" in event:
        parts = ticker.split("-")
        title_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Netflix Ranking Market** — YES resolves based on a specific title's position "
            f"in Netflix's official Top 10 for a specified date.\n\n"
            f"Specific risks to investigate:\n"
            f"- Check FlixPatrol (flixpatrol.com) for the current Netflix Top 10 — "
            f"this is the primary data source used for resolution\n"
            f"- Is the ranking for a specific date (daily) or a weekly aggregate?\n"
            f"- Is `{title_slug}` currently trending up or down? New episodes or "
            f"press coverage drive rapid ranking changes\n"
            f"- Is this the US ranking or the global ranking? They can differ significantly\n"
            f"- What new content dropped this week that could displace `{title_slug}`?"
        )

    if "TOPSONG" in event or "TOPALBUM" in event:
        parts = ticker.split("-")
        title_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Billboard Chart Market** — YES resolves based on `{title_slug}`'s position "
            f"on the Billboard Hot 100 or Albums chart for the specified week.\n\n"
            f"Specific risks to investigate:\n"
            f"- What does the current Luminate/Billboard tracking show for `{title_slug}`? "
            f"(Chart analysts publish midweek tracking data)\n"
            f"- What songs/albums are above `{title_slug}` this week?\n"
            f"- Billboard weights streaming (most), airplay, and sales — "
            f"which factor is `{title_slug}` strongest in?\n"
            f"- When does the chart week end and when is the new chart published?\n"
            f"- Is there a major competitor release this week that could push `{title_slug}` down?"
        )

    if "FIRSTSUPERBOWLSONG" in event or "SUPERBOWLHALFTIME" in event:
        return (
            "**Super Bowl Halftime Setlist Market** — YES resolves based on which song is "
            "performed first during the halftime show.\n\n"
            "Specific risks to investigate:\n"
            "- What song does the official Apple Music/NFL promotional trailer feature? "
            "(trailers typically signal the show's featured tracks)\n"
            "- What has the artist's recent tour setlist looked like — specifically which "
            "song opens the show? (JamBase, Setlist.fm for recent concert setlists)\n"
            "- Have any rehearsal reports or setlist leaks emerged? "
            "(these typically surface 1-7 days before the game)\n"
            "- Halftime shows often differ from tour setlists — the show is ~12-15 minutes "
            "and goes through major revisions up to game week\n"
            "- Search for any credible insider or production crew reports about the opening"
        )

    if "SUPERBOWLAD" in event:
        parts = ticker.split("-")
        brand_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**Super Bowl Advertiser Market** — YES resolves if `{brand_slug}` runs a "
            f"national in-game ad during the Super Bowl broadcast.\n\n"
            f"Specific risks to investigate:\n"
            f"- Check Ad Age, Adweek, Marketing Dive, and iSpot.tv advertiser trackers — "
            f"these publish confirmed advertisers in the weeks before the game\n"
            f"- Has `{brand_slug}` confirmed a Super Bowl buy, or is it only reported/rumored?\n"
            f"- Did `{brand_slug}` advertise during prior Super Bowls? "
            f"(prior participation is the strongest predictor)\n"
            f"- Does Kalshi count national broadcast spots only, or also streaming/Peacock breaks?\n"
            f"- A Peacock-only or regional buy would NOT count as a national Super Bowl ad "
            f"under most resolution rules"
        )

    # --- AI / Technology Markets ---

    if "TOPMODEL" in event:
        parts = ticker.split("-")
        model_slug = parts[-1] if len(parts) > 1 else "unknown"
        return (
            f"**AI Model Rankings Market** — YES resolves based on `{model_slug}` being "
            f"the top-ranked AI model per Kalshi's specified benchmark.\n\n"
            f"Specific risks to investigate:\n"
            f"- Which specific leaderboard does Kalshi use for resolution? "
            f"(LMSYS Chatbot Arena, Scale HELM, HuggingFace Open LLM — these differ significantly)\n"
            f"- What is the current ranking of `{model_slug}` on the relevant leaderboard?\n"
            f"- Have any major model releases been announced or dropped in the measurement window?\n"
            f"- Does the leaderboard update in real-time or on a fixed schedule?\n"
            f"- What is the close date — could a new release change rankings before then?"
        )

    if "SPACEXCOUNT" in event:
        return (
            "**SpaceX Launch Count Market** — YES resolves based on SpaceX's total launch "
            "count for the specified year compared to a threshold.\n\n"
            "Specific risks to investigate:\n"
            "- What is SpaceX's current launch count for the year? "
            "(Spaceflight Now, NASASpaceflight.com maintain running tallies)\n"
            "- What upcoming launches are on the manifest before year-end?\n"
            "- Are any upcoming launches at risk of delay (FAA license, weather, hardware)?\n"
            "- Does Kalshi count Falcon 9, Falcon Heavy, and Starship separately or combined?\n"
            "- What was SpaceX's launch cadence in prior comparable periods?"
        )

    # --- Fallback ---

    return (
        "**General Market** — Research what specifically triggers YES resolution and whether "
        "any current conditions threaten that outcome.\n\n"
        "Specific risks to investigate:\n"
        "- What is the exact determining event and has it occurred yet?\n"
        "- Is the event still on schedule, or are there disruption risks?\n"
        "- What are Kalshi's exact resolution criteria — which source, which measurement?\n"
        "- What is the latest publicly available data or news directly relevant to this outcome?\n"
        "- What is the strongest current argument that YES will NOT resolve?\n"
        "- Are there any known disputes, appeals, or rule ambiguities for this market type?"
    )
