"""Deterministically build data/color_script.json from the approved SCRIPT_color_v1.md content.

Sentences are authored explicitly (so concat == narration by construction) with delivery tags;
each section gets a beat plan that maps to the cutaway scene families + registry assets we actually
have. Run: py -3 scripts/build_color_script.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each section: key_phrase, sentences [(text, delivery)], beats.
# Beat types -> families: establish/illustrate=object, stat_pop=stat, compare=comparison,
# diagram_build=diagram, list_reveal=list, quote=quote, cutaway_gag=miniature, emphasize/transition=caption.
SECTIONS = [
    {
        "key_phrase": "SAME FIGHT",
        "sent": [
            ("Two athletes step onto the mat.", "neutral"),
            ("Same height. Same weight. Same training.", "neutral"),
            ("They fight, and it's close - the kind of close where it could go either way.", "neutral"),
            ("And then one of them wins.", "weighty"),
            ("Now here's the strange part.", "neutral"),
            ("If we could rewind, swap the color of their gear, and run it again, the winner might change.", "neutral"),
            ("Not the fighting. Just the color.", "weighty"),
            ("Same two people, same exact moves, and a different hand gets raised.", "neutral"),
            ("That sounds like superstition.", "neutral"),
            ("It isn't.", "ominous"),
        ],
        "beats": [
            {"type": "compare", "s": [0, 3], "text": "RED  vs  BLUE", "subjects": ["person", "person"], "importance": "high"},
            {"type": "emphasize", "s": [4, 7], "text": "JUST THE COLOR", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [8, 9], "text": "NOT SUPERSTITION", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "A STATUS REPORT",
        "sent": [
            ("Why would a color do anything at all?", "question"),
            ("Because in nature, red is rarely a decoration. It's a status report.", "neutral"),
            ("A male mandrill's face goes a brighter red as he climbs the ranks, and fades when he falls - the color wired directly to his testosterone.", "neutral"),
            ("He can't fake it.", "weighty"),
            ("Zebra finches size each other up by the red of their beaks, and the redder bird usually wins.", "neutral"),
            ("Across primates, birds, fish, red tends to mean the same thing.", "neutral"),
            ("I am dominant, and this is not the day to test me.", "ominous"),
            ("So the question isn't why animals respond to red. It's whether we ever stopped.", "weighty"),
        ],
        "beats": [
            {"type": "emphasize", "s": [0, 1], "text": "RED ISN'T DECORATION", "subjects": ["light"], "importance": "high"},
            {"type": "establish", "s": [2, 4], "text": "WIRED TO TESTOSTERONE", "subjects": ["light", "person"], "importance": "medium"},
            {"type": "emphasize", "s": [5, 7], "text": "I AM DOMINANT", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "NOT A FAIR COIN",
        "sent": [
            ("In 2004, two researchers went looking.", "neutral"),
            ("They pulled the results from four combat sports at the Athens Olympics - boxing, taekwondo, and two kinds of wrestling.", "neutral"),
            ("The crucial detail: in these sports, athletes are handed red or blue gear at random. Nobody chooses.", "neutral"),
            ("It's a coin flip.", "neutral"),
            ("If color did nothing, red should win half the time.", "neutral"),
            ("It didn't.", "ominous"),
            ("Red won fifty-five percent of bouts.", "weighty"),
            ("And in the closest, most evenly matched fights, red won sixty-two percent.", "weighty"),
            ("A coin that lands heads sixty-two percent of the time isn't a fair coin.", "neutral"),
            ("So something was loading it. The only question was what.", "ominous"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 2], "text": "RANDOM RED OR BLUE", "subjects": ["person", "person"], "importance": "medium"},
            {"type": "stat_pop", "s": [3, 6], "text": "RED WON 55%", "subjects": ["number"], "importance": "high"},
            {"type": "stat_pop", "s": [7, 8], "text": "62% IN CLOSE BOUTS", "subjects": ["number"], "importance": "high"},
            {"type": "emphasize", "s": [9, 9], "text": "NOT A FAIR COIN", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "TWO SUSPECTS",
        "sent": [
            ("There were two suspects.", "neutral"),
            ("Suspect one: the color changes the fighters.", "neutral"),
            ("Maybe wearing red makes you feel a little more dangerous, and facing red makes you flinch a little more.", "neutral"),
            ("Suspect two: the color changes the person keeping score.", "neutral"),
            ("The fighters are identical; the referee is the one who's biased.", "neutral"),
            ("In a normal match, both could be true at once, and you'd never know which one tipped it.", "neutral"),
            ("You need a way to freeze the fighters and test only the judge.", "weighty"),
        ],
        "beats": [
            {"type": "compare", "s": [0, 4], "text": "THE FIGHTER  vs  THE JUDGE", "subjects": ["person", "person"], "importance": "high"},
            {"type": "emphasize", "s": [5, 6], "text": "FREEZE THE FIGHTERS", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "SAME FOOTAGE",
        "sent": [
            ("Which is exactly what someone did.", "neutral"),
            ("Take real taekwondo footage. Show it to forty-two experienced referees, and have them score it.", "neutral"),
            ("Then take the same clips and digitally swap the colors, so the athlete who was in red is now in blue.", "neutral"),
            ("The performance is bit-for-bit identical. The only thing that changed is a color filter.", "neutral"),
            ("The red athletes scored about thirteen percent higher.", "weighty"),
            ("Same kick. Same human throwing it. Thirteen percent more points, for being wrapped in red.", "weighty"),
            ("You can't claim the fighters fought differently, because it was the same footage.", "neutral"),
            ("The bias wasn't on the mat. It was behind the scoring table, in the eyes of people who'd have sworn they were being fair.", "ominous"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 1], "text": "42 REFEREES", "subjects": ["person"], "importance": "medium"},
            {"type": "compare", "s": [2, 3], "text": "SAME CLIP, SWAPPED", "subjects": ["person", "person"], "importance": "high"},
            {"type": "stat_pop", "s": [4, 5], "text": "RED:  +13%", "subjects": ["number"], "importance": "high"},
            {"type": "emphasize", "s": [6, 7], "text": "IT WAS THE JUDGE", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "WHAT YOU WORE",
        "sent": [
            ("Once you know to look for it, the pattern has a longer history.", "neutral"),
            ("Years earlier, researchers went through penalty records in American football and hockey, and found that teams who wore black were penalized more.", "neutral"),
            ("Not occasionally. Consistently.", "weighty"),
            ("Two teams switched to black uniforms mid-history, and their penalty minutes climbed right after.", "neutral"),
            ("Maybe black-clad players really do play dirtier.", "neutral"),
            ("But then the researchers filmed identical plays, once in white, once in black, and asked referees to judge. The black version was rated more aggressive.", "neutral"),
            ("Red flatters you to the judge. Black incriminates you.", "weighty"),
            ("Either way, the person scoring isn't watching what you did. They're watching what you wore.", "ominous"),
        ],
        "beats": [
            {"type": "compare", "s": [0, 3], "text": "WHITE  vs  BLACK", "subjects": ["person", "person"], "importance": "high"},
            {"type": "emphasize", "s": [4, 5], "text": "BLACK = MORE FLAGS", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [6, 7], "text": "THEY JUDGE THE JERSEY", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "THE NUMBER IS YEARS",
        "sent": [
            ("Now move it somewhere the score actually matters.", "neutral"),
            ("A courtroom is just another room where humans watch a person and decide a number, except the number is years.", "weighty"),
            ("And juries, it turns out, aren't immune to the packaging.", "neutral"),
            ("Defendants who look the part - the wrong tattoos, the wrong clothes - are reliably judged more dangerous and sentenced harder, for the same alleged crime.", "neutral"),
            ("Lawyers have known this forever, which is why defendants tend to show up in soft grays and quiet collars, never red.", "neutral"),
            ("Now, be careful here. This is softer science than the sports studies.", "neutral"),
            ("It's mostly mock juries, not real verdicts, and the cleanest findings are about tattoos and dress, not color specifically.", "neutral"),
            ("But the machine underneath is the same one we just watched mis-score a kick.", "neutral"),
            ("It doesn't switch off because the stakes went up. If anything, it gets better at hiding.", "ominous"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 1], "text": "THE NUMBER IS YEARS", "subjects": ["building"], "importance": "high"},
            {"type": "emphasize", "s": [2, 4], "text": "DRESSED FOR THE JURY", "subjects": ["person"], "importance": "medium"},
            {"type": "emphasize", "s": [5, 6], "text": "SOFTER SCIENCE", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [7, 8], "text": "IT DOESN'T SWITCH OFF", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "IT DIDN'T REPLICATE",
        "sent": [
            ("And then there's the place the science got a little drunk on itself.", "neutral"),
            ("Around 2008, a famous set of studies claimed that simply putting a woman in red made men rate her as more attractive, and that the men had no idea it was happening.", "neutral"),
            ("It's a great story. Red, the ancient signal, hijacking attraction in a coffee shop.", "neutral"),
            ("The trouble is, when other labs tried to repeat it, the effect got shy.", "neutral"),
            ("Some found it; many didn't; the big pooled analysis came back lukewarm.", "weighty"),
            ("So I'm not going to tell you that wearing red will fix your dating life.", "neutral"),
            ("The honest answer is that this one is wobbling, and you should be suspicious of anyone who sells it to you with confidence.", "weighty"),
            ("Which is, itself, the lesson. The pull toward a tidy color story is strong enough to bend the people studying it.", "ominous"),
        ],
        "beats": [
            {"type": "establish", "s": [0, 2], "text": "ROMANTIC RED", "subjects": ["person", "light"], "importance": "medium"},
            {"type": "emphasize", "s": [3, 4], "text": "IT DIDN'T REPLICATE", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [5, 7], "text": "BE SUSPICIOUS", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "IT WAS IN US",
        "sent": [
            ("So where does that leave the red advantage - the original, solid one, the Olympic coin that landed red sixty-two percent of the time?", "question"),
            ("Here's the part I love.", "neutral"),
            ("Somebody checked again, recently, with twenty more years of data.", "neutral"),
            ("And the advantage is gone.", "ominous"),
            ("Today, red wins about fifty point five percent. A coin flip again.", "weighty"),
            ("What changed? The sports did.", "neutral"),
            ("Taekwondo brought in electronic scoring and instant replay. The rules got tighter, the human referee got quietly demoted, and a machine started counting the hits.", "neutral"),
            ("And the moment the biased judge stepped back, the magic evaporated.", "weighty"),
            ("If red had been making the fighters genuinely better, the effect should have survived. The fighters are still human.", "neutral"),
            ("It died the instant we stopped trusting a person to score.", "weighty"),
            ("Which tells you the advantage was never really in the red. It was in us.", "ominous"),
        ],
        "beats": [
            {"type": "stat_pop", "s": [0, 4], "text": "NOW:  50.5%", "subjects": ["number"], "importance": "high"},
            {"type": "establish", "s": [5, 7], "text": "THE MACHINE COUNTS", "subjects": ["counter"], "importance": "medium"},
            {"type": "emphasize", "s": [8, 9], "text": "IT DIED WITH THE JUDGE", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [10, 10], "text": "IT WAS IN US", "subjects": ["light"], "importance": "high"},
        ],
    },
    {
        "key_phrase": "THE WRAPPING",
        "sent": [
            ("We'd like to believe we judge what's actually in front of us - the kick, the play, the person.", "neutral"),
            ("Mostly, we judge the wrapping, and then we invent a reason that sounds like merit.", "weighty"),
            ("The good news, if you want one, is that the cure is boring and it works: take the human out of the scoring, and the bias goes with them.", "neutral"),
            ("The bad news is that most of life doesn't have instant replay.", "weighty"),
            ("Most of the time, it's just you, a color you half-chose, and someone across the table who's certain they're being fair.", "ominous"),
        ],
        "beats": [
            {"type": "emphasize", "s": [0, 1], "text": "WE JUDGE THE WRAPPING", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [2, 3], "text": "NO INSTANT REPLAY", "subjects": ["light"], "importance": "high"},
            {"type": "emphasize", "s": [4, 4], "text": "CERTAIN THEY'RE FAIR", "subjects": ["light"], "importance": "high"},
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
            beats.append({
                "id": "s%d_%d" % (i + 1, j + 1),
                "type": b["type"],
                "sentence_start": b["s"][0],
                "sentence_end": b["s"][1],
                "visual_intent": b.get("visual_intent", b["text"]),
                "text": b["text"],
                "subjects": b["subjects"],
                "importance": b.get("importance", "medium"),
            })
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
    # invariant check
    bad = 0
    for s in data["sections"]:
        if " ".join(x["text"] for x in s["sentences"]) != s["narration"]:
            bad += 1
    print("wrote", out)
    print("sections:", len(data["sections"]),
          "| sentences:", sum(len(s["sentences"]) for s in data["sections"]),
          "| beats:", sum(len(s["beats"]) for s in data["sections"]),
          "| invariant_violations:", bad)


if __name__ == "__main__":
    main()
