# Active Recall and Spaced Repetition: Research for Socrato Flashcards Feature

## Why Active Recall Works

The core mechanism behind flashcard-based learning is the testing effect: retrieving information from memory strengthens that memory significantly more than passively re-reading it. Roediger and Karpicke's landmark 2006 study in Psychological Science found that students who practiced retrieval forgot only about 13% of material over two days, compared to 56% for those who restudied. A follow-up by Karpicke and Blunt (2011, Science) further showed that retrieval practice outperformed even elaborative concept mapping on delayed tests, which is a technique widely considered to be an "active" study strategy.

Spaced repetition adds a scheduling layer on top of this. Instead of reviewing material in a single session, spacing reviews at increasing intervals directly combats the Ebbinghaus forgetting curve. Cepeda et al. (2006) reviewed 254 studies and found that distributing practice over time consistently produced better retention than massing it. The optimal spacing depends on the retention goal since longer retention benefits from longer gaps between reviews.

Dunlosky et al.'s comprehensive 2013 review rated ten common study techniques across hundreds of studies. Only two received a "high utility" rating: practice testing (active recall) and distributed practice (spaced repetition). Highlighting, rereading, and summarization were all rated low utility. A subsequent meta-analysis by Donoghue and Hattie (2021), covering 242 studies and over 169,000 participants, confirmed these rankings.

The evidence here is consistent throughout other education research. Active recall and spaced repetition have large, well-replicated effects on retention across subject areas and student populations.

---

## Evidence from Anki in Academic Settings

A January 2026 systematic review by Frappa et al. in Medical Science Educator synthesized 11 studies on Anki use among medical students, which gives us a clearer picture of what happens when these techniques are applied in a real academic context.

For standardized exams like the USMLE Step 1, results were consistently positive. High-frequency Anki users outperformed minimal users by 4-13 points, with a dose-response relationship: roughly one additional point per 1,700 cards reviewed. For university course exams, results were more mixed. Some studies found significant gains (one reported +6–7% across consecutive course exams with a structured Anki training program), while others found no measurable difference despite students reporting positive experiences.

The discrepancy between standardized and course exam results likely comes down to two factors: deck quality and preparation timelines. Standardized licensing exams allow months of cumulative spaced review, which is exactly the condition where the spacing effect is strongest. Course exams have compressed timelines that limit how much the algorithm can help. Community-curated decks like AnKing were also more consistently effective than faculty-developed ones, pointing to deck quality as a real variable.

Students who adopted Anki earlier in their curriculum and used it regularly tended to perform better on benchmark exams. Episodic cramming with flashcards did not show the same benefit.

---

## How to Ensure Better Learning Outcomes

Based on both the cognitive science literature and the implementation patterns from the Frappa et al. review, a few factors consistently separate effective use from ineffective use.

**Align cards with course content and assessment format.** Deck quality and curricular alignment appear to be the primary reason some Anki interventions worked and others did not. Cards need to map directly to what students are actually being tested on — pre-made decks optimized for standardized exams worked well for those exams, but not necessarily for coursework.

**Start early and stay consistent.** The spacing effect requires time to work. Multiple studies found that early adoption and sustained daily use predicted better outcomes. Last-minute cramming with flashcards does not capture the benefit of the algorithm.

**Do not rely on flashcards alone.** Flashcards are strongest for factual and conceptual recall. For higher-order reasoning — applying, analyzing, synthesizing — they need to be supplemented with problem-solving practice, case-based learning, or question banks. Overreliance on flashcards risks producing surface-level familiarity without deeper understanding.

**Embrace the difficulty.** The "desirable difficulties" principle means retrieval should feel effortful: that struggle is the learning signal. Students consistently report that rereading feels more productive than self-testing, but the evidence shows the opposite. Difficulty during retrieval is not a sign that the strategy is not working.

**Provide structure and training.** Gilbert et al. found that students who went through a formal Anki training program significantly outperformed non-users. Simply making flashcards available is not enough — students benefit from guidance on how to use the tool effectively.

---

## Implications for Socrato

These findings map directly onto where Socrato can create real value.

The main problem with existing spaced repetition tools is the deck quality problem. Most students either use pre-made decks that are not aligned with their specific course, or spend significant time making their own cards before they can even start studying. Socrato addresses this by generating cards directly from the student's own notes, which means alignment with course content is automatic.

The Again / Hard / Good / Easy rating system in the flashcard UI is the mechanism that enables the spacing effect to actually work — without it, flashcards are just passive review. Pairing flashcards with the quiz feature also addresses the research finding that flashcards alone are not sufficient for higher-order reasoning, since the quiz tests application rather than just recall.

The biggest gap the research flags is consistency of use. The spacing algorithm only produces results when students return to it regularly over time. Features that encourage habit formation — streaks, review reminders, progress tracking — are likely where the most meaningful outcome improvements come from, beyond the core generation feature itself.

---

## Algorithm Implementation

### SM-2
 
SM-2 is the algorithm developed by Piotr Wozniak in 1987 and is the foundation of Anki. It is the simplest production-ready option and can be implemented in a few dozen lines of code.
 
Each card tracks three values: the **interval** (days until next review), the **repetition count**, and an **ease factor** (a floating point number starting at 2.5, minimum 1.3) that reflects how difficult the card has been historically. After each review, the user rates recall quality on a 0–5 scale, and the algorithm updates accordingly:
 
- If quality ≥ 3 (correct response): interval is multiplied by the ease factor on subsequent reviews; rep count increments.
- If quality < 3 (incorrect): interval resets to 1 day; rep count resets to 0.
- The ease factor is adjusted after every review: `EF' = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))`.
 
The Again / Hard / Good / Easy buttons in Socrato's current flashcard UI map cleanly to this. They also just need to translate to a quality score (e.g., Again = 1, Hard = 2, Good = 4, Easy = 5) and persist the resulting interval, rep count, and ease factor per card per user in the database. (This is my TODO for the week as well)

### What to Log for the Algorithm
 
For SM-2, each review event needs:
- `card_id`
- `user_id`
- `reviewed_at` (timestamp)
- `quality` (0–5 or mapped from Again/Hard/Good/Easy)
- `interval_before` and `interval_after`
- `ease_factor_before` and `ease_factor_after`

---

## References

- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning. *Psychological Science*, 17(3), 249–255.
- Karpicke, J. D., & Blunt, J. R. (2011). Retrieval practice produces more learning than elaborative studying with concept mapping. *Science*, 331(6018), 772–775.
- Cepeda, N. J., et al. (2006). Distributed practice in verbal recall tasks. *Psychological Bulletin*, 132(3), 354–380.
- Dunlosky, J., et al. (2013). Improving students' learning with effective learning techniques. *Psychological Science in the Public Interest*, 14(1), 4–58.
- Donoghue, G. M., & Hattie, J. A. C. (2021). A meta-analysis of ten learning techniques. *Frontiers in Education*, 6.
- Frappa, et al. (2026). Anki use and academic performance in medical education: A systematic review. *Medical Science Educator*.