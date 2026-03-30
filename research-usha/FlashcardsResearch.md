# Flashcards Feature Justification: Research Writeup

<!-- Suggested Structure:

What the feature is

What learning problem it solves

Research evidence

Why our implementation helps -->


---
 
## What the Feature Is
 
When a student pastes their study notes into Socrato, the platform automatically generates a set of flashcards from that content. Each card shows a question on one side and the answer on the other. Students can flip cards and rate their recall using the levels Again, Hard, Good, or Easy, which the same four-button system used by Anki. Those ratings are meant to feed a spaced repetition scheduling algorithm (SM-2) that determines when each card should be shown again, prioritizing cards the student struggles with and spacing out cards they know well.
 
---
 
## The Learning Problem It Solves
 
The widespread availability of AI tools has made it easier than ever for students to get answers without doing the cognitive work of retrieving them. A student can paste their notes into an LLM tool, ask for a summary, and feel like they've studied without having actually engaged with the material in any meaningful way. This is a well-documented pattern: when learning feels easy, students tend to believe they have learned more than they actually have. Roediger and Karpicke (2006) demonstrated this directly: students who restudied material rated themselves as more confident than those who tested themselves, yet performed significantly worse on delayed recall tests. The subjective feeling of fluency from rereading or passive review is not the same as actual retention.
 
The deeper issue is that AI-assisted studying tends to short-circuit the process that actually builds memory: effortful retrieval. If a student only reads an AI-generated summary of their notes, they are doing the same cognitive work as rereading, which Dunlosky et al. (2013) rated as "low utility" in their comprehensive review of ten study techniques. The problem is not AI itself; it is that AI use tends to keep students in passive consumption mode rather than active retrieval mode.
 
---
 
## Research Evidence
 
**Active recall significantly outperforms passive review for retention.** 
Roediger and Karpicke (2006) found that students who practiced retrieval forgot only about 13% of material after two days, compared to 56% for students who restudied. This held even when the restudying group felt more confident going into the test. The act of attempting to retrieve information, even if imperfectly, strengthens memory more than re-exposure to the same material.
 
**Spaced repetition compounds the benefit.** 
Cepeda et al. (2006) conducted a meta-analysis across 317 experiments and found that distributing practice over time consistently produced better long-term retention than massing it into a single session. The optimal review window is the point where recall is effortful but still possible, where roughly when the probability of recall has dropped to around 85–90%. This is exactly the logic behind spaced repetition algorithms like SM-2.
 
**These are the only two "high utility" study strategies.** 
Dunlosky et al. (2013) reviewed ten common study techniques and rated only practice testing and distributed practice as high utility. Highlighting, summarizing, and rereading, which all are things students naturally gravitate toward, (and all things that AI makes easier) were rated low utility. The implication is that the path of least resistance when using generic AI platforms is also the least effective path for learning.
 
---
 
## Why Our Implementation Helps
 
Socrato's flashcard feature directly addresses the passive AI use problem by making retrieval the default interaction. Instead of reading a summary, the student is asked a question and must attempt to produce an answer before seeing it. The Again / Hard / Good / Easy rating system is not just a UI pattern, it is the input to the scheduling algorithm that makes spaced repetition work. Without it, flashcards are just passive review with extra steps. Now with it, the platform adapts to what each student actually knows and does not know, surfaces difficult cards more frequently, and spaces out easier ones. It is this distribution of effort that the research shows is most effective for retention.
 
The auto-generation from student notes also addresses a practical barrier that limits how many students actually use spaced repetition tools: making cards takes time. If students have to manually create flashcards, most will not do it consistently enough for the algorithm to matter. By generating them from the notes the student already has, Socrato removes that friction and ensures the cards are aligned with the actual course content, a factor that the Frappa et al. (2026) systematic review identified as one of the main reasons some Anki interventions succeed and others do not.
 
---
 
## Why This Feature Belongs in the Project
 
The core concern motivating this project is that AI tools can make learning feel productive without actually being productive. Students can generate summaries, get answers to questions, and feel like they understand material, all without doing the retrieval work that actually encodes it in long-term memory. Flashcards with spaced repetition are one of the most evidence-backed tools for closing that gap. By building them into Socrato and generating them automatically from student notes, this feature turns a passive AI interaction (paste notes, only get output) into an active learning loop (paste notes, get quizze, get tested on flashcards, come back tomorrow). That is a direct and specific response to the learning problem this project is trying to solve.
 
---
 
## Sources
 
- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention. *Psychological Science*, 17(3), 249–255. https://doi.org/10.1111/j.1467-9280.2006.01693.x
 
- Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. *Psychological Bulletin*, 132(3), 354–380. https://doi.org/10.1037/0033-2909.132.3.354
 
- Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving students' learning with effective learning techniques. *Psychological Science in the Public Interest*, 14(1), 4–58. https://doi.org/10.1177/1529100612453266
 
- Frappa, M., et al. (2026). Anki use and academic performance in medical education: A systematic review of evidence and learning theory. *Medical Science Educator*. https://doi.org/10.1007/s40670-025-02313-6
