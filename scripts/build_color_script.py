"""Deterministically build data/color_script.json from the approved script + owner critique fixes.

Sentences are authored explicitly (so concat == narration by construction) with delivery tags that
drive TTS pacing/pauses. v2-critique fixes applied here: COMPLETE sentences only (no mid-sentence
fragment splits -> no weird mid-thought pauses), merged staccato, simplified romantic-red, section-9
suspense, real outro, new assets. Run: py -3 scripts/build_color_script.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# delivery tags: neutral curious question brisk weighty surprised skeptical ominous warm_cta transition punch
# Beat types -> families: establish/illustrate=object, stat_pop=stat, compare=comparison,
# diagram_build=diagram, list_reveal=list, quote=quote, cutaway_gag=miniature, emphasize/transition=caption.
SECTIONS = [
    {  # 1 - COLD OPEN + personal discovery hook
        "key_phrase": "JUST THE COLOR",
        "sent": [
            ("Two athletes step onto the mat.", "neutral"),
            ("Same height, same weight, same training.", "neutral"),
            ("They fight, and it's close - the kind that could go either way.", "neutral"),
            ("And then one of them wins.", "weighty"),
            ("Now watch what happens if we rewind, swap the color of their gear, and run it back.", "neutral"),
            ("The winner might change.", "weighty"),
            ("Not the fighting - just the color.", "weighty"),
            ("Same two people, same moves, and a different hand gets raised.", "neutral"),
            ("I first ran into this on a test, of all places.", "neutral"),
            ("A reading passage claimed the color you wear can change who wins, and who loses.", "neutral"),
            ("It sounded like nonsense.", "weighty"),
            ("It isn't.", "punch"),
            ("And it goes a lot deeper than sports.", "transition"),
        ],
        "beats": [
            {"type": "compare", "s": [0, 5], "text": "RED  vs  BLUE", "subjects": ["person", "person"], "colors": ["accent", "blue"], "importance": "high"},
            {"type": "emphasize", "s": [6, 7], "text": "JUST THE COLOR", "subjects": ["light"], "importance": "high"},
            {"type": "establish", "s": [8, 9], "text": "FROM A TEST", "subjects": ["paperwork"], "importance": "medium"},
            {"type": "emphasize", "s": [10, 12], "text": "DEEPER THAN SPORTS", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 2 - red in nature (mandrill + finch assets)
        "key_phrase": "WIRED IN",
        "sent": [
            ("So why would a color do anything at all?", "question"),
            ("Because in nature, red is rarely a decoration - it's a status report.", "neutral"),
            ("A male mandrill's face turns a brighter red as he climbs the ranks, and fades when he falls.", "neutral"),
            ("That color is wired straight to his testosterone, and he can't fake it.", "weighty"),
            ("Small songbirds size each other up by the red of their beaks, and the redder bird usually wins.", "neutral"),
            ("Across primates, birds, and fish, red keeps meaning the same thing.", "weighty"),
            ("Back off.", "punch"),
            ("So the real question isn't why animals react to red.", "neutral"),
            ("It's whether we ever stopped.", "transition"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 1], "text": "A STATUS REPORT", "subjects": ["mandrill"], "importance": "high"},
            {"type": "establish", "s": [2, 3], "text": "WIRED IN, NOT CHOSEN", "subjects": ["mandrill"], "importance": "high"},
            {"type": "establish", "s": [4, 4], "text": "THE REDDER BIRD WINS", "subjects": ["finch"], "importance": "medium"},
            {"type": "emphasize", "s": [5, 6], "text": "BACK OFF", "subjects": ["mandrill"], "importance": "high"},
            {"type": "emphasize", "s": [7, 8], "text": "DID WE EVER STOP?", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 3 - Olympic pattern (stats)
        "key_phrase": "NOT A FAIR COIN",
        "sent": [
            ("In 2004, two researchers went looking.", "neutral"),
            ("They pulled the results from four combat sports at the Athens Olympics.", "neutral"),
            ("Boxing, taekwondo, and two kinds of wrestling.", "neutral"),
            ("And here's the crucial part: in these sports, the gear is handed out at random.", "neutral"),
            ("Red or blue, nobody picks.", "neutral"),
            ("It's a coin flip.", "weighty"),
            ("So if color did nothing, red should win half the time.", "neutral"),
            ("It didn't.", "punch"),
            ("Red won fifty-five percent of bouts.", "weighty"),
            ("And in the closest fights, the ones that could tip either way, red won sixty-two.", "weighty"),
            ("A coin that lands red sixty-two percent of the time isn't a fair coin.", "weighty"),
            ("Something was loading it.", "transition"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 4], "text": "RED OR BLUE, AT RANDOM", "subjects": ["person", "person"], "colors": ["accent", "blue"], "importance": "medium"},
            {"type": "stat_pop", "s": [5, 8], "text": "RED WON 55%", "subjects": [], "importance": "high"},
            {"type": "stat_pop", "s": [9, 9], "text": "62% IN CLOSE FIGHTS", "subjects": [], "importance": "high"},
            {"type": "emphasize", "s": [10, 11], "text": "NOT A FAIR COIN", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 4 - two suspects
        "key_phrase": "TWO SUSPECTS",
        "sent": [
            ("So there were two suspects.", "weighty"),
            ("Suspect one: the color changes the fighters.", "neutral"),
            ("Maybe red makes you feel more dangerous, and makes your opponent flinch.", "neutral"),
            ("Suspect two: the color changes the person keeping score.", "neutral"),
            ("The fighters are identical - the referee is the one who's biased.", "weighty"),
            ("In a real match, both could be true at once, and you'd never tell them apart.", "neutral"),
            ("You'd need a way to freeze the fighters, and test only the judge.", "transition"),
        ],
        "beats": [
            {"type": "compare", "s": [0, 4], "text": "THE FIGHTER  or  THE JUDGE", "subjects": ["person", "person"], "colors": ["accent", "ink"], "importance": "high"},
            {"type": "emphasize", "s": [5, 6], "text": "FREEZE THE FIGHTERS", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 5 - the color-swap (the crack)
        "key_phrase": "IT WAS THE JUDGE",
        "sent": [
            ("Which is exactly what someone did.", "neutral"),
            ("They took real taekwondo footage and showed it to forty-two experienced referees to score.", "neutral"),
            ("Then they took the same clips and digitally swapped the colors.", "neutral"),
            ("The fighter who was in red was now in blue.", "neutral"),
            ("Same kick, same human, same exact moment.", "weighty"),
            ("The only thing that changed was a color filter.", "neutral"),
            ("The red athletes scored about thirteen percent higher.", "weighty"),
            ("Thirteen percent more points, just for being wrapped in red.", "weighty"),
            ("The bias wasn't on the mat.", "punch"),
            ("It was behind the scoring table, in the eyes of people who'd have sworn they were being fair.", "transition"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 1], "text": "42 REFEREES", "subjects": ["person"], "importance": "medium"},
            {"type": "compare", "s": [2, 5], "text": "SAME CLIP, SWAPPED", "subjects": ["person", "person"], "colors": ["accent", "blue"], "importance": "high"},
            {"type": "stat_pop", "s": [6, 7], "text": "RED:  +13%", "subjects": [], "importance": "high"},
            {"type": "emphasize", "s": [8, 9], "text": "IT WAS THE JUDGE", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 6 - black uniforms
        "key_phrase": "WHAT YOU WORE",
        "sent": [
            ("And once you know to look for it, you start seeing it everywhere.", "transition"),
            ("Years earlier, researchers dug through penalty records in pro football and hockey.", "neutral"),
            ("Teams that wore black got penalized more - not occasionally, but consistently.", "weighty"),
            ("Two teams even changed their jerseys to black one season, and their penalties jumped right after.", "neutral"),
            ("Now, maybe players in black really do play dirtier.", "neutral"),
            ("So the researchers filmed the exact same plays, once in white, once in black.", "neutral"),
            ("Referees called the black version more aggressive.", "weighty"),
            ("Red flatters you to the judge, and black incriminates you.", "neutral"),
            ("Either way, they're not scoring what you did.", "neutral"),
            ("They're scoring what you wore.", "transition"),
        ],
        "beats": [
            {"type": "compare", "s": [0, 4], "text": "WHITE  vs  BLACK", "subjects": ["person", "person"], "colors": ["muted", "ink"], "importance": "high"},
            {"type": "emphasize", "s": [5, 6], "text": "SAME PLAY, MORE FLAGS", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [7, 9], "text": "THEY SCORE THE JERSEY", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 7 - courtroom (gavel)
        "key_phrase": "THE NUMBER IS YEARS",
        "sent": [
            ("Now take it somewhere the score actually matters.", "transition"),
            ("A courtroom is just another room where people watch someone and decide a number.", "neutral"),
            ("Except here, the number is years.", "weighty"),
            ("And juries aren't immune to the packaging either.", "neutral"),
            ("Defendants who look the part get judged more dangerous, and sentenced harder, for the same crime.", "weighty"),
            ("Lawyers have known this forever.", "neutral"),
            ("It's why they put their clients in soft grays and quiet collars, never red.", "neutral"),
            ("Now, be honest with yourself here.", "curious"),
            ("This is softer science than the sports studies - mostly mock juries, and more about clothes than color.", "neutral"),
            ("But it's the same machine we just watched mis-score a kick.", "neutral"),
            ("And it doesn't switch off when the stakes go up.", "weighty"),
            ("If anything, it just hides better.", "transition"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 2], "text": "THE NUMBER IS YEARS", "subjects": ["gavel"], "importance": "high"},
            {"type": "emphasize", "s": [3, 6], "text": "DRESSED FOR THE JURY", "subjects": ["person"], "colors": ["muted"], "importance": "medium"},
            {"type": "emphasize", "s": [7, 9], "text": "SOFTER SCIENCE - BE HONEST", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [10, 11], "text": "IT JUST HIDES BETTER", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 8 - romantic red (simplified + person_female + heart)
        "key_phrase": "RED, MAYBE",
        "sent": [
            ("And then there's the one everybody wants to be true.", "curious"),
            ("Around 2008, studies claimed a woman in red looked more attractive to men, and the men had no idea it was happening.", "neutral"),
            ("It's a great story.", "neutral"),
            ("But here's the catch: when other scientists tried to repeat it, it mostly fell apart.", "weighty"),
            ("So I'm not going to promise you that red fixes your dating life.", "neutral"),
            ("Honestly, nobody's even sure this one is real.", "weighty"),
            ("And that's kind of the point.", "neutral"),
            ("A good color story is so tempting that even the scientists chasing it can get fooled.", "transition"),
        ],
        "beats": [
            {"type": "compare", "s": [0, 2], "text": "RED  =  ATTRACTIVE?", "subjects": ["person_female", "person"], "colors": ["accent", "ink"], "importance": "high"},
            {"type": "cutaway_gag", "s": [3, 3], "text": "IT FELL APART", "subjects": ["heart"], "importance": "high"},
            {"type": "emphasize", "s": [4, 7], "text": "EVEN SCIENTISTS GET FOOLED", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 9 - the twist (suspense restructured)
        "key_phrase": "IT WAS IN US",
        "sent": [
            ("So where does that leave the red advantage - the original, solid one?", "question"),
            ("You'd expect it to still be there.", "neutral"),
            ("For twenty years, everyone assumed it was.", "neutral"),
            ("Then someone went back and checked, with two decades of new data.", "neutral"),
            ("And the advantage was gone.", "ominous"),
            ("Today, red wins about fifty point five percent - a coin flip again.", "weighty"),
            ("So what changed?", "question"),
            ("The sport did.", "weighty"),
            ("Taekwondo brought in electronic scoring and instant replay.", "neutral"),
            ("The human referee got quietly demoted, and a machine started counting the hits.", "neutral"),
            ("And the moment the biased judge stepped back, the magic evaporated.", "weighty"),
            ("Think about that.", "curious"),
            ("If red had been making the fighters better, it should have survived.", "neutral"),
            ("The fighters are still human.", "neutral"),
            ("It died the instant we stopped trusting a person to score.", "weighty"),
            ("Which tells you the advantage was never really in the red.", "ominous"),
            ("It was in us.", "transition"),
        ],
        "beats": [
            {"type": "emphasize", "s": [0, 2], "text": "STILL THERE?", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [3, 4], "text": "GONE", "subjects": ["light"], "importance": "high"},
            {"type": "stat_pop", "s": [5, 6], "text": "NOW:  50.5%", "subjects": [], "importance": "high"},
            {"type": "establish", "s": [7, 10], "text": "THE MACHINE COUNTS", "subjects": ["counter"], "importance": "medium"},
            {"type": "emphasize", "s": [11, 14], "text": "IT DIED WITH THE JUDGE", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [15, 16], "text": "IT WAS IN US", "subjects": ["light"], "importance": "high"},
        ],
    },
    {  # 10 - closer + outro hook
        "key_phrase": "THE WRAPPING",
        "sent": [
            ("We'd like to believe we judge what's actually in front of us.", "neutral"),
            ("The kick, the play, the person.", "weighty"),
            ("But mostly, we judge the wrapping, and then invent a reason that sounds like merit.", "weighty"),
            ("The fix is almost insultingly simple.", "neutral"),
            ("Take the human out of the scoring, and the bias leaves with them.", "neutral"),
            ("But most of life doesn't have instant replay.", "weighty"),
            ("Most of the time, it's just you, a color you barely chose, and someone across the table who's certain they're being fair.", "weighty"),
            ("So here's the thing worth chewing on.", "curious"),
            ("If a single color can quietly bend a trained referee, what else are you being scored on that you've never once noticed?", "transition"),
        ],
        "beats": [
            {"type": "emphasize", "s": [0, 2], "text": "WE JUDGE THE WRAPPING", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [3, 5], "text": "NO INSTANT REPLAY", "subjects": ["light"], "importance": "high"},
            {"type": "compare", "s": [6, 6], "text": "YOU  vs  THE TABLE", "subjects": ["person", "person"], "colors": ["accent", "ink"], "importance": "medium"},
            {"type": "emphasize", "s": [7, 8], "text": "WHAT ELSE AREN'T YOU SEEING?", "subjects": ["light"], "importance": "high"},
        ],
    },
]


def build():
    sections = []
    for i, sec in enumerate(SECTIONS):
        sentences = [{"text": t, "delivery": d} for (t, d) in sec["sent"]]
        narration = " ".join(s["text"] for s in sentences)
        beats = []
        for j, b in enumerate(sec["beats"]):
            beat = {
                "id": "s%d_%d" % (i + 1, j + 1),
                "type": b["type"],
                "sentence_start": b["s"][0],
                "sentence_end": b["s"][1],
                "visual_intent": b.get("visual_intent", b["text"]),
                "text": b["text"],
                "subjects": b["subjects"],
                "importance": b.get("importance", "medium"),
            }
            if b.get("colors"):
                beat["colors"] = b["colors"]
            beats.append(beat)
        sections.append({
            "narration": narration,
            "sentences": sentences,
            "key_phrase": sec["key_phrase"],
            "beats": beats,
        })

    return {
        "title": "The Referee Sees Red",
        "title_options": [
            "The Referee Sees Red",
            "Red Doesn't Make You Better. It Makes Them Worse.",
            "The Color That Wins Your Arguments For You",
        ],
        "hook_options": [
            "Same fighters. Same moves. Swap the color, and a different hand gets raised.",
        ],
        "thumbnail_text_options": ["RED WINS?", "IT WAS THE JUDGE", "55% -> 50%"],
        "description": (
            "Across the Olympics, athletes in red won more - until the machines took over scoring, "
            "and the advantage vanished. A look at how the color you wear quietly hijacks the judgment "
            "of whoever is keeping score, from the mat to the courtroom. Sources in the video notes."
        ),
        "tags": ["psychology", "color", "red", "sports science", "bias", "referee", "explainer"],
        "sections": sections,
    }


def main():
    data = build()
    out = os.path.join(ROOT, "data", "color_script.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    bad = sum(
        1 for s in data["sections"]
        if " ".join(x["text"] for x in s["sentences"]) != s["narration"]
    )
    words = sum(len(s["narration"].split()) for s in data["sections"])
    print("wrote", out)
    print("sections:", len(data["sections"]),
          "| sentences:", sum(len(s["sentences"]) for s in data["sections"]),
          "| beats:", sum(len(s["beats"]) for s in data["sections"]),
          "| words:", words,
          "| invariant_violations:", bad)


if __name__ == "__main__":
    main()
