/* Voice check: does a piece of writing read like AI, or like the person sending it?
 *
 * A browser port of email_voice_check.py (Claude Code's pre-send gate), rule for rule, so an agent with only a
 * browser can run the same check. Nothing leaves the page: the text is checked here, in the browser.
 *
 * Two passes, then a verdict:
 *   lexical     words and phrases AI reaches for (formal transitions, email cliches, hedging, empty praise,
 *               avoided contractions)
 *   structural  the AI skeleton that survives swapping words: a tidy three-part ending, stacked "X, the Y,"
 *               glosses, contractions sprinkled evenly, three or more dashes splitting sentences
 *   PASS 0-2 signals and none structural; FLAG 3-4, or any structural; MAJOR FLAG 5+, or 3+ structural.
 *   strict: any signal at all is a FAIL (the setting for anything about to be posted or sent).
 * House rules are hard FAILs, never advisory:
 *   as the owner   the writing names its own author in the third person ("Jon has the password")
 *   plain English  (for a non-technical reader) over 350 words, technical terms with no explanation in the
 *                  same sentence, or a reply that doesn't quote the points it answers with ">"
 * Passing is necessary, not sufficient: it means the prose doesn't read as AI, not that it's right.
 *
 * Usage: VoiceCheck.check(text, {strict, asOwner, plain, reply}) in the page, or require() it in node.
 */
(function (root) {
  "use strict";
  // Curly apostrophes count as apostrophes: chat apps and phones type them, and "don’t" is a contraction.
  const norm = (t) => t.replace(/[‘’]/g, "'");
  const rx = (s) => new RegExp(s, "gi");

  const FORMAL_PHRASES = [
    String.raw`\bI would recommend\b`, String.raw`\bIt is (suggested|recommended|worth noting|important to note)\b`,
    String.raw`\butilizing\b`, String.raw`\bfurthermore\b`, String.raw`\bmoreover\b`, String.raw`\bnevertheless\b`,
    String.raw`\bconsequently\b`, String.raw`\bthus,`, String.raw`\bhence,`, String.raw`\baccordingly\b`,
    String.raw`\bin conclusion\b`, String.raw`\bto summarize\b`, String.raw`\bit should be noted\b`,
    String.raw`\bone should consider\b`, String.raw`\bas such,`, String.raw`\bthat being said\b`,
    String.raw`\bneedless to say\b`,
  ];
  const EMAIL_TELLS = [
    String.raw`\bI hope this (email|message|note) finds you well\b`,
    String.raw`\bI wanted to (reach out|touch base|follow up|circle back)\b`,
    String.raw`\b(reach out|touch base|circle back)\b`, String.raw`\bat your earliest convenience\b`,
    String.raw`\bplease (do not|don'?t) hesitate\b`, String.raw`\brest assured\b`, String.raw`\bdelve\b`,
    String.raw`\btapestry\b`, String.raw`\ba testament to\b`,
    String.raw`\bin (today'?s|the) (fast[- ]paced|ever[- ]changing|modern|digital) (world|landscape|era)\b`,
    String.raw`\bnavigat(e|ing) the (complexit|landscape|world)`, String.raw`\bin the realm of\b`,
    String.raw`\bwhen it comes to\b`, String.raw`\bnot just [^,.;]{1,45}? but\b`,
    String.raw`\bit'?s not (just )?about [^,.;]{1,45}?,? (it'?s|but)\b`,
    String.raw`\bunlock(ing)? (the|your) (potential|power)\b`, String.raw`\belevate your\b`, String.raw`\bseamless(ly)?\b`,
  ];
  const HEDGING_PHRASES = [
    String.raw`\bsomewhat\b`, String.raw`\brelatively\b`, String.raw`\bappears to\b`, String.raw`\bseems to indicate\b`,
    String.raw`\bseems to suggest\b`, String.raw`\bmay potentially\b`, String.raw`\bcould potentially\b`,
    String.raw`\bmight potentially\b`, String.raw`\bit appears that\b`,
  ];
  const GENERIC_PRAISE = [
    String.raw`\bwell[- ]structured\b`, String.raw`\bcomprehensive\b`, String.raw`\bcommendable\b`,
    String.raw`\bnoteworthy\b`, String.raw`\bexemplary\b`, String.raw`\bimpressive\b`, String.raw`\brobust\b`,
    String.raw`\belegant solution\b`,
  ];
  // Contractions people use and AI prose avoids.
  const CONTRACTION_PAIRS = [
    ["did not", "didn't"], ["cannot", "can't"], ["will not", "won't"], ["do not", "don't"], ["does not", "doesn't"],
    ["is not", "isn't"], ["are not", "aren't"], ["was not", "wasn't"], ["were not", "weren't"],
    ["would not", "wouldn't"], ["could not", "couldn't"], ["should not", "shouldn't"], ["I am", "I'm"],
    ["I have", "I've"], ["I would", "I'd"], ["it is", "it's"], ["that is", "that's"], ["we are", "we're"],
    ["you are", "you're"],
  ];
  // A dash splitting a sentence: an en or em dash, or a spaced hyphen, within one line (never a bullet list).
  const MID_SENTENCE_DASH = /\w(?:[ \t]+[-–—][ \t]+|[–—])\w/g;
  const CONTRACTION_TOKEN = /\b\w+'(s|t|re|ve|ll|d|m)\b/i;
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const count = (re, t) => (t.match(re) || []).length;
  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const pstdev = (a) => { const m = mean(a); return Math.sqrt(mean(a.map((x) => (x - m) ** 2))); };
  const words = (t) => t.split(/\s+/).filter(Boolean);

  function countContractions(text) {
    let expanded = 0, contracted = 0;
    for (const [e, c] of CONTRACTION_PAIRS) {
      expanded += count(rx(String.raw`\b` + e + String.raw`\b`), text);
      contracted += count(rx(esc(c)), text);
    }
    return [expanded, contracted];
  }
  const countDashes = (text) => count(MID_SENTENCE_DASH, text);
  const splitSentences = (text) => text.trim().split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);
  const splitAnswers = (text) => text.split(/^\s*(?:-{3,}|#{3,})\s*$/m).map((p) => p.trim()).filter(Boolean);

  // A tidy three-part ending: the last sentence is a chain of parallel verbs, or "then ..., then ...".
  function hasClosingParallelChain(text) {
    const s = splitSentences(text);
    if (!s.length) return false;
    const last = s[s.length - 1].toLowerCase();
    if (count(/,\s+then\b/g, last) >= 2) return true;
    return /(\b\w+(s|ed|ing)\b[^,]*,\s+){2,}.*\b(and|or)\s+\w+/.test(last);
  }
  // "X, the Y," glosses packed mid-sentence.
  const countStackedAppositives = (text) => count(/,\s+(?:the|a|an)\s+[\w][\w\s/.\-]{2,40}?,/g, text);

  // Contractions sprinkled at even intervals: what scrubbing AI prose "for voice" leaves behind.
  function hasEvenContractionSpread(text) {
    const w = words(text);
    if (w.length < 25) return false;
    const pos = [];
    w.forEach((x, i) => { if (CONTRACTION_TOKEN.test(x)) pos.push(i); });
    if (pos.length < 3) return false;
    const gaps = pos.slice(1).map((p, i) => p - pos[i]);
    const m = mean(gaps);
    if (m < 12 || m > 40 || gaps.length < 2) return false;
    return (m ? pstdev(gaps) / m : 1) < 0.45;
  }
  // 3+ drafts (split by a line of --- or ###) the same shape: one generation pass.
  function answersAreUniform(answers) {
    if (answers.length < 3) return false;
    const counts = [], means = [];
    for (const a of answers) {
      const s = splitSentences(a);
      if (!s.length) return false;
      counts.push(s.length);
      means.push(mean(s.map((x) => words(x).length)));
    }
    return Math.max(...counts) - Math.min(...counts) <= 1 && Math.max(...means) - Math.min(...means) <= 6;
  }

  function structuralMatches(text) {
    const found = [], answers = splitAnswers(text), multi = answers.length >= 2;
    const targets = multi ? answers : [text];
    let chain = 0, appos = 0, even = 0;
    for (const a of targets) {
      if (hasClosingParallelChain(a)) chain++;
      if (countStackedAppositives(a) >= 2) appos++;
      if (hasEvenContractionSpread(a)) even++;
    }
    if (chain) found.push(["structural", `closing parallel-verb chain (x${chain})`]);
    if (appos) found.push(["structural", `stacked appositive glosses (x${appos})`]);
    if (even) found.push(["structural", "even contraction spread (sprinkled, not clumped)"]);
    const d = countDashes(text);
    if (d >= 3) found.push(["structural", `em-dash overuse (${d} mid-sentence dashes)`]);
    if (multi && answersAreUniform(answers)) found.push(["structural", `cross-draft uniformity (${answers.length} drafts, same shape)`]);
    return found;
  }

  // --- House rules ---------------------------------------------------------------------------------------
  const WORD_LIMIT = 350;
  const JARGON_TERMS = ["PR", "repo", "repository", "merge", "merged", "CI", "relay", "signalling", "dev branch",
    "staging", "orchestrator", "Swarm", "secret", "composer", "stack", "env", "cron", "handler", "config", "deploy",
    "commit", "branch", "endpoint", "volume", "container", "schema", "webform", "recipe", "purge", "honeypot", "SPF",
    "DKIM", "IMAP", "API", "DNS", "CSV"];
  const GLOSS = /\b(that is|which is|which means|meaning|in other words|i\.e\.|the thing that|basically|put simply|a kind of|what that means)\b/i;

  // The body only: quoted reply lines and a signature (at most two short closing lines) don't count.
  function stripQuotedAndSignature(text) {
    const parts = text.split("\n").filter((l) => !l.trimStart().startsWith(">")).join("\n").trimEnd().split("\n");
    let removed = 0;
    while (parts.length && removed < 2) {
      const last = parts[parts.length - 1].trim();
      if (!last) { parts.pop(); continue; }
      if (words(last).length <= 2 && !/[.!?:]$/.test(last)) { parts.pop(); removed++; continue; }
      break;
    }
    return parts.join("\n");
  }
  const bodyWords = (text) => words(stripQuotedAndSignature(text)).length;
  function unglossedJargon(text) {
    const out = [], seen = new Set();
    for (const s of splitSentences(stripQuotedAndSignature(text))) {
      if (GLOSS.test(s)) continue;
      for (const t of JARGON_TERMS) {
        if (new RegExp(String.raw`\b` + esc(t) + String.raw`\b`).test(s) && !seen.has(t.toLowerCase())) {
          seen.add(t.toLowerCase());
          out.push(t);
        }
      }
    }
    return out;
  }
  // Writing as the owner, the body never names him: "Jon has the password" above Jon's own signature.
  const SELF_NAMES = /\b(?:Jon|Jonathan|Turtle\s?Wolfe|TortoiseWolfe)\b(?!\s+(?!Pohlner\b|Wolfe\b)[A-Z][a-z])/;
  function thirdPersonSelf(text) {
    const lines = text.split("\n");
    let last = -1;
    lines.forEach((l, i) => { if (l.trim()) last = i; });
    const hits = [];
    let fenced = false;
    lines.forEach((line, i) => {
      if (line.trimStart().startsWith("```")) { fenced = !fenced; return; }
      if (fenced || i === last || line.trimStart().startsWith(">") || line.startsWith("    ") || line.startsWith("\t")) return;
      if (SELF_NAMES.test(line)) hits.push(line.trim().slice(0, 70));
    });
    return hits;
  }

  function check(raw, opts) {
    const o = Object.assign({ strict: true, asOwner: true, plain: false, reply: false }, opts || {});
    const text = norm(raw || "");
    const matches = [];
    for (const [cat, list] of [["formal_phrase", FORMAL_PHRASES], ["email_tell", EMAIL_TELLS], ["hedging", HEDGING_PHRASES], ["generic_praise", GENERIC_PRAISE]]) {
      for (const p of list) for (const m of text.matchAll(rx(p))) matches.push([cat, m[0]]);
    }
    const [expanded, contracted] = countContractions(text);
    if (expanded >= 3 && contracted === 0) matches.push(["no_contractions", `${expanded} expanded forms, 0 contractions`]);
    else if (expanded >= 5 && contracted <= 1) matches.push(["few_contractions", `${expanded} expanded forms, only ${contracted} contractions`]);
    const structural = structuralMatches(text);
    matches.push(...structural);
    const n = matches.length, ns = structural.length;
    let verdict = n <= 2 ? "PASS" : n <= 4 ? "FLAG" : "MAJOR FLAG";
    if (ns >= 1 && verdict === "PASS") verdict = "FLAG";
    if (ns >= 3) verdict = "MAJOR FLAG";
    if (o.strict && n >= 1) verdict = "FAIL";
    const house = [];
    if (o.asOwner) {
      const s = thirdPersonSelf(text);
      if (s.length) house.push(["third_person", `author named in the body: "${s[0]}"`]);
    }
    if (o.plain) {
      const w = bodyWords(text);
      if (w > WORD_LIMIT) house.push(["length", `${w} words, limit ${WORD_LIMIT}`]);
      const j = unglossedJargon(text);
      if (j.length) house.push(["jargon", j.slice(0, 8).map((x) => `"${x}"`).join(", ")]);
      if (o.reply && !text.split("\n").some((l) => l.trimStart().startsWith(">"))) house.push(["no_quoting", "a reply with no '>' quoted points to answer under"]);
    }
    if (house.length) verdict = "FAIL";
    return { signal_count: n, structural_count: ns, matches, house, verdict, body_words: bodyWords(text),
      dash_count: countDashes(text), contraction_ratio: `${expanded} expanded / ${contracted} contracted` };
  }

  const api = { check };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.VoiceCheck = api;
})(typeof window !== "undefined" ? window : globalThis);
